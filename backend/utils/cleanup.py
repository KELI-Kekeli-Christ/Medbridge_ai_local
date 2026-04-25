"""
Nettoyage automatique des sessions et ordonnances expirées.
À appeler via un cron job ou une management command.

Cron suggéré (toutes les heures) :
    0 * * * * cd /path/to/backend && python manage.py cleanup_expired
"""

import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def delete_expired_sessions():
    from apps.sessions.models import InferenceSession
    deleted, _ = InferenceSession.objects.filter(expires_at__lt=timezone.now()).delete()
    logger.info(f"Sessions expirées supprimées: {deleted}")
    return deleted


def delete_expired_prescriptions():
    from apps.prescriptions.models import Prescription
    deleted, _ = Prescription.objects.filter(expires_at__lt=timezone.now()).delete()
    logger.info(f"Ordonnances expirées supprimées: {deleted}")
    return deleted
