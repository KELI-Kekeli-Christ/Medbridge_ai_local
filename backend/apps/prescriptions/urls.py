from django.urls import path
from .views import PrescriptionCreateView, PrescriptionDetailView, PrescriptionPDFView

urlpatterns = [
    path('', PrescriptionCreateView.as_view(), name='prescription-create'),
    path('<uuid:prescription_id>/', PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('<uuid:prescription_id>/pdf/', PrescriptionPDFView.as_view(), name='prescription-pdf'),
]
