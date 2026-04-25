from rest_framework import serializers
from .models import InferenceSession


class InferenceSessionSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = InferenceSession
        fields = (
            'session_id', 'user_type', 'source_language',
            'target_language', 'created_at', 'expires_at', 'is_expired'
        )
        read_only_fields = ('session_id', 'created_at', 'expires_at')

    def get_is_expired(self, obj):
        return obj.is_expired()
