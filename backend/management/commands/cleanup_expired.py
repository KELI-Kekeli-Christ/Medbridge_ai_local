from django.core.management.base import BaseCommand
from utils.cleanup import delete_expired_sessions, delete_expired_prescriptions


class Command(BaseCommand):
    help = 'Supprime les sessions et ordonnances expirées (> 24h)'

    def handle(self, *args, **kwargs):
        sessions = delete_expired_sessions()
        prescriptions = delete_expired_prescriptions()
        self.stdout.write(
            self.style.SUCCESS(
                f'Nettoyage terminé: {sessions} sessions, {prescriptions} ordonnances supprimées.'
            )
        )
