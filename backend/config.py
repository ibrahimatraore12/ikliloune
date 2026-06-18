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
DOSSIER_RACINE    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOSSIER_IMAGES    = os.path.join(DOSSIER_RACINE, "static", "images", "produits")
DOSSIER_TEMP      = os.path.join(DOSSIER_RACINE, "uploads_temp")
DOSSIER_TEMPLATES = os.path.join(DOSSIER_RACINE, "templates")
DOSSIER_STATIC    = os.path.join(DOSSIER_RACINE, "static")

# --- Sécurité --------------------------------------------------
SECRET_KEY     = os.environ.get("SECRET_KEY", "dev-key-local-change-en-prod")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")

# --- URL Admin secrète (jamais exposée sur le site) -----------
ADMIN_URL_SECRET   = os.environ.get("ADMIN_URL_SECRET", "ik-gestion-2025-prive")
ADMIN_URL_DASHBOARD = os.environ.get("ADMIN_URL_DASHBOARD", "ik-dashboard-prive")
ADMIN_URL_LOGOUT    = os.environ.get("ADMIN_URL_LOGOUT", "ik-gestion-logout")

# --- Base de données -------------------------------------------
CHEMIN_DB = os.path.join(DOSSIER_RACINE, "ikliloune.db")
URL_DB    = os.environ.get("DATABASE_URL", f"sqlite:///{CHEMIN_DB}")
# Render.com retourne postgres:// → SQLAlchemy veut postgresql://
if URL_DB.startswith("postgres://"):
    URL_DB = URL_DB.replace("postgres://", "postgresql://", 1)

# --- Images ----------------------------------------------------
TAILLE_MAX_UPLOAD  = 10 * 1024 * 1024   # 10 Mo max
FORMATS_ACCEPTES   = {"jpg", "jpeg", "png", "webp", "gif"}
LARGEUR_MAX_IMAGE  = 800
HAUTEUR_MAX_IMAGE  = 800
QUALITE_WEBP       = 82

# --- Stock — seuils pour indicateur couleur client ------------
# Le client voit uniquement vert / orange / rouge (jamais le chiffre)
SEUIL_STOCK_BAS  = int(os.environ.get("SEUIL_STOCK_BAS",  "3"))
SEUIL_STOCK_HAUT = int(os.environ.get("SEUIL_STOCK_HAUT", "10"))

# --- Contact magasin ------------------------------------------
NUMERO_WHATSAPP  = os.environ.get("NUMERO_WHATSAPP", "2250748956959")   # numéro principal
NUMERO_WHATSAPP2 = os.environ.get("NUMERO_WHATSAPP2", "2250585826888")  # numéro secondaire
EMAIL_MAGASIN    = os.environ.get("EMAIL_MAGASIN",    "contact@ikliloune.com")

# --- Réseaux sociaux ------------------------------------------
INSTAGRAM_URL = os.environ.get("INSTAGRAM_URL", "https://www.instagram.com/ikliloune_chic?igsh=ZDh6dmQ3MmdleGp1")
FACEBOOK_URL  = os.environ.get("FACEBOOK_URL",  "https://facebook.com/ikliloune")
TIKTOK_URL    = os.environ.get("TIKTOK_URL",    "https://tiktok.com/@ikliloune")
SNAPCHAT_URL  = os.environ.get("SNAPCHAT_URL",  "https://snapchat.com/add/ikliloune")

# --- Paiement Mobile Money ------------------------------------
ORANGE_MONEY_NUM = os.environ.get("ORANGE_MONEY_NUM", "+225 07 48 95 69 59")
MTN_MOMO_NUM     = os.environ.get("MTN_MOMO_NUM",     "+225 05 85 82 68 88")
WAVE_NUM         = os.environ.get("WAVE_NUM",          "")

# --- Serveur --------------------------------------------------
DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"
PORT  = int(os.environ.get("PORT", 5001))   # 5001 — évite conflit VSCode
