from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    SpeechToTextSerializer,
    LanguageDetectSerializer,
    TranslationSerializer,
    FullPipelineSerializer,
)
from .services import (
    run_speech_to_text,
    run_language_detection,
    run_translation,
    run_full_pipeline,
)
from .model_config import get_stt_models_for_language, get_translation_models


class SpeechToTextView(APIView):
    """
    POST /api/inference/speech-to-text/
    Transcrit un fichier audio en texte via le modèle Whisper fine-tuné.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SpeechToTextSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            result = run_speech_to_text(
                audio_file=data['audio_file'],
                language_hint=data.get('language_hint', 'fr'),
                speaker_type=data.get('speaker_type', 'doctor'),
                model_id=data.get('model_id', 'whisper_ewe'),
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LanguageDetectView(APIView):
    """
    POST /api/inference/detect-language/
    Détecte automatiquement la langue du texte.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LanguageDetectSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = run_language_detection(serializer.validated_data['text'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TranslationView(APIView):
    """
    POST /api/inference/translate/
    Traduit/adapte le texte entre registre médical et registre patient.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TranslationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            result = run_translation(
                text=data['text'],
                mode=data['mode'],
                source_language=data['source_language'],
                target_language=data['target_language'],
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FullPipelineView(APIView):
    """
    POST /api/inference/full-pipeline/
    Pipeline complet: audio → transcription → traduction → texte médical + patient.
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = FullPipelineSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            result = run_full_pipeline(
                audio_file=data['audio_file'],
                speaker_type=data['speaker_type'],
                output_mode=data['output_mode'],
                language_hint=data.get('language_hint') or None,
                model_id=data.get('model_id', 'whisper_ewe'),
                target_language=data.get('target_language', 'fr'),
            )
            # Ajout du session_id dans la réponse si fourni
            if 'session_id' in data:
                result['session_id'] = str(data['session_id'])
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelsInfoView(APIView):
    """
    GET /api/models/
    Liste les modèles disponibles avec leurs métadonnées.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.conf import settings
        import os

        # Noms lisibles pour l'affichage
        model_display_names = {
            'whisper': 'Whisper Ewe (ASR)',
            'omni': 'OmniASR Ewe (ASR)',
            'translation': 'Traduction locale seq2seq',
            'language_detection': 'Détection de langue',
            'nllb_ewe_fr': 'NLLB Ewe → Français',
            'nllb_ar_fr': 'NLLB Arabe → Français',
        }

        models_info = []
        for key, config in settings.AI_MODELS.items():
            path_exists = os.path.exists(config['path'])
            models_info.append({
                'model_id': key,
                'name': model_display_names.get(key, key),
                'type': config['type'],
                'path_configured': config['path'],
                'loaded': path_exists,
                'status': 'available' if path_exists else 'model_file_missing',
            })

        return Response(models_info, status=status.HTTP_200_OK)

class AvailableSttModelsView(APIView):
    """
    GET /api/models/stt/?language=ee
    Liste les modèles STT disponibles pour une langue donnée.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        language = request.query_params.get('language', 'fr')
        models = get_stt_models_for_language(language)
        
        # Ajouter les informations d'existence des modèles
        import os
        from django.conf import settings
        
        for model in models:
            if 'path' in model:
                path = os.path.join(settings.BASE_DIR, model['path'])
                model['available'] = os.path.exists(path)
            else:
                model['available'] = True
        
        return Response({
            'language': language,
            'models': models,
        }, status=status.HTTP_200_OK)


class AvailableTranslationModelsView(APIView):
    """
    GET /api/models/translation/?source=ee&target=fr
    Liste les modèles de traduction disponibles pour une paire de langues.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        source_lang = request.query_params.get('source', 'fr')
        target_lang = request.query_params.get('target', 'fr')
        models = get_translation_models(source_lang, target_lang)
        
        return Response({
            'source_language': source_lang,
            'target_language': target_lang,
            'models': models,
        }, status=status.HTTP_200_OK)