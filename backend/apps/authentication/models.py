from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        DOCTOR = 'doctor', 'Médecin'
        PATIENT = 'patient', 'Patient'

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)
    institution = models.CharField(max_length=255, blank=True)  # ex: Université d'Avignon
    preferred_language = models.CharField(max_length=10, default='fr')

    def is_doctor(self):
        return self.role == self.Role.DOCTOR
