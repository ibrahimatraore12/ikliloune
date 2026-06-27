# =============================================================
# models/commande.py — Table des commandes clients
# =============================================================

import json
import random
import string
from datetime import datetime
from backend.database import db


def _generer_numero():
    """
    Génère un numéro de commande unique.
    Format : IK[3chiffres]-YYYYMMDD
    Exemple : IK047-20260601
    """
    aujourd_hui = datetime.utcnow().strftime("%Y%m%d")
    suffixe     = ''.join(random.choices(string.digits, k=3))
    return f"IK{suffixe}-{aujourd_hui}"


class Commande(db.Model):
    """Une commande passée sur le site ou via WhatsApp."""

    __tablename__ = "commandes"

    id              = db.Column(db.Integer, primary_key=True)

    # Numéro lisible affiché au client — ex: IK047-20260601
    numero          = db.Column(db.String(20), unique=True, nullable=False,
                                default=_generer_numero)

    # --- Informations client (snapshot au moment de la commande) --
    client_nom      = db.Column(db.String(150), nullable=False)
    client_prenom   = db.Column(db.String(100), nullable=True)
    client_telephone= db.Column(db.String(30),  nullable=False)
    client_email    = db.Column(db.String(150), nullable=True)   # optionnel
    client_adresse  = db.Column(db.String(300), nullable=True)

    # --- Panier JSON -------------------------------------------
    # [{"id":1,"reference":"IKL-2026-00001","nom":"Parfum Or",
    #   "prix_actuel":28500,"qty":2,"coloris":"Or","taille":"M",
    #   "photo":"produit_1.webp"}]
    articles_json   = db.Column(db.Text, nullable=False, default="[]")

    # --- Montants FCFA -----------------------------------------
    sous_total      = db.Column(db.Integer, nullable=False, default=0)
    remise_montant  = db.Column(db.Integer, nullable=False, default=0)
    total           = db.Column(db.Integer, nullable=False, default=0)
    code_promo_utilise = db.Column(db.String(30), nullable=True)
    # --- Mode de livraison ------------------------------------
    # "click_collect" | "livraison"
    mode_livraison    = db.Column(db.String(20), nullable=False, default="click_collect")
    # "zone_1" | "zone_2" | "zone_3"
    zone_livraison    = db.Column(db.String(20), nullable=True)
    # Frais en FCFA (0 si retrait magasin)
    frais_livraison   = db.Column(db.Integer, nullable=False, default=0)
    # Adresse de livraison précise
    adresse_livraison = db.Column(db.String(300), nullable=True)

    # --- Canal et paiement -------------------------------------
    # "site_web" | "whatsapp" | "magasin"
    canal           = db.Column(db.String(20), nullable=False, default="site_web")
    # "orange_money" | "mtn_momo" | "wave" | "a_definir"
    mode_paiement   = db.Column(db.String(30), nullable=True)

    # --- Workflow statuts --------------------------------------
    # recue → confirmee → en_preparation → expediee → livree
    # depuis n'importe quel statut → annulee
    statut          = db.Column(db.String(30), nullable=False, default="recue")

    # Notes internes (admin uniquement)
    notes_admin     = db.Column(db.Text, nullable=True)

    # --- Relations ---------------------------------------------
    historique      = db.relationship("HistoriqueStatut",
                                      backref="commande",
                                      lazy=True,
                                      order_by="HistoriqueStatut.change_le")

    # --- Horodatage --------------------------------------------
    cree_le         = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    # --- Méthodes ----------------------------------------------

    def articles(self):
        """Retourne la liste des articles du panier."""
        try:
            return json.loads(self.articles_json or "[]")
        except Exception:
            return []

    def libelle_statut(self):
        """Retourne le label lisible du statut."""
        labels = {
            "recue"          : "Commande reçue",
            "confirmee"      : "Confirmée",
            "en_preparation" : "En préparation",
            "expediee"       : "Expédiée",
            "livree"         : "Livrée ✓",
            "annulee"        : "Annulée",
        }
        return labels.get(self.statut, self.statut)

    def etape_workflow(self):
        """
        Retourne le numéro d'étape pour la barre de progression client.
        0 = recue, 1 = confirmee, 2 = en_preparation, 3 = expediee, 4 = livree
        """
        etapes = ["recue", "confirmee", "en_preparation", "expediee", "livree"]
        try:
            return etapes.index(self.statut)
        except ValueError:
            return -1  # annulee

    def vers_dict(self):
        """Convertit la commande en dict pour l'API JSON."""
        return {
            "id"                 : self.id,
            "numero"             : self.numero,
            "client_nom"         : self.client_nom,
            "client_prenom"      : self.client_prenom or "",
            "client_telephone"   : self.client_telephone,
            "client_email"       : self.client_email or "",
            "client_adresse"     : self.client_adresse or "",
            "articles"           : self.articles(),
            "sous_total"         : self.sous_total,
            "remise_montant"     : self.remise_montant,
            "total"              : self.total,
            "code_promo_utilise" : self.code_promo_utilise or "",
            "canal"              : self.canal,
            "mode_livraison"     : self.mode_livraison or "click_collect",
            "zone_livraison"     : self.zone_livraison or "",
            "frais_livraison"    : self.frais_livraison or 0,
            "adresse_livraison"  : self.adresse_livraison or "",
            "mode_paiement"      : self.mode_paiement or "",
            "statut"             : self.statut,
            "libelle_statut"     : self.libelle_statut(),
            "etape_workflow"     : self.etape_workflow(),
            "notes_admin"        : self.notes_admin or "",
            "cree_le"            : self.cree_le.strftime("%d/%m/%Y %H:%M"),
        }

    def __repr__(self):
        return f"<Commande {self.numero} | {self.client_nom} | {self.total} FCFA>"


class HistoriqueStatut(db.Model):
    """
    Trace chaque changement de statut d'une commande.
    Permet de savoir qui a fait quoi et quand.
    """

    __tablename__ = "historique_statuts"

    id            = db.Column(db.Integer, primary_key=True)
    commande_id   = db.Column(db.Integer, db.ForeignKey("commandes.id"),
                              nullable=False)
    statut_avant  = db.Column(db.String(30), nullable=True)
    statut_apres  = db.Column(db.String(30), nullable=False)
    note          = db.Column(db.Text, nullable=True)
    # Qui a changé (admin username ou "système")
    modifie_par   = db.Column(db.String(80), nullable=False, default="système")
    change_le     = db.Column(db.DateTime, default=datetime.utcnow)

    def vers_dict(self):
        """Convertit en dict pour l'API JSON."""
        labels = {
            "recue"          : "Reçue",
            "confirmee"      : "Confirmée",
            "en_preparation" : "En préparation",
            "expediee"       : "Expédiée",
            "livree"         : "Livrée",
            "annulee"        : "Annulée",
        }
        return {
            "id"           : self.id,
            "commande_id"  : self.commande_id,
            "statut_avant" : labels.get(self.statut_avant, self.statut_avant or ""),
            "statut_apres" : labels.get(self.statut_apres, self.statut_apres),
            "note"         : self.note or "",
            "modifie_par"  : self.modifie_par,
            "change_le"    : self.change_le.strftime("%d/%m/%Y à %H:%M"),
        }

    def __repr__(self):
        return (f"<HistoriqueStatut cmd#{self.commande_id} | "
                f"{self.statut_avant} → {self.statut_apres}>")
