from rest_framework import serializers
from .models import Prescription


class PrescriptionCreateSerializer(serializers.Serializer):
    session_id = serializers.UUIDField(required=False)
    doctor_text = serializers.CharField(min_length=5, max_length=10000)
    patient_language = serializers.CharField(max_length=10, default='fr')
    generate_patient_version = serializers.BooleanField(default=True)


class PrescriptionSerializer(serializers.ModelSerializer):
    prescription_id = serializers.UUIDField(read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = (
            'prescription_id', 'doctor_text', 'patient_text',
            'source_language', 'patient_language',
            'created_at', 'expires_at', 'is_expired'
        )

    def get_is_expired(self, obj):
        return obj.is_expired()
