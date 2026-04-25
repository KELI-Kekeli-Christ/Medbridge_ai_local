from django.contrib import admin
from django.urls import path, include
from apps.inference.views import ModelsInfoView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth & utilisateurs
    path('api/auth/', include('apps.authentication.urls')),

    # Sessions anonymes (UUID + TTL 24h)
    path('api/sessions/', include('apps.sessions.urls')),

    # Inférence IA
    path('api/inference/', include('apps.inference.urls')),

    # Ordonnances
    path('api/prescriptions/', include('apps.prescriptions.urls')),

    # Catalogue des modèles
    path('api/models/', ModelsInfoView.as_view(), name='models-info'),
]
