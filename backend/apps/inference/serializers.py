from rest_framework import serializers


class SpeechToTextSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    audio_file = serializers.FileField()
    language_hint = serializers.CharField(max_length=10, required=False, default='fr')
    speaker_type = serializers.ChoiceField(choices=['doctor', 'patient'], default='doctor')
    model_id = serializers.CharField(max_length=50, required=False, default='whisper_ewe')


class LanguageDetectSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    text = serializers.CharField(min_length=2, max_length=5000)


class TranslationSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    text = serializers.CharField(min_length=2, max_length=5000)
    mode = serializers.ChoiceField(
        choices=['medical_to_patient', 'patient_to_medical'],
        default='medical_to_patient'
    )
    source_language = serializers.CharField(max_length=10, default='fr')
    target_language = serializers.CharField(max_length=10, default='fr')


class FullPipelineSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    audio_file = serializers.FileField()
    speaker_type = serializers.ChoiceField(choices=['doctor', 'patient'], default='doctor')
    output_mode = serializers.ChoiceField(
        choices=['prescription', 'summary', 'both'],
        default='prescription'
    )
    language_hint = serializers.CharField(max_length=10, required=False, allow_blank=True, default='')
    target_language = serializers.CharField(max_length=10, required=False, default='fr')
    model_id = serializers.CharField(max_length=50, required=False, default='whisper_ewe')
