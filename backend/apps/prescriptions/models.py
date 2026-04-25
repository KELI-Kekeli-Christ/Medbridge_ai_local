import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_expiry():
    return timezone.now() + timedelta(seconds=settings.SESSION_TTL_SECONDS)


class Prescription(models.Model):
    prescription_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    session = models.ForeignKey(
        'inference_sessions.InferenceSession',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='prescriptions'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='prescriptions'
    )

    # Texte brut dicté par le médecin
    doctor_text = models.TextField()

    # Version traduite en langage patient
    patient_text = models.TextField(blank=True)

    source_language = models.CharField(max_length=10, default='fr')
    patient_language = models.CharField(max_length=10, default='fr')

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Ordonnance {self.prescription_id}"
