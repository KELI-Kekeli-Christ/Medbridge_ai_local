"""
Configuration centralisée des modèles d'inférence.
Permet de gérer plusieurs modèles par tâche et langue.
"""

from enum import Enum
from typing import Dict, List

class ModelType(str, Enum):
    """Types de modèles supportés"""
    WHISPER = 'whisper'
    OMNI = 'omni'
    NLLB = 'nllb'
    TRANSLATION = 'translation'
    LANG_DETECT = 'lang_detect'


class LanguageCode(str, Enum):
    """Codes de langue supportés"""
    FR = 'fr'
    EN = 'en'
    EWE = 'ee'
    ARABIC = 'ar'
    ARABIC_EGYPTIAN = 'arz'


# Mapping langdetect → codes internes
LANGDETECT_TO_INTERNAL = {
    'fr': LanguageCode.FR,
    'en': LanguageCode.EN,
    'ar': LanguageCode.ARABIC,
}

# Mapping codes internes → NLLB codes
INTERNAL_TO_NLLB = {
    LanguageCode.FR: 'fra_Latn',
    LanguageCode.EN: 'eng_Latn',
    LanguageCode.EWE: 'ewe_Latn',
    LanguageCode.ARABIC: 'arb_Arab',
    LanguageCode.ARABIC_EGYPTIAN: 'arz_Arab',
}


# Configuration des modèles de speech-to-text disponibles
STT_MODELS = {
    LanguageCode.EWE: [
        {
            'id': 'whisper_ewe',
            'name': 'Whisper (Ewe)',
            'type': ModelType.WHISPER,
            'path': 'models/whisper_medium_ewe_hf',
            'description': 'Whisper medium fine-tuned pour Ewe',
            'priority': 1,
        },
        {
            'id': 'omni_ewe',
            'name': 'Omni (Ewe)',
            'type': ModelType.OMNI,
            'path': 'models/omni_ewe',
            'description': 'OmniASR fine-tuned pour Ewe',
            'priority': 2,
        },
    ],
    LanguageCode.FR: [
        {
            'id': 'whisper_fr',
            'name': 'Whisper (FR)',
            'type': ModelType.WHISPER,
            'path': 'models/whisper',
            'description': 'Whisper pour le français',
            'priority': 1,
        },
    ],
    LanguageCode.ARABIC: [
        {
            'id': 'omni_ar',
            'name': 'Omni (Arabe)',
            'type': ModelType.OMNI,
            'path': 'models/omni_ewe',  # Utilise le modèle Omni disponible (ewe pour test)
            'description': 'OmniASR pour l\'arabe',
            'priority': 1,
        },
    ],
}


# Configuration des modèles de traduction disponibles
TRANSLATION_MODELS = {
    'fr_fr': [
        {
            'id': 'nllb_fr_fr',
            'name': 'NLLB (FR → FR)',
            'type': ModelType.NLLB,
            'description': 'Traduction médicale FR → FR avec NLLB',
            'priority': 1,
        },
        {
            'id': 'local_fr_fr',
            'name': 'Local Model (FR → FR)',
            'type': ModelType.TRANSLATION,
            'path': 'models/translation',
            'description': 'Modèle de traduction local fine-tuné',
            'priority': 2,
        },
    ],
    'ee_fr': [
        {
            'id': 'nllb_ee_fr',
            'name': 'NLLB (Ewe → FR)',
            'type': ModelType.NLLB,
            'path': 'models/NLLB_ewe_francais/final_model',
            'description': 'Traduction Ewe → Français avec NLLB local',
            'priority': 1,
        },
    ],
    'fr_ee': [
        {
            'id': 'nllb_fr_ee',
            'name': 'NLLB (FR → Ewe)',
            'type': ModelType.NLLB,
            'path': 'models/NLLB_ewe_francais/final_model',
            'description': 'Traduction Français → Ewe avec NLLB local',
            'priority': 1,
        },
    ],
    'ar_fr': [
        {
            'id': 'nllb_ar_fr',
            'name': 'NLLB (Arabe → FR)',
            'type': ModelType.NLLB,
            'path': 'models/NLLB_arab_francais/final_model',
            'description': 'Traduction Arabe → Français avec NLLB local',
            'priority': 1,
        },
    ],
    'ee_ee': [
        {
            'id': 'nllb_ee_ee',
            'name': 'NLLB (Ewe → Ewe)',
            'type': ModelType.NLLB,
            'description': 'Traduction Ewe → Ewe (réduction) avec NLLB',
            'priority': 1,
        },
    ],
    'ar_ar': [
        {
            'id': 'nllb_ar_ar',
            'name': 'NLLB (Arabe → Arabe)',
            'type': ModelType.NLLB,
            'description': 'Traduction Arabe → Arabe avec NLLB',
            'priority': 1,
        },
    ],
}


# Configuration pour la détection de langue
LANG_DETECT_CONFIG = {
    'preferred': ModelType.LANG_DETECT,  # Essayer d'abord le modèle custom
    'fallback': 'langdetect_with_whitelist',  # Fallback: langdetect + whitelist Ewe
    'ewe_indicators': [
        'zɔ', 'miawoe', 'medzoé', 'mesre', 'woe', 'nye', 'kpɔ',
        'mí', 'dé', 'gbeé', 'ɖ', 'ŋu', 'nu', 'eye',
    ],
}


def get_stt_models_for_language(language: str) -> List[Dict]:
    """
    Retourne les modèles STT disponibles pour une langue donnée.
    Trié par priorité (priority=1 est le modèle recommandé).
    """
    lang_code = language.lower()
    
    # Mapping des codes de langue vers LanguageCode
    lang_map = {
        'fr': LanguageCode.FR,
        'en': LanguageCode.EN,
        'ee': LanguageCode.EWE,
        'ewe': LanguageCode.EWE,
        'ar': LanguageCode.ARABIC,
        'arabic': LanguageCode.ARABIC,
        'arz': LanguageCode.ARABIC_EGYPTIAN,
    }
    
    code = lang_map.get(lang_code)
    if not code:
        return []
    
    models = STT_MODELS.get(code, [])
    return sorted(models, key=lambda m: m.get('priority', 999))


def get_translation_models(source_lang: str, target_lang: str) -> List[Dict]:
    """
    Retourne les modèles de traduction disponibles pour une paire de langues.
    """
    pair_key = f"{source_lang}_{target_lang}"
    models = TRANSLATION_MODELS.get(pair_key, [])
    return sorted(models, key=lambda m: m.get('priority', 999))


def normalize_language_code(lang: str) -> str:
    """Normalise les codes de langue vers le format interne"""
    mapping = {
        'ewe': LanguageCode.EWE,
        'ee': LanguageCode.EWE,
        'french': LanguageCode.FR,
        'fr': LanguageCode.FR,
        'english': LanguageCode.EN,
        'en': LanguageCode.EN,
        'arabic': LanguageCode.ARABIC,
        'ar': LanguageCode.ARABIC,
        'arz': LanguageCode.ARABIC_EGYPTIAN,
    }
    return str(mapping.get(lang.lower(), lang.lower()))


def get_nllb_language_code(internal_code: str) -> str:
    """Convertit un code de langue interne en code NLLB"""
    # Normaliser d'abord
    internal_code = normalize_language_code(internal_code)
    return INTERNAL_TO_NLLB.get(internal_code, internal_code)
