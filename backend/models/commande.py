# =============================================================
# models/commande.py — Table des commandes clients
# =============================================================

import json
from datetime import datetime
from backend.database import db


class Commande(db.Model):
    """Une commande passée sur le site."""

    __tablename__ = "commandes"

    id              = db.Column(db.Integer, primary_key=True)

    # Numéro lisible affiché au client (ex: "CMD-2025-004821")
    numero          = db.Column(db.String(30), unique=True, nullable=False)

    # Informations client
    client_nom      = db.Column(db.String(150), nullable=False)
    client_telephone = db.Column(db.String(30), nullable=False)
    client_email    = db.Column(db.String(150), nullable=True)
    client_adresse  = db.Column(db.String(300), nullable=True)

    # Panier : liste JSON des articles commandés
    # [{"id":1,"nom":"Rose d'Or","prix":28500,"qty":2,"photo":"..."}]
    articles_json   = db.Column(db.Text, nullable=False, default="[]")

    # Montants en FCFA
    total           = db.Column(db.Integer, nullable=False, default=0)
    remise          = db.Column(db.Integer, nullable=True, default=0)

    # Mode de paiement choisi : "orange", "momo", "wave", "whatsapp"
    paiement        = db.Column(db.String(30), nullable=True)

    # Statut de la commande
    # "en_attente" → "confirmee" → "en_preparation" → "livree"
    statut          = db.Column(db.String(30), nullable=False,
                                default="en_attente")

    # Notes internes (visibles uniquement par l'admin)
    notes_admin     = db.Column(db.Text, nullable=True)

    # Horodatage
    cree_le         = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    def articles(self):
        """Retourne la liste des articles du panier."""
        return json.loads(self.articles_json or "[]")

    def vers_dict(self):
        """Convertit la commande en dict pour l'API JSON."""
        return {
            "id"               : self.id,
            "numero"           : self.numero,
            "client_nom"       : self.client_nom,
            "client_telephone" : self.client_telephone,
            "client_email"     : self.client_email or "",
            "client_adresse"   : self.client_adresse or "",
            "articles"         : self.articles(),
            "total"            : self.total,
            "remise"           : self.remise or 0,
            "paiement"         : self.paiement or "",
            "statut"           : self.statut,
            "notes_admin"      : self.notes_admin or "",
            "cree_le"          : self.cree_le.strftime("%d/%m/%Y %H:%M"),
        }

    def __repr__(self):
        return f"<Commande {self.numero} | {self.client_nom} | {self.total} FCFA>"
