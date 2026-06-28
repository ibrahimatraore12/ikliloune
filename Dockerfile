# =============================================================
# Dockerfile — Image de production IKLILOUNE
# Base : Python 3.11 slim (légère)
# Serveur : Gunicorn (production-grade)
# =============================================================

# Image de base officielle Python 3.11 légère
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="IKLILOUNE <contact@ikliloune.com>"
LABEL description="IKLILOUNE — La Maison du Chic"

# Variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1   
ENV PYTHONUNBUFFERED=1          
ENV FLASK_DEBUG=False           

# Dossier de travail dans le container
WORKDIR /app

# Copier d'abord requirements.txt seul
# (optimisation Docker : ne réinstalle pas si requirements.txt n'a pas changé)
COPY requirements.txt .

# Installer les dépendances système nécessaires pour Pillow
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code du projet
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p static/images/produits uploads_temp

# Exposer le port
EXPOSE 5000

# Commande de lancement avec Gunicorn
# 2 workers = bon équilibre pour un petit site
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--log-level", "info", "wsgi:app"]
