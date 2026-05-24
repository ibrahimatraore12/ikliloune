# =============================================================
# config.py — Configuration centrale de l'application
# Un seul endroit pour tous les paramètres.
# Pour changer un paramètre → on le change ici uniquement.
# =============================================================

import os
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# --- Chemins ---------------------------------------------------
# Dossier racine du projet (parent de backend/)
DOSSIER_RACINE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

DOSSIER_IMAGES   = os.path.join(DOSSIER_RACINE, "static", "images", "produits")
DOSSIER_TEMP     = os.path.join(DOSSIER_RACINE, "uploads_temp")
DOSSIER_TEMPLATES = os.path.join(DOSSIER_RACINE, "templates")
DOSSIER_STATIC   = os.path.join(DOSSIER_RACINE, "static")

# --- Sécurité --------------------------------------------------
# Lire depuis .env — jamais écrire les vrais secrets ici
SECRET_KEY       = os.environ.get("SECRET_KEY", "dev-key-local")
ADMIN_USERNAME   = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD   = os.environ.get("ADMIN_PASSWORD", "admin")

# --- Base de données -------------------------------------------
# SQLite = un fichier .db local, parfait pour démarrer
CHEMIN_DB  = os.path.join(DOSSIER_RACINE, "ikliloune.db")
URL_DB     = f"sqlite:///{CHEMIN_DB}"

# --- Images ----------------------------------------------------
TAILLE_MAX_UPLOAD        = 10 * 1024 * 1024   # 10 Mo max
FORMATS_ACCEPTES         = {"jpg", "jpeg", "png", "webp"}
LARGEUR_MAX_IMAGE        = 800    # pixels
HAUTEUR_MAX_IMAGE        = 800    # pixels
QUALITE_WEBP             = 82     # 0-100 — bon équilibre qualité/poids

# --- Contact magasin -------------------------------------------
NUMERO_WHATSAPP = os.environ.get("NUMERO_WHATSAPP", "2250104144141")
EMAIL_MAGASIN   = os.environ.get("EMAIL_MAGASIN", "contact@ikliloune.com")

# --- Serveur ---------------------------------------------------
DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"
PORT  = int(os.environ.get("PORT", 5000))
