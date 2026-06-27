# =============================================================
# models/historique_stock.py — Audit complet des mouvements de stock
# OBJECTIF SÉCURITÉ : détecter toute manipulation frauduleuse.
# =============================================================
from datetime import datetime
from backend.database import db


class HistoriqueStock(db.Model):
    """
    Trace CHAQUE modification de stock, quelle qu'en soit la cause.

    Types de mouvement :
        ajout_initial       — création d'un produit avec stock > 0
        ajustement_manuel   — admin modifie le stock depuis l'interface
        vente               — commande confirmée → stock décrémenté
        annulation_commande — commande annulée  → stock remis en rayon
        desactivation       — produit désactivé (retiré du catalogue)
        reactivation        — produit réactivé (remis en ligne)
        correction          — correction ponctuelle documentée
        vente_magasin       — vente directe en boutique (caisse)
    """
    __tablename__ = "historique_stock"

    id             = db.Column(db.Integer, primary_key=True)
    produit_id     = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    type_mouvement = db.Column(db.String(40), nullable=False, index=True)
    quantite_avant = db.Column(db.Integer, nullable=False)
    quantite_apres = db.Column(db.Integer, nullable=False)
    delta          = db.Column(db.Integer, nullable=False)   # + entrée, - sortie
    commande_id    = db.Column(db.Integer, db.ForeignKey("commandes.id"), nullable=True)
    note           = db.Column(db.String(300), nullable=True)

    produit  = db.relationship("Produit",
                               backref=db.backref("mouvements_stock", lazy="dynamic"))
    commande = db.relationship("Commande",
                               backref=db.backref("mouvements_stock", lazy="dynamic"))

    def __repr__(self):
        signe = "+" if self.delta >= 0 else ""
        return (f"<HistoriqueStock [{self.type_mouvement}] "
                f"{signe}{self.delta} produit_id={self.produit_id}>")

    def vers_dict(self):
        return {
            "id"           : self.id,
            "produit_id"   : self.produit_id,
            "produit_nom"  : self.produit.nom if self.produit else "—",
            "produit_ref"  : self.produit.reference if self.produit else "—",
            "date"         : self.date_mouvement.strftime("%d/%m/%Y %H:%M"),
            "type"         : self.type_mouvement,
            "avant"        : self.quantite_avant,
            "apres"        : self.quantite_apres,
            "delta"        : self.delta,
            "commande_id"  : self.commande_id,
            "commande_num" : self.commande.numero if self.commande else "",
            "note"         : self.note or "",
        }
