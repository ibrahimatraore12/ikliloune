# =============================================================
# wsgi.py — Point d'entrée WSGI pour Gunicorn / production
# Usage : gunicorn wsgi:app
# =============================================================

from main import creer_app

app = creer_app()

if __name__ == "__main__":
    app.run()
