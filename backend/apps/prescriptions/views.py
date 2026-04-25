import io

from django.http import FileResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inference.services import run_translation
from apps.sessions.models import InferenceSession
from .models import Prescription
from .serializers import PrescriptionCreateSerializer, PrescriptionSerializer
from .utils import generate_prescription_pdf


class PrescriptionCreateView(APIView):
    """
    POST /api/prescriptions/
    Crée une ordonnance et génère automatiquement la version patient.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PrescriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        doctor_text = data['doctor_text']
        patient_language = data['patient_language']
        patient_text = ''

        # Génération automatique de la version patient
        if data['generate_patient_version']:
            try:
                result = run_translation(
                    text=doctor_text,
                    mode='medical_to_patient',
                    source_language='fr',
                    target_language=patient_language,
                )
                patient_text = result['translated_text']
            except Exception as e:
                return Response(
                    {'detail': f'Erreur traduction: {e}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Résolution de la session si fournie
        session = None
        if 'session_id' in data:
            try:
                session = InferenceSession.objects.get(session_id=data['session_id'])
            except InferenceSession.DoesNotExist:
                pass

        doctor = request.user if request.user.is_authenticated else None

        prescription = Prescription.objects.create(
            session=session,
            doctor=doctor,
            doctor_text=doctor_text,
            patient_text=patient_text,
            patient_language=patient_language,
        )

        return Response(PrescriptionSerializer(prescription).data, status=status.HTTP_201_CREATED)


class PrescriptionDetailView(APIView):
    """
    GET /api/prescriptions/{prescription_id}/
    """
    permission_classes = [permissions.AllowAny]

    def _get_prescription(self, prescription_id):
        try:
            return Prescription.objects.get(prescription_id=prescription_id)
        except Prescription.DoesNotExist:
            return None

    def get(self, request, prescription_id):
        prescription = self._get_prescription(prescription_id)
        if not prescription:
            return Response({'detail': 'Ordonnance introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        if prescription.is_expired():
            prescription.delete()
            return Response({'detail': 'Ordonnance expirée.'}, status=status.HTTP_410_GONE)
        return Response(PrescriptionSerializer(prescription).data)


class PrescriptionPDFView(APIView):
    """
    GET /api/prescriptions/{prescription_id}/pdf/
    Génère et télécharge l'ordonnance en PDF (version médecin + version patient).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, prescription_id):
        try:
            prescription = Prescription.objects.get(prescription_id=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'detail': 'Ordonnance introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        if prescription.is_expired():
            prescription.delete()
            return Response({'detail': 'Ordonnance expirée.'}, status=status.HTTP_410_GONE)

        pdf_buffer = generate_prescription_pdf(prescription)
        pdf_buffer.seek(0)

        return FileResponse(
            pdf_buffer,
            as_attachment=True,
            filename=f'ordonnance_{prescription.prescription_id}.pdf',
            content_type='application/pdf',
        )
