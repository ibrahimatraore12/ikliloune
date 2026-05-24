# =============================================================
# services/image_service.py — Compression automatique en WebP
# Reçoit une photo brute, retourne un fichier WebP léger.
# =============================================================

import os
from PIL import Image
from backend import config


def traiter_image(fichier_source, nom_cible):
    """
    Redimensionne et convertit une image en WebP.

    Paramètres :
        fichier_source (str) : chemin vers la photo brute
        nom_cible      (str) : nom sans extension (ex: "produit_5")

    Retourne :
        str  : nom du fichier WebP créé (ex: "produit_5.webp")
        None : si erreur
    """
    try:
        image = Image.open(fichier_source)

        # Convertir en RGB si nécessaire (PNG transparent, etc.)
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")

        # Redimensionner sans déformer (conserve les proportions)
        image.thumbnail(
            (config.LARGEUR_MAX_IMAGE, config.HAUTEUR_MAX_IMAGE),
            Image.LANCZOS
        )

        # Construire le chemin de destination
        nom_webp = f"{nom_cible}.webp"
        os.makedirs(config.DOSSIER_IMAGES, exist_ok=True)
        chemin_dest = os.path.join(config.DOSSIER_IMAGES, nom_webp)

        # Sauvegarder en WebP compressé
        image.save(chemin_dest, format="WEBP",
                   quality=config.QUALITE_WEBP, method=6)

        taille_ko = os.path.getsize(chemin_dest) // 1024
        print(f"✅ Image traitée : {nom_webp} ({taille_ko} Ko)")
        return nom_webp

    except Exception as e:
        print(f"❌ Erreur image : {e}")
        return None


def supprimer_image(nom_fichier):
    """Supprime une photo produit du serveur."""
    if not nom_fichier:
        return False
    chemin = os.path.join(config.DOSSIER_IMAGES, nom_fichier)
    if os.path.exists(chemin):
        os.remove(chemin)
        print(f"🗑️  Image supprimée : {nom_fichier}")
        return True
    return False
