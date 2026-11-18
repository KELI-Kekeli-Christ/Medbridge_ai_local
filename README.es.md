<p align="center">
  <a href="README.md">English</a>
  &nbsp;·&nbsp;
  <a href="README.fr.md">Français</a>
  &nbsp;·&nbsp;
  <a href="README.es.md"><b>Español</b></a>
</p>

Asistente local de consulta médica: transcripción, detección de idioma, traducción médica y recetas en PDF. API Django e interfaz Next.js. Los pasos completos están en su `README.md`.

```bash
cd backend
python -m venv ../env && source ../env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

La API escucha en `http://localhost:8000`. Arranca la aplicación Next.js desde `frontend` con el script del `package.json` de esa carpeta.


La documentación en inglés que ya estaba en este repositorio sigue en el archivo en inglés.
