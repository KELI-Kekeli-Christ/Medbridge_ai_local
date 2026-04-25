from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import InferenceSession
from .serializers import InferenceSessionSerializer


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = InferenceSessionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = InferenceSession.objects.filter(expires_at__gt=timezone.now())
        if self.request.user.is_authenticated:
            return qs.filter(user=self.request.user)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


class SessionDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def _get_session(self, session_id):
        try:
            return InferenceSession.objects.get(session_id=session_id)
        except InferenceSession.DoesNotExist:
            return None

    def get(self, request, session_id):
        session = self._get_session(session_id)
        if not session:
            return Response({'detail': 'Session introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        if session.is_expired():
            session.delete()
            return Response({'detail': 'Session expirée.'}, status=status.HTTP_410_GONE)
        return Response(InferenceSessionSerializer(session).data)

    def delete(self, request, session_id):
        session = self._get_session(session_id)
        if not session:
            return Response({'detail': 'Session introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
