<p align="center">
  <a href="README.md"><b>English</b></a>
  &nbsp;·&nbsp;
  <a href="README.fr.md">Français</a>
  &nbsp;·&nbsp;
  <a href="README.es.md">Español</a>
</p>

# 🩺 MedBridge AI

Une plateforme IA de **consultation médicale assistée** pour transformer l’audio clinique en contenu exploitable :
- transcription (STT),
- détection de langue,
- traduction/adaptation médicale,
- génération de prescription (avec export PDF),
- orchestration via une API Django + une interface Next.js.

---

## ✨ Fonctionnalités clés

- 🎙️ **Speech-to-Text** multi-modèles (Whisper / Omni)
- 🌍 **Détection automatique de langue** (avec heuristiques Ewe)
- 🔁 **Traduction médicale** (NLLB local + fallback)
- 🧠 **Pipeline complet** audio → texte → adaptation
- 📄 **Gestion des prescriptions** + génération PDF
- 🔐 **Authentification JWT** (login, refresh, profil)
- 🧾 **Sessions anonymes** (TTL 24h)
- ⚡ **GPU auto** : utilisation de CUDA si disponible, sinon CPU

---

## 🧱 Architecture

### Backend
- **Django + DRF**
- Apps : `authentication`, `sessions`, `inference`, `prescriptions`
- Modèles IA locaux dans `backend/models/`

### Frontend
- **Next.js 15 + React 19 + TypeScript + Tailwind**
- App Router (`frontend/app`)
- Proxy API via rewrite vers le backend

---

## 🗂️ Structure du projet

```text
Medbrigde_AI_local/
├── backend/
│   ├── apps/
│   │   ├── authentication/
│   │   ├── inference/
│   │   ├── prescriptions/
│   │   └── sessions/
│   ├── medbridge/
│   ├── models/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   ├── services/
│   └── package.json
└── README.md
```

---

## 🚀 Démarrage rapide

## 1) Backend (Django)

Prérequis : Python 3.12+

```bash
cd backend
python -m venv ../env
source ../env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend disponible sur : **http://localhost:8000**

> Pour PyTorch CUDA, installe la variante adaptée à ton GPU/driver.

## 2) Frontend (Next.js)

Prérequis : Node 20+

```bash
cd frontend
npm install
npm run dev
```

Frontend disponible sur : **http://localhost:3000**

---

## 🔧 Variables d’environnement utiles

### Backend (`backend/.env`)

```env
SECRET_KEY=change-me
DEBUG=True
HF_LOCAL_FILES_ONLY=False
NLLB_MODEL_ID=facebook/nllb-200-distilled-600M
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 📡 API (aperçu)

### Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `POST /api/auth/token/refresh/`
- `GET /api/auth/me/`

### Inference
- `POST /api/inference/speech-to-text/`
- `POST /api/inference/detect-language/`
- `POST /api/inference/translate/`
- `POST /api/inference/full-pipeline/`
- `GET /api/inference/models/stt/?language=ee`
- `GET /api/inference/models/translation/?source=ee&target=fr`
- `GET /api/models/` (catalogue global)

### Sessions & Prescriptions
- `POST /api/sessions/`
- `GET /api/sessions/<uuid>/`
- `POST /api/prescriptions/`
- `GET /api/prescriptions/<uuid>/`
- `GET /api/prescriptions/<uuid>/pdf/`

---

## 🤖 Modèles IA pris en charge

- **Whisper** (fine-tuné Ewe / FR)
- **OmniASR** (fairseq2)
- **NLLB** (Ewe→FR, Arabe→FR + fallback générique)
- **Détection de langue** (modèle custom ou fallback `langdetect`)

Les chemins modèles sont configurés dans `backend/medbridge/settings.py` via `AI_MODELS`.

---

## 🧪 Conseils dev

- Vérifier l’état des modèles : `GET /api/models/`
- En cas de manque modèle local, le backend applique des fallbacks (selon service)
- Les logs d’inférence sont activés côté backend (niveau `INFO`)

---

## 📌 Roadmap possible

- Monitoring des performances GPU/CPU
- Batch inference pour fichiers audio longs
- Dashboard qualité (WER/BLEU/latence)
- Déploiement Docker complet (frontend + backend + modèles)

---

## 👥 Projet

Projet MedBridge AI — assistance clinique multilingue orientée production locale.
