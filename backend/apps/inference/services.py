"""
Logique métier des inférences. Appellée par les views.
Chaque fonction retourne un dict prêt à être sérialisé.
"""

import io
import logging
import os
import tempfile
import time

logger = logging.getLogger(__name__)

NLLB_LANGUAGE_MAP = {
    'fr': 'fra_Latn',
    'en': 'eng_Latn',
    'ee': 'ewe_Latn',
    'ar': 'arb_Arab',
    'arz': 'arz_Arab',
}


def _get_model_device(model):
    """Retourne le device PyTorch du modèle, ou CPU si indéterminé."""
    try:
        import torch
        return next(model.parameters()).device
    except Exception:
        try:
            return model.device
        except Exception:
            import torch
            return torch.device('cpu')


def _move_to_device(batch, device):
    """Déplace un dict de tenseurs (ou un tenseur) sur le device donné."""
    if hasattr(batch, 'to'):
        return batch.to(device)
    if isinstance(batch, dict):
        return {
            k: (v.to(device) if hasattr(v, 'to') else v)
            for k, v in batch.items()
        }
    return batch


def _run_nllb_translation(text: str, source_language: str, target_language: str) -> str:
    from .model_loader import get_nllb_model

    import torch

    pair_key = f"{source_language}_{target_language}"
    logger.info(f"[Translation] Démarrage avec modèle: nllb ({pair_key}), texte: {text[:50]}...")

    model, tokenizer = get_nllb_model(pair_key)
    model_device = _get_model_device(model)
    src_lang = NLLB_LANGUAGE_MAP.get(source_language, source_language)
    tgt_lang = NLLB_LANGUAGE_MAP.get(target_language, target_language)

    # Pour NllbTokenizer, utiliser les bonnes méthodes
    try:
        # Définir la langue source
        tokenizer.src_lang = src_lang
        
        # Encoder le texte
        encoded = tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        encoded = _move_to_device(encoded, model_device)
        
        # Définir la langue cible et obtenir son ID pour forced_bos_token_id
        tokenizer.tgt_lang = tgt_lang
        forced_bos_token_id = tokenizer.convert_tokens_to_ids(tokenizer.tgt_lang)

        with torch.no_grad():
            output_ids = model.generate(
                **encoded,
                forced_bos_token_id=forced_bos_token_id,
                max_new_tokens=512,
                num_beams=4,
                early_stopping=True,
            )

        return tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()
    except AttributeError:
        # Si ce n'est pas un NllbTokenizer, essayer l'approche générique
        tokenizer.src_lang = src_lang
        encoded = tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        encoded = _move_to_device(encoded, model_device)
        
        # Chercher le token BOS pour la langue cible
        if hasattr(tokenizer, 'lang_code_to_id'):
            forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang]
        else:
            forced_bos_token_id = None

        with torch.no_grad():
            kwargs = {
                'max_new_tokens': 512,
                'num_beams': 4,
                'early_stopping': True,
            }
            if forced_bos_token_id is not None:
                kwargs['forced_bos_token_id'] = forced_bos_token_id
                
            output_ids = model.generate(**encoded, **kwargs)

        return tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0].strip()


# ─── Speech-to-Text ─────────────────────────────────────────────────────────────

def run_speech_to_text(audio_file, language_hint: str = None, speaker_type: str = 'doctor', model_id: str = 'whisper_ewe') -> dict:
    from .model_loader import get_stt_model

    start = time.time()
    logger.info(f"[STT] Démarrage avec modèle: {model_id}, langue: {language_hint}, locuteur: {speaker_type}")
    
    model, processor = get_stt_model(model_id)
    model_device = _get_model_device(model)

    # Sauvegarde temporaire du fichier audio
    suffix = os.path.splitext(audio_file.name)[-1] or '.wav'
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        import torch
        import torchaudio

        # Détecter le type de modèle
        # OmniASR : processor est un SentencePieceProcessor (a GetPieceSize())
        is_omni = hasattr(processor, 'GetPieceSize')
        # HuggingFace Whisper : processor a get_decoder_prompt_ids()
        is_huggingface = (not is_omni) and processor is not None
        # OpenAI Whisper : a .transcribe() dans le module whisper
        is_openai_whisper = (not is_omni) and (not is_huggingface) and \
            hasattr(model, 'transcribe') and 'whisper' in model.__class__.__module__.lower()

        # Charger l'audio à 16kHz dans tous les cas
        waveform, sample_rate = torchaudio.load(tmp_path)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        # Mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        if is_omni:
            # ── OmniASR (wav2vec2_asr + CTC, fairseq2 0.6) ───────────────────
            from fairseq2.nn.batch_layout import BatchLayout
            sp = processor  # SentencePieceProcessor
            audio_1d = waveform.squeeze(0)  # [T]
            T = audio_1d.shape[0]
            seqs = audio_1d.unsqueeze(0).to(model_device)  # [1, T]
            seqs_layout = BatchLayout(shape=(1, T), seq_lens=[T])

            with torch.no_grad():
                output = model(seqs, seqs_layout)

            # Returns (logits, seqs_layout): logits shape [1, T', vocab]
            logits_batch = output[0] if isinstance(output, (tuple, list)) else output
            logits = logits_batch[0]  # [T', vocab]

            token_ids = logits.argmax(-1).tolist()

            # CTC decode: remove blank (<pad>=1), BOS/EOS/UNK, and consecutive duplicates
            blank_id = sp.PieceToId('<pad>')
            skip_ids = {blank_id, sp.unk_id(), sp.bos_id(), sp.eos_id()}
            prev, decoded = None, []
            for t in token_ids:
                if t not in skip_ids and t != prev:
                    decoded.append(t)
                prev = t
            transcript = sp.Decode(decoded).strip()
            detected_lang = language_hint or 'ee'

        elif is_huggingface:
            # ── HuggingFace Whisper fine-tuné ─────────────────────────────────
            input_features = processor(
                waveform.squeeze().numpy(),
                sampling_rate=16000,
                return_tensors='pt'
            ).input_features
            input_features = input_features.to(model_device)

            forced_ids = None
            if language_hint:
                # Whisper ne reconnaît pas 'ee' — slot 'yo' (Yoruba) utilisé pour Ewe
                whisper_lang = 'yo' if language_hint == 'ee' else language_hint
                try:
                    forced_ids = processor.get_decoder_prompt_ids(language=whisper_lang, task='transcribe')
                except Exception:
                    forced_ids = None

            with torch.no_grad():
                predicted_ids = model.generate(input_features, forced_decoder_ids=forced_ids)
            transcript = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
            raw_lang = language_hint or 'fr'
            detected_lang = 'ee' if raw_lang == 'yo' else raw_lang

        elif is_openai_whisper:
            # ── OpenAI Whisper ────────────────────────────────────────────────
            options = {}
            if language_hint:
                options['language'] = 'yo' if language_hint == 'ee' else language_hint
            result = model.transcribe(tmp_path, **options)
            transcript = result['text'].strip()
            raw_lang = result.get('language', language_hint or 'fr')
            detected_lang = 'ee' if raw_lang == 'yo' else raw_lang

        else:
            options = {}
            if language_hint:
                options['language'] = 'yo' if language_hint == 'ee' else language_hint
            result = model.transcribe(tmp_path, **options)
            transcript = result['text'].strip()
            raw_lang = result.get('language', language_hint or 'fr')
            detected_lang = 'ee' if raw_lang == 'yo' else raw_lang

    finally:
        os.unlink(tmp_path)

    return {
        'transcript': transcript,
        'detected_language': detected_lang,
        'speaker_type': speaker_type,
        'latency_ms': round((time.time() - start) * 1000),
    }


# ─── Détection de langue ─────────────────────────────────────────────────────────

# Caractères et mots indicatifs de langue Ewe
EWE_INDICATORS = {
    'chars': ['ɔ', 'ɖ', 'ŋ', 'ƒ', 'ʊ'],  # Caractères spéciaux Ewe
    'words': [
        'zɔ', 'miawoe', 'medzoé', 'mesre', 'woe', 'nye', 'kpɔ',
        'mí', 'dé', 'gbeé', 'meve', 'nu', 'eye', 'vɔ',
    ],
}


def _detect_ewe_confidence(text: str) -> float:
    """
    Calcule un score de confiance pour déterminer si le texte est en Ewe.
    Basé sur la présence de caractères et mots Ewe spécifiques.
    """
    text_lower = text.lower()
    score = 0.0
    
    # Caractères Ewe = fort indicateur
    ewe_char_count = sum(1 for char in text if char in EWE_INDICATORS['chars'])
    if ewe_char_count > 0:
        score += min(ewe_char_count * 0.2, 0.5)
    
    # Mots Ewe = fort indicateur
    ewe_word_count = sum(1 for word in EWE_INDICATORS['words'] if word in text_lower)
    if ewe_word_count > 0:
        score += min(ewe_word_count * 0.25, 0.5)
    
    # Normaliser le score entre 0 et 1
    return min(score, 1.0)


def run_language_detection(text: str) -> dict:
    from .model_loader import get_lang_detect_model

    start = time.time()
    logger.info(f"[Language Detection] Démarrage pour texte: {text[:50]}...")
    
    # Première vérification: est-ce que c'est du Ewe?
    ewe_confidence = _detect_ewe_confidence(text)
    if ewe_confidence > 0.3:
        # Confiance suffisante que c'est du Ewe
        logger.info(f"[Language Detection] Ewe détecté (whitelist, confiance: {ewe_confidence:.2f})")
        return {
            'detected_language': 'ee',
            'confidence': round(ewe_confidence, 4),
            'alternatives': [
                {'language': 'ee', 'confidence': round(ewe_confidence, 4)},
            ],
            'latency_ms': round((time.time() - start) * 1000),
            'method': 'whitelist',
        }
    
    # Sinon, utiliser le modèle standard
    mode, model, tokenizer = get_lang_detect_model()

    if mode == 'langdetect':
        from langdetect import detect, detect_langs
        try:
            detected = detect(text)
            logger.info(f"[Language Detection] Résultat langdetect: {detected} (méthode: langdetect)")
            probs = detect_langs(text)
            alternatives = [{'language': str(p).split(':')[0], 'confidence': round(p.prob, 4)} for p in probs]
            confidence = alternatives[0]['confidence'] if alternatives else 0.0
        except Exception as e:
            logger.warning(f"langdetect failed: {e}, defaulting to 'fr'")
            detected = 'fr'
            confidence = 0.5
            alternatives = [{'language': 'fr', 'confidence': 0.5}]
    else:
        import torch
        inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=128)
        inputs = _move_to_device(inputs, _get_model_device(model))
        with torch.no_grad():
            logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)
        top = probs.topk(3)
        labels = model.config.id2label
        alternatives = [
            {'language': labels[idx.item()], 'confidence': round(val.item(), 4)}
            for val, idx in zip(top.values[0], top.indices[0])
        ]
        detected = alternatives[0]['language']
        confidence = alternatives[0]['confidence']

    return {
        'detected_language': detected,
        'confidence': confidence,
        'alternatives': alternatives,
        'latency_ms': round((time.time() - start) * 1000),
        'method': 'langdetect' if mode == 'langdetect' else 'custom_model',
    }


# ─── Traduction médicale ↔ patient ───────────────────────────────────────────────

def run_translation(text: str, mode: str = 'medical_to_patient',
                    source_language: str = 'fr', target_language: str = 'fr') -> dict:
    from .model_loader import get_translation_model

    start = time.time()
    fallback_used = False

    warning = None
    warning_detail = None

    # Traduction inter-langues ou réduction dans la même langue: priorité au modèle NLLB multilingue.
    # NLLB peut aussi faire des traductions médical ↔ patient dans la même langue.
    if source_language in NLLB_LANGUAGE_MAP and target_language in NLLB_LANGUAGE_MAP:
        try:
            translated = _run_nllb_translation(text, source_language, target_language)
            return {
                'original_text': text,
                'translated_text': translated,
                'mode': mode,
                'source_language': source_language,
                'target_language': target_language,
                'fallback_used': fallback_used,
                'latency_ms': round((time.time() - start) * 1000),
            }
        except Exception as e:
            logger.warning("Échec traduction NLLB (%s -> %s): %s", source_language, target_language, e)
            warning = 'nllb_failed'
            warning_detail = 'Le modèle multilingue NLLB a échoué, fallback activé.'
    elif source_language != target_language:
        # Paire de langues non supportée par NLLB
        warning = 'unsupported_language_pair'
        warning_detail = 'Paire de langues non supportée par la configuration actuelle.'

    # Fallback: essayer le modèle de traduction local si disponible
    try:
        model, tokenizer = get_translation_model()

        # Prefix pour orienter le modèle selon le mode
        prefix_map = {
            'medical_to_patient': 'médical vers patient: ',
            'patient_to_medical': 'patient vers médical: ',
        }
        prefix = prefix_map.get(mode, '')
        input_text = prefix + text

        import torch
        inputs = tokenizer(
            input_text,
            return_tensors='pt',
            max_length=512,
            truncation=True,
            padding=True
        )
        inputs = _move_to_device(inputs, _get_model_device(model))

        with torch.no_grad():
            output_ids = model.generate(
                inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_new_tokens=512,
                num_beams=4,
                early_stopping=True,
            )

        translated = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    except Exception as e:
        # Fallback non bloquant: on renvoie le texte original si le modèle
        # de traduction n'est pas disponible.
        logger.warning("Fallback traduction activé: %s", e)
        translated = text
        fallback_used = True

        if warning is None:
            warning = 'translation_model_unavailable'
            warning_detail = 'Le modèle de traduction local est indisponible, texte original renvoyé.'

    response = {
        'original_text': text,
        'translated_text': translated,
        'mode': mode,
        'source_language': source_language,
        'target_language': target_language,
        'fallback_used': fallback_used,
        'latency_ms': round((time.time() - start) * 1000),
    }

    if warning:
        response['warning'] = warning
        response['warning_detail'] = warning_detail

    return response


# ─── Pipeline complet ────────────────────────────────────────────────────────────

def run_full_pipeline(audio_file, speaker_type: str = 'doctor',
                      output_mode: str = 'prescription', language_hint: str = None,
                      model_id: str = 'whisper_ewe', target_language: str = 'fr') -> dict:
    start = time.time()
    logger.info(
        f"[Full Pipeline] Démarrage: modèle={model_id}, locuteur={speaker_type}, "
        f"langue_hint={language_hint}, target={target_language}"
    )

    # 1. Transcription audio — language_hint est la langue du patient (aide le modèle STT)
    stt_hint = language_hint if language_hint else None
    stt_result = run_speech_to_text(audio_file, language_hint=stt_hint, speaker_type=speaker_type, model_id=model_id)
    transcript = stt_result['transcript']
    detected_lang = stt_result['detected_language']

    # 2. Traduction/adaptation selon le type de locuteur
    if speaker_type == 'doctor':
        # Médecin parle → adapter pour le patient (même langue)
        translation_result = run_translation(transcript, mode='medical_to_patient',
                                             source_language=detected_lang, target_language=detected_lang)
        medical_text = transcript
        patient_text = translation_result['translated_text']
    else:
        # Patient parle → traduire vers la langue du médecin (target_language)
        trans_target = target_language if target_language != detected_lang else detected_lang
        translation_result = run_translation(transcript, mode='patient_to_medical',
                                             source_language=detected_lang, target_language=trans_target)
        patient_text = transcript
        medical_text = translation_result['translated_text']

    return {
        'transcript': transcript,
        'detected_language': detected_lang,
        'speaker_type': speaker_type,
        'medical_text': medical_text,
        'patient_text': patient_text,
        'output_mode': output_mode,
        'total_latency_ms': round((time.time() - start) * 1000),
    }
