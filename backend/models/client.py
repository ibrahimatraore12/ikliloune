# =============================================================
# models/client.py — Registre des clients / prospects
# Alimenté par le formulaire pop-up -5% et les commandes
# =============================================================

from datetime import datetime
from backend.database import db


class Client(db.Model):
    """
    Un client ou prospect enregistré.
    Source : pop-up capture email, ou commande passée.
    Utilisé pour les campagnes marketing.
    """

    __tablename__ = "clients"

    id          = db.Column(db.Integer, primary_key=True)
    prenom      = db.Column(db.String(100), nullable=False)
    nom         = db.Column(db.String(100), nullable=True)
    email       = db.Column(db.String(150), unique=True, nullable=False)
    telephone   = db.Column(db.String(30), nullable=True)

    # Intérêt déclaré : "parfum", "sac", "vetement", "chaussure", "tout"
    interet     = db.Column(db.String(50), nullable=True)

    # "popup" = inscrit via le formulaire -5%
    # "commande" = a passé une commande
    source      = db.Column(db.String(30), nullable=True, default="popup")

    # Le code promo reçu (ex: "IKLI5")
    code_promo  = db.Column(db.String(20), nullable=True)

    # Nombre de commandes passées
    nb_commandes = db.Column(db.Integer, nullable=False, default=0)

    # Date de naissance (facultative — pour les offres anniversaire)
    date_naissance = db.Column(db.String(10), nullable=True)
    # Adresse (facultative)
    adresse        = db.Column(db.String(300), nullable=True)

    # Consentement marketing (RGPD)
    consentement = db.Column(db.Boolean, nullable=False, default=True)

    # Actif dans les campagnes ? False = désabonné
    actif       = db.Column(db.Boolean, nullable=False, default=True)

    # Horodatage
    cree_le     = db.Column(db.DateTime, default=datetime.utcnow)

    def vers_dict(self):
        """Convertit le client en dict pour l'export CSV."""
        return {
            "id"          : self.id,
            "prenom"      : self.prenom,
            "nom"         : self.nom or "",
            "email"       : self.email,
            "telephone"   : self.telephone or "",
            "interet"     : self.interet or "",
            "source"         : self.source or "",
            "date_naissance"  : self.date_naissance or "",
            "adresse"         : self.adresse or "",
            "nb_commandes"    : self.nb_commandes,
            "actif"       : self.actif,
            "cree_le"     : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<Client #{self.id} | {self.prenom} {self.nom} | {self.email}>"
