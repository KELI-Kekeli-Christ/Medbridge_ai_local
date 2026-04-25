"""
Chargement unique des modèles fine-tunés depuis le dossier backend/models/.
Les modèles sont chargés en mémoire au démarrage du serveur (lazy loading).

Structure attendue dans backend/models/ :
    models/
    ├── whisper/          ← ton modèle Whisper fine-tuné (dossier HuggingFace ou .pt)
    ├── translation/      ← ton modèle seq2seq de traduction médicale
    └── lang_detect/      ← optionnel, sinon langdetect lib est utilisé
"""

import logging
import os

from django.conf import settings
# torch importé de façon lazy dans chaque fonction

logger = logging.getLogger(__name__)

_loaded_models = {}


def get_torch_device() -> str:
    """Retourne 'cuda' si disponible, sinon 'cpu'."""
    import torch
    return 'cuda' if torch.cuda.is_available() else 'cpu'


def _get_model_path(model_key: str) -> str:
    config = settings.AI_MODELS.get(model_key)
    if not config:
        raise ValueError(f"Modèle inconnu: {model_key}")
    return config['path'], config['type']


def get_whisper_model():
    """Charge le modèle Whisper fine-tuné depuis models/whisper/."""
    if 'whisper' in _loaded_models:
        return _loaded_models['whisper']

    path, _ = _get_model_path('whisper')
    device = get_torch_device()

    try:
        # Essayer d'abord HuggingFace fine-tuned
        if os.path.isdir(path):
            try:
                from transformers import WhisperForConditionalGeneration, WhisperProcessor
                processor = WhisperProcessor.from_pretrained(path)
                model = WhisperForConditionalGeneration.from_pretrained(path)
                model.to(device)
                model.eval()
                _loaded_models['whisper'] = (model, processor)
                logger.info(f"Whisper chargé depuis {path} (HuggingFace, device={device})")
                return _loaded_models['whisper']
            except Exception as hf_error:
                logger.warning(f"Whisper HuggingFace échec ({hf_error}), essai OpenAI Whisper...")
        
        # Fallback: OpenAI Whisper
        import whisper
        model = whisper.load_model('tiny', device=device)
        _loaded_models['whisper'] = (model, None)
        logger.info(f"Whisper chargé depuis OpenAI (modèle 'tiny', device={device})")
        return _loaded_models['whisper']
    except Exception as e:
        logger.error(f"Erreur chargement Whisper: {e}")
        raise


def get_omni_model():
    """
    Charge le modèle OmniASR Ewe (wav2vec2_asr fairseq2) avec CTC.
    Retourne (model, sp_tokenizer) — type 'omni' détecté dans services.py.
    Fallback vers Whisper si chargement impossible.
    """
    if 'omni' in _loaded_models:
        return _loaded_models['omni']

    path, _ = _get_model_path('omni')
    device = get_torch_device()

    try:
        import yaml
        import torch
        import sentencepiece as spm
        from pathlib import Path
        from fairseq2.models.wav2vec2.asr import (
            Wav2Vec2AsrConfig, create_wav2vec2_asr_model
        )
        from fairseq2.models.wav2vec2 import Wav2Vec2EncoderConfig

        model_dir = Path(path)
        checkpoint_path = model_dir / 'model' / 'pp_00' / 'tp_00' / 'sdp_00.pt'
        tok_path = model_dir / 'omniASR_tokenizer.model'

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint non trouvé: {checkpoint_path}")
        if not tok_path.exists():
            raise FileNotFoundError(
                f"Tokenizer non trouvé: {tok_path} — "
                "télécharger depuis https://dl.fbaipublicfiles.com/mms/omniASR_tokenizer.model"
            )

        with open(model_dir / 'model.yaml') as f:
            mc = yaml.safe_load(f)['model_config']
        ec = mc['encoder_config']

        encoder_config = Wav2Vec2EncoderConfig(
            model_dim=ec['model_dim'],
            max_seq_len=ec['max_seq_len'],
            feature_dim=ec['feature_dim'],
            use_fbank=False,
            first_pass_dropout_p=0.0,
            layer_norm_features=ec['layer_norm_features'],
            feature_extractor_layer_descs=[tuple(x) for x in ec['feature_extractor_layer_descs']],
            feature_extractor_bias=ec['feature_extractor_bias'],
            feature_extractor_layer_norm_convs=ec['feature_extractor_layer_norm_convs'],
            feature_grad_scale=ec['feature_grad_scale'],
            num_fbank_channels=0,
            fbank_stride=0,
            sample_fbank_every_k=0,
            pos_encoder_type=ec['pos_encoder_type'],
            pos_encoder_depth=ec['pos_encoder_depth'],
            pos_conv_kernel_size=ec['pos_conv_kernel_size'],
            num_pos_conv_groups=ec['num_pos_conv_groups'],
            use_conformer=False,
            num_encoder_layers=ec['num_encoder_layers'],
            num_encoder_attn_heads=ec['num_encoder_attn_heads'],
            ffn_inner_dim=ec['ffn_inner_dim'],
            dropout_p=0.0,
            attn_dropout_p=0.0,
            ffn_inner_dropout_p=0.0,
            layer_drop_p=0.0,
            norm_order=ec['norm_order'],
            depthwise_conv_kernel_size=0,
        )
        asr_config = Wav2Vec2AsrConfig(
            encoder_config=encoder_config,
            target_vocab_size=mc['target_vocab_size'],
            final_dropout_p=0.0,
            use_masking=False,
        )

        # Charger et nettoyer le checkpoint (supprimer les 2 clés incompatibles avec fairseq2 0.6)
        raw_state = torch.load(checkpoint_path, map_location='cpu', weights_only=False)
        for k in ['encoder.layer_norm.weight', 'encoder.layer_norm.bias']:
            raw_state.pop(k, None)

        model = create_wav2vec2_asr_model(asr_config)
        model.load_state_dict(raw_state, strict=True)
        model.to(device)
        model.eval()

        sp = spm.SentencePieceProcessor()
        sp.Load(str(tok_path))

        _loaded_models['omni'] = (model, sp)
        logger.info(
            f"Modèle OmniASR Ewe chargé depuis {path} "
            f"(fairseq2 0.6, vocab={sp.GetPieceSize()}, device={device})"
        )
        return _loaded_models['omni']
    except Exception as e:
        logger.warning(f"Erreur chargement Omni ({e}) - Fallback à Whisper")
        return get_whisper_model()


def get_stt_model(model_id: str = 'whisper_ewe'):
    """
    Charge le modèle STT approprié selon model_id.
    
    Args:
        model_id: ID du modèle ('whisper_ewe', 'omni_ewe', 'whisper_fr', etc.)
                  Si None ou vide, retourne Whisper par défaut.
    
    Returns:
        (model, processor): Tuple du modèle et du processeur
    """
    # Mapper les IDs de modèle vers les clés de configuration
    model_map = {
        'whisper_ewe': ('whisper', 'whisper'),
        'whisper_fr': ('whisper', 'whisper'),
        'omni_ewe': ('omni', 'omni'),
        'omni_ar': ('omni', 'omni'),
    }
    
    # Utiliser whisper par défaut
    config_key, cache_key = model_map.get(model_id, ('whisper', 'whisper'))
    
    if config_key == 'whisper':
        return get_whisper_model()
    elif config_key == 'omni':
        return get_omni_model()
    else:
        logger.warning(f"Modèle STT inconnu: {model_id}, utilisation de Whisper")
        return get_whisper_model()


def get_translation_model():
    """Charge le modèle de traduction médicale fine-tuné depuis models/translation/."""
    if 'translation' in _loaded_models:
        return _loaded_models['translation']

    path, _ = _get_model_path('translation')
    device = get_torch_device()

    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        tokenizer = AutoTokenizer.from_pretrained(path)
        model = AutoModelForSeq2SeqLM.from_pretrained(path)
        model.to(device)
        model.eval()
        _loaded_models['translation'] = (model, tokenizer)
        logger.info(f"Modèle de traduction chargé depuis {path} (device={device})")
    except Exception as e:
        logger.error(f"Erreur chargement modèle traduction: {e}")
        raise

    return _loaded_models['translation']


def get_nllb_model(pair_key: str = 'generic'):
    """
    Charge le modèle NLLB pour une paire de langues.
    pair_key: 'ee_fr', 'ar_fr', ou 'generic' pour le modèle HuggingFace générique.
    Essaie d'abord le modèle local spécialisé, puis le générique HuggingFace en fallback.
    """
    cache_key = f'nllb_{pair_key}'
    if cache_key in _loaded_models:
        return _loaded_models[cache_key]

    device = get_torch_device()

    # Mapping paire → clé dans AI_MODELS settings
    local_model_map = {
        'ee_fr': 'nllb_ewe_fr',
        'ar_fr': 'nllb_ar_fr',
    }

    settings_key = local_model_map.get(pair_key)
    if settings_key:
        config = settings.AI_MODELS.get(settings_key)
        if config and os.path.isdir(config['path']):
            try:
                from transformers import NllbTokenizer, AutoModelForSeq2SeqLM
                tokenizer = NllbTokenizer.from_pretrained(config['path'])
                model = AutoModelForSeq2SeqLM.from_pretrained(config['path'])
                model.to(device)
                model.eval()
                _loaded_models[cache_key] = (model, tokenizer)
                logger.info(
                    f"Modèle NLLB local chargé pour {pair_key}: {config['path']} "
                    f"(device={device})"
                )
                return _loaded_models[cache_key]
            except Exception as e:
                logger.warning(f"NLLB local ({pair_key}) échec: {e}, tentative générique HuggingFace")

    # Fallback: modèle NLLB générique HuggingFace
    generic_cache = 'nllb_generic'
    if generic_cache in _loaded_models:
        return _loaded_models[generic_cache]

    model_id = os.getenv('NLLB_MODEL_ID', 'facebook/nllb-200-distilled-600M')
    local_files_only = os.getenv('HF_LOCAL_FILES_ONLY', 'False') == 'True'
    try:
        from transformers import NllbTokenizer, AutoModelForSeq2SeqLM
        tokenizer = NllbTokenizer.from_pretrained(model_id, local_files_only=local_files_only)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id, local_files_only=local_files_only)
        model.to(device)
        model.eval()
        _loaded_models[generic_cache] = (model, tokenizer)
        logger.info(f"Modèle NLLB générique chargé: {model_id} (device={device})")
        return _loaded_models[generic_cache]
    except Exception as e:
        logger.error(f"Erreur chargement NLLB générique ({model_id}): {e}")
        raise


def get_nllb_translation_model():
    """Compatibilité — charge le modèle NLLB générique."""
    return get_nllb_model('generic')


def get_lang_detect_model():
    """
    Retourne le détecteur de langue.
    Utilise ton modèle fine-tuné si présent, sinon langdetect lib.
    """
    if 'lang_detect' in _loaded_models:
        return _loaded_models['lang_detect']

    path, _ = _get_model_path('language_detection')
    device = get_torch_device()

    if os.path.isdir(path) and os.listdir(path):
        try:
            from transformers import AutoTokenizer, AutoModelForSequenceClassification
            tokenizer = AutoTokenizer.from_pretrained(path)
            model = AutoModelForSequenceClassification.from_pretrained(path)
            model.to(device)
            model.eval()
            _loaded_models['lang_detect'] = ('custom', model, tokenizer)
            logger.info(f"Modèle détection langue chargé depuis {path} (device={device})")
        except Exception as e:
            logger.warning(f"Modèle custom non chargé ({e}), fallback langdetect.")
            _loaded_models['lang_detect'] = ('langdetect', None, None)
    else:
        _loaded_models['lang_detect'] = ('langdetect', None, None)

    return _loaded_models['lang_detect']
