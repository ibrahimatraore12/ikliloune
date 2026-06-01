# =============================================================
# models/code_promo.py — Codes promotionnels
# =============================================================

from datetime import datetime
from backend.database import db


class CodePromo(db.Model):
    """Un code promo utilisable pendant la commande."""

    __tablename__ = "codes_promo"

    id          = db.Column(db.Integer, primary_key=True)
    code        = db.Column(db.String(30), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Type : "pourcentage" | "montant_fixe"
    type_reduction   = db.Column(db.String(20), nullable=False, default="pourcentage")
    valeur           = db.Column(db.Integer,    nullable=False, default=5)

    # Conditions d'application
    # "tous" | "nouveaux_clients" | "evenement"
    conditions       = db.Column(db.String(30), nullable=False, default="tous")

    # Montant minimum du panier pour que le code s'applique (0 = pas de minimum)
    montant_min      = db.Column(db.Integer, nullable=False, default=0)

    # Limites temporelles
    date_debut       = db.Column(db.DateTime, nullable=True)
    date_fin         = db.Column(db.DateTime, nullable=True)

    # Limites d'usage
    max_utilisations = db.Column(db.Integer, nullable=True)   # None = illimité
    nb_utilisations  = db.Column(db.Integer, nullable=False, default=0)

    # Soft delete
    actif            = db.Column(db.Boolean, nullable=False, default=True)
    cree_le          = db.Column(db.DateTime, default=datetime.utcnow)

    # Rétrocompatibilité (ancien champ)
    reduction_pct    = db.Column(db.Integer, nullable=True)
    expire_le        = db.Column(db.DateTime, nullable=True)

    def calculer_remise(self, total_panier):
        """
        Calcule le montant de la remise en FCFA.

        Paramètre :
            total_panier (int) : montant du panier en FCFA

        Retourne :
            int : montant de la réduction en FCFA
        """
        if self.type_reduction == "pourcentage":
            pct = self.valeur or self.reduction_pct or 0
            return int(total_panier * pct / 100)
        elif self.type_reduction == "montant_fixe":
            return min(self.valeur, total_panier)
        return 0

    def est_valide(self, total_panier=0, nb_commandes_client=0):
        """
        Vérifie si le code est utilisable.

        Paramètres :
            total_panier        (int) : montant du panier en FCFA
            nb_commandes_client (int) : nombre de commandes passées par ce client

        Retourne :
            tuple (bool, str) : (valide, message)
        """
        if not self.actif:
            return False, "Ce code promo est inactif"

        maintenant = datetime.utcnow()

        # Vérifier date_fin (aussi expire_le pour rétrocompatibilité)
        fin = self.date_fin or self.expire_le
        if fin and maintenant > fin:
            return False, "Ce code promo a expiré"

        # Vérifier date de début
        if self.date_debut and maintenant < self.date_debut:
            return False, "Ce code promo n'est pas encore actif"

        # Vérifier le nombre d'utilisations maximum
        if self.max_utilisations and self.nb_utilisations >= self.max_utilisations:
            return False, "Ce code promo a atteint son nombre maximum d'utilisations"

        # Vérifier le montant minimum du panier
        if self.montant_min and total_panier < self.montant_min:
            return False, f"Panier minimum requis : {self.montant_min:,} FCFA".replace(",", " ")

        # Vérifier conditions nouveaux clients
        if self.conditions == "nouveaux_clients" and nb_commandes_client > 0:
            return False, "Ce code est réservé aux nouveaux clients"

        return True, "Code valide"

    def vers_dict(self):
        """Convertit en dict pour l'API JSON."""
        pct = self.valeur if self.type_reduction == "pourcentage" else (self.reduction_pct or 0)
        valide, msg = self.est_valide()
        fin = self.date_fin or self.expire_le
        return {
            "id"              : self.id,
            "code"            : self.code,
            "description"     : self.description or "",
            "type_reduction"  : self.type_reduction,
            "valeur"          : self.valeur,
            "reduction_pct"   : pct,
            "conditions"      : self.conditions,
            "montant_min"     : self.montant_min,
            "date_debut"      : self.date_debut.strftime("%d/%m/%Y") if self.date_debut else "",
            "date_fin"        : fin.strftime("%d/%m/%Y") if fin else "Illimité",
            "max_utilisations": self.max_utilisations,
            "nb_utilisations" : self.nb_utilisations,
            "actif"           : self.actif,
            "valide"          : valide,
            "message"         : msg,
            "cree_le"         : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<CodePromo {self.code} | -{self.valeur}{'%' if self.type_reduction == 'pourcentage' else ' FCFA'}>"
