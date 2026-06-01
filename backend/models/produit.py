# =============================================================
# models/produit.py — Table des articles du catalogue
# =============================================================

import json
import random
import string
from datetime import datetime
from backend.database import db
from backend import config


def _generer_reference():
    """
    Génère une référence produit unique au format IKL-YYYY-XXXXX.
    Exemple : IKL-2026-00142

    Retourne :
        str : référence unique générée
    """
    annee   = datetime.utcnow().year
    suffixe = ''.join(random.choices(string.digits, k=5))
    return f"IKL-{annee}-{suffixe}"


class Produit(db.Model):
    """Un article vendu sur le site IKLILOUNE."""

    __tablename__ = "produits"

    # --- Identifiants ------------------------------------------
    id          = db.Column(db.Integer, primary_key=True)
    reference   = db.Column(db.String(20), unique=True, nullable=False,
                            default=_generer_reference)

    # --- Informations principales ------------------------------
    nom         = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(1000), nullable=True)

    # "parfum", "sac", "chaussure", "vetement", "accessoire"
    categorie   = db.Column(db.String(50), nullable=False)

    # "femme" (Perles 🫧), "homme" (Corail 🪸), "mixte"
    genre       = db.Column(db.String(20), nullable=False, default="mixte")

    # --- Prix en FCFA ------------------------------------------
    prix        = db.Column(db.Integer, nullable=False)
    prix_promo  = db.Column(db.Integer, nullable=True)

    # --- Stock -------------------------------------------------
    stock       = db.Column(db.Integer, nullable=False, default=0)
    # Seuils configurables depuis l'admin (hérite de config si non définis)
    seuil_bas   = db.Column(db.Integer, nullable=False, default=3)
    seuil_haut  = db.Column(db.Integer, nullable=False, default=10)

    # --- Badge -------------------------------------------------
    # "nouveau", "best_seller", "promo", "bientot_epuise", ou vide
    badge       = db.Column(db.String(30), nullable=True, default="")

    # --- Données JSON ------------------------------------------
    # Couleurs : '[{"hex":"#C9922A","nom":"Or"}]'
    couleurs_json   = db.Column(db.Text, nullable=True, default="[]")
    # Tailles : '["S","M","L"]' ou '["38","39","40"]'
    tailles_json    = db.Column(db.Text, nullable=True, default="[]")
    # Attributs spécifiques par catégorie (JSON libre)
    attributs_json  = db.Column(db.Text, nullable=True, default="{}")

    # --- Photo principale (WebP auto-converti) -----------------
    photo       = db.Column(db.String(200), nullable=True, default="")

    # --- Mise en avant -----------------------------------------
    en_vedette  = db.Column(db.Boolean, nullable=False, default=False)

    # --- Compteurs (pour statistiques) ------------------------
    nb_consultations = db.Column(db.Integer, nullable=False, default=0)
    nb_commandes     = db.Column(db.Integer, nullable=False, default=0)

    # --- Soft delete (jamais de DELETE physique) --------------
    actif       = db.Column(db.Boolean, nullable=False, default=True)

    # --- Horodatage automatique --------------------------------
    cree_le     = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le  = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # --- Méthodes ----------------------------------------------

    def en_promo(self):
        """True si un prix promotionnel est défini et inférieur au prix."""
        return self.prix_promo is not None and 0 < self.prix_promo < self.prix

    def en_stock(self):
        """True si au moins une unité disponible."""
        return self.stock > 0

    def prix_actuel(self):
        """Prix à afficher : promo si disponible, sinon normal."""
        return self.prix_promo if self.en_promo() else self.prix

    def indicateur_stock(self):
        """
        Retourne l'indicateur couleur du stock pour l'affichage client.
        Le client ne voit JAMAIS le chiffre brut — uniquement la couleur.

        Retourne :
            str : 'vert' | 'orange' | 'rouge' | 'rupture'
        """
        if self.stock <= 0:
            return 'rupture'
        if self.stock <= self.seuil_bas:
            return 'rouge'
        if self.stock <= self.seuil_haut:
            return 'orange'
        return 'vert'

    def couleurs(self):
        """Retourne la liste des couleurs parsée depuis JSON."""
        try:
            return json.loads(self.couleurs_json or "[]")
        except Exception:
            return []

    def tailles(self):
        """Retourne la liste des tailles parsée depuis JSON."""
        try:
            return json.loads(self.tailles_json or "[]")
        except Exception:
            return []

    def attributs(self):
        """Retourne les attributs parsés depuis JSON."""
        try:
            return json.loads(self.attributs_json or "{}")
        except Exception:
            return {}

    def vers_dict(self):
        """
        Convertit le produit en dictionnaire pour l'API JSON.
        Note : le stock brut N'EST PAS exposé — uniquement l'indicateur couleur.
        """
        return {
            "id"              : self.id,
            "reference"       : self.reference,
            "nom"             : self.nom,
            "description"     : self.description or "",
            "categorie"       : self.categorie,
            "genre"           : self.genre,
            "prix"            : self.prix,
            "prix_promo"      : self.prix_promo,
            "prix_actuel"     : self.prix_actuel(),
            "en_promo"        : self.en_promo(),
            # Stock : indicateur couleur uniquement (pas le chiffre)
            "stock_indicateur": self.indicateur_stock(),
            "en_stock"        : self.en_stock(),
            "badge"           : self.badge or "",
            "couleurs"        : self.couleurs(),
            "tailles"         : self.tailles(),
            "attributs"       : self.attributs(),
            "photo"           : self.photo or "",
            "en_vedette"      : self.en_vedette,
            "nb_consultations": self.nb_consultations,
            "actif"           : self.actif,
            "cree_le"         : self.cree_le.strftime("%d/%m/%Y"),
        }

    def vers_dict_admin(self):
        """
        Version admin du dictionnaire — inclut le stock réel.
        Utilisée UNIQUEMENT dans les routes admin protégées.
        """
        d = self.vers_dict()
        d["stock"]      = self.stock
        d["seuil_bas"]  = self.seuil_bas
        d["seuil_haut"] = self.seuil_haut
        d["nb_commandes"] = self.nb_commandes
        return d

    def __repr__(self):
        return f"<Produit {self.reference} | {self.nom} | {self.prix} FCFA>"
