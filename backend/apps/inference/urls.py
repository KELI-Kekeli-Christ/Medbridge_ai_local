from django.urls import path
from .views import (
    SpeechToTextView,
    LanguageDetectView,
    TranslationView,
    FullPipelineView,
    AvailableSttModelsView,
    AvailableTranslationModelsView,
)

urlpatterns = [
    path('speech-to-text/', SpeechToTextView.as_view(), name='inference-stt'),
    path('detect-language/', LanguageDetectView.as_view(), name='inference-lang-detect'),
    path('translate/', TranslationView.as_view(), name='inference-translate'),
    path('full-pipeline/', FullPipelineView.as_view(), name='inference-pipeline'),
    path('models/stt/', AvailableSttModelsView.as_view(), name='available-stt-models'),
    path('models/translation/', AvailableTranslationModelsView.as_view(), name='available-translation-models'),
]
