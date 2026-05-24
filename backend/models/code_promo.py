# =============================================================
# models/code_promo.py — Codes promotionnels
# Permet de créer des codes promo pour les campagnes marketing
# =============================================================

from datetime import datetime
from backend.database import db


class CodePromo(db.Model):
    """Un code promo utilisable pendant la commande."""

    __tablename__ = "codes_promo"

    id          = db.Column(db.Integer, primary_key=True)

    # Le code que le client saisit (ex: "ETE25", "NOEL10")
    code        = db.Column(db.String(30), unique=True, nullable=False)

    # Description interne (ex: "Campagne été 2025")
    description = db.Column(db.String(200), nullable=True)

    # Réduction en pourcentage (ex: 10 = -10%)
    reduction_pct = db.Column(db.Integer, nullable=False, default=5)

    # Nombre maximum d'utilisations (None = illimité)
    max_utilisations = db.Column(db.Integer, nullable=True)

    # Nombre d'utilisations actuelles
    nb_utilisations  = db.Column(db.Integer, nullable=False, default=0)

    # Date d'expiration (None = pas d'expiration)
    expire_le   = db.Column(db.DateTime, nullable=True)

    # Actif ou non
    actif       = db.Column(db.Boolean, nullable=False, default=True)

    cree_le     = db.Column(db.DateTime, default=datetime.utcnow)

    def est_valide(self):
        """
        Vérifie si le code est utilisable.
        Conditions : actif + pas expiré + pas épuisé
        """
        if not self.actif:
            return False, "Code inactif"

        if self.expire_le and datetime.utcnow() > self.expire_le:
            return False, "Code expiré"

        if self.max_utilisations and self.nb_utilisations >= self.max_utilisations:
            return False, "Code épuisé"

        return True, "Valide"

    def vers_dict(self):
        valide, msg = self.est_valide()
        return {
            "id"              : self.id,
            "code"            : self.code,
            "description"     : self.description or "",
            "reduction_pct"   : self.reduction_pct,
            "max_utilisations": self.max_utilisations,
            "nb_utilisations" : self.nb_utilisations,
            "expire_le"       : self.expire_le.strftime("%d/%m/%Y") if self.expire_le else "Illimité",
            "actif"           : self.actif,
            "valide"          : valide,
            "message"         : msg,
            "cree_le"         : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<CodePromo {self.code} | -{self.reduction_pct}%>"
