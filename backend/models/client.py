# =============================================================
# models/client.py — Registre des clients / prospects
# Alimenté par le formulaire pop-up et les commandes
# =============================================================

from datetime import datetime
from backend.database import db


class Client(db.Model):
    """
    Un client ou prospect enregistré.
    L'email est OPTIONNEL — le téléphone est l'identifiant principal.
    Source : pop-up capture email, commande, WhatsApp, saisie manuelle.
    """

    __tablename__ = "clients"

    id          = db.Column(db.Integer, primary_key=True)
    prenom      = db.Column(db.String(100), nullable=False)
    nom         = db.Column(db.String(100), nullable=True)

    # Téléphone = identifiant principal (obligatoire)
    telephone   = db.Column(db.String(30), unique=True, nullable=False)

    # Email optionnel (pour newsletters — avec consentement)
    email       = db.Column(db.String(150), unique=True, nullable=True)

    adresse        = db.Column(db.String(300), nullable=True)
    date_naissance = db.Column(db.String(10),  nullable=True)

    # Intérêt déclaré : "perles", "corail", "les_deux", "tout"
    interet     = db.Column(db.String(50), nullable=True)

    # "popup" | "commande" | "whatsapp" | "manuel"
    source      = db.Column(db.String(30), nullable=True, default="commande")

    # Code promo offert à l'inscription
    code_promo  = db.Column(db.String(20), nullable=True)

    # Statistiques
    nb_commandes  = db.Column(db.Integer, nullable=False, default=0)
    total_achats  = db.Column(db.Integer, nullable=False, default=0)  # FCFA

    # Consentement RGPD — opt-in newsletter
    consentement  = db.Column(db.Boolean, nullable=False, default=False)

    # Soft delete
    actif         = db.Column(db.Boolean, nullable=False, default=True)

    cree_le       = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le    = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    def nom_complet(self):
        """Retourne le nom complet du client."""
        parties = [self.prenom or "", self.nom or ""]
        return " ".join(p for p in parties if p).strip() or "Client"

    def vers_dict(self):
        """Convertit le client en dict pour l'export et l'API."""
        return {
            "id"             : self.id,
            "prenom"         : self.prenom,
            "nom"            : self.nom or "",
            "nom_complet"    : self.nom_complet(),
            "telephone"      : self.telephone,
            "email"          : self.email or "",
            "adresse"        : self.adresse or "",
            "date_naissance" : self.date_naissance or "",
            "interet"        : self.interet or "",
            "source"         : self.source or "",
            "code_promo"     : self.code_promo or "",
            "nb_commandes"   : self.nb_commandes,
            "total_achats"   : self.total_achats,
            "consentement"   : self.consentement,
            "actif"          : self.actif,
            "cree_le"        : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<Client #{self.id} | {self.nom_complet()} | {self.telephone}>"
