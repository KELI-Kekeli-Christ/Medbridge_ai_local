from django.urls import path
from .views import SessionListCreateView, SessionDetailView

urlpatterns = [
    path('', SessionListCreateView.as_view(), name='session-list-create'),
    path('<uuid:session_id>/', SessionDetailView.as_view(), name='session-detail'),
]
