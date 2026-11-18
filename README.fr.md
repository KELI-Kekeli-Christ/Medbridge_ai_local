<p align="center">
  <a href="README.md">English</a>
  &nbsp;·&nbsp;
  <a href="README.fr.md"><b>Français</b></a>
  &nbsp;·&nbsp;
  <a href="README.es.md">Español</a>
</p>

Assistant local de consultation : transcription, détection de langue, traduction médicale et ordonnances PDF. API Django et interface Next.js. Les étapes complètes sont dans son `README.md`.

```bash
cd backend
python -m venv ../env && source ../env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

L’API écoute sur `http://localhost:8000`. Lancez l’application Next.js depuis `frontend` avec le script du `package.json` de ce dossier.


La documentation anglaise déjà présente dans ce dépôt reste dans le fichier anglais.
