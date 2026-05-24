# =============================================================
# models/produit.py — Table des articles du catalogue
# =============================================================

import json
from datetime import datetime
from backend.database import db


class Produit(db.Model):
    """Un article vendu sur le site IKLILOUNE."""

    __tablename__ = "produits"

    # --- Colonnes ----------------------------------------------
    id          = db.Column(db.Integer, primary_key=True)
    nom         = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)

    # "parfum", "sac", "chaussure", "vetement"
    categorie   = db.Column(db.String(50), nullable=False)

    # "femme" (Perles), "homme" (Corail), "mixte"
    genre       = db.Column(db.String(20), nullable=False, default="mixte")

    # Prix en FCFA
    prix        = db.Column(db.Integer, nullable=False)
    prix_promo  = db.Column(db.Integer, nullable=True)

    # Quantité disponible
    stock       = db.Column(db.Integer, nullable=False, default=0)

    # "new", "promo", ou vide
    badge       = db.Column(db.String(20), nullable=True, default="")

    # Couleurs : '[{"hex":"#C9922A","nom":"Or"}]'
    couleurs_json   = db.Column(db.Text, nullable=True, default="[]")

    # Tailles : '["S","M","L"]' ou '["38","39","40"]'
    tailles_json    = db.Column(db.Text, nullable=True, default="[]")

    # Attributs spécifiques selon catégorie (JSON)
    # Parfum  : {"ml":"100","olfactif":"Floral","tenue":"8h"}
    # Sac     : {"matiere":"Cuir","dimensions":"35x25"}
    # Chaussure: {"talon":"7","matiere":"Cuir"}
    # Vêtement : {"tissu":"Wax","type":"Robe"}
    attributs_json  = db.Column(db.Text, nullable=True, default="{}")

    # Nom du fichier photo WebP (ex: "produit_5.webp")
    photo       = db.Column(db.String(200), nullable=True, default="")

    # False = retiré du catalogue (on ne supprime jamais vraiment)
    actif       = db.Column(db.Boolean, nullable=False, default=True)

    # Horodatage automatique
    cree_le     = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le  = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # --- Méthodes ----------------------------------------------

    def en_promo(self):
        """True si un prix promotionnel est défini."""
        return self.prix_promo is not None and self.prix_promo > 0

    def en_stock(self):
        """True si au moins une unité disponible."""
        return self.stock > 0

    def stock_faible(self):
        """True si stock <= 3 — affiche l'alerte sur le site."""
        return 0 < self.stock <= 3

    def prix_actuel(self):
        """Prix à afficher : promo si disponible, sinon normal."""
        return self.prix_promo if self.en_promo() else self.prix

    def vers_dict(self):
        """Convertit le produit en dict pour l'API JSON."""
        return {
            "id"            : self.id,
            "nom"           : self.nom,
            "description"   : self.description or "",
            "categorie"     : self.categorie,
            "genre"         : self.genre,
            "prix"          : self.prix,
            "prix_promo"    : self.prix_promo,
            "prix_actuel"   : self.prix_actuel(),
            "en_promo"      : self.en_promo(),
            "stock"         : self.stock,
            "en_stock"      : self.en_stock(),
            "stock_faible"  : self.stock_faible(),
            "badge"         : self.badge or "",
            "couleurs"      : json.loads(self.couleurs_json or "[]"),
            "tailles"       : json.loads(self.tailles_json or "[]"),
            "attributs"     : json.loads(self.attributs_json or "{}"),
            "photo"         : self.photo or "",
            "actif"         : self.actif,
            "cree_le"       : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<Produit #{self.id} | {self.nom} | {self.prix} FCFA>"
