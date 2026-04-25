import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_expiry():
    return timezone.now() + timedelta(seconds=settings.SESSION_TTL_SECONDS)


class InferenceSession(models.Model):
    """
    Session anonyme ou liée à un utilisateur.
    Chaque session a un UUID unique et expire automatiquement après 24h.
    """
    class SpeakerType(models.TextChoices):
        DOCTOR = 'doctor', 'Médecin'
        PATIENT = 'patient', 'Patient'

    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='sessions'
    )
    user_type = models.CharField(max_length=10, choices=SpeakerType.choices, default=SpeakerType.DOCTOR)
    source_language = models.CharField(max_length=10, default='fr')
    target_language = models.CharField(max_length=20, default='fr-patient')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Session {self.session_id} ({self.user_type})"
