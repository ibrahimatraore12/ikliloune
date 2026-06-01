# =============================================================
# tests/test_modeles.py — Tests unitaires des modèles SQLAlchemy
# Vérifie la logique métier : indicateurs stock, numéros,
# validité codes promo, historique statuts, etc.
# =============================================================

import pytest
from datetime import datetime, timedelta


class TestProduit:
    """Tests du modèle Produit — logique métier et indicateurs."""

    def test_indicateur_vert_stock_suffisant(self, app):
        """Un produit avec stock > seuil_haut → indicateur vert."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="parfum", genre="femme",
                        prix=1000, stock=20, seuil_haut=10, seuil_bas=3)
            assert p.indicateur_stock() == "vert"

    def test_indicateur_orange_stock_moyen(self, app):
        """Un produit avec stock entre seuil_bas et seuil_haut → orange."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="sac", genre="femme",
                        prix=1000, stock=5, seuil_haut=10, seuil_bas=3)
            assert p.indicateur_stock() == "orange"

    def test_indicateur_rouge_stock_bas(self, app):
        """Un produit avec stock <= seuil_bas (mais > 0) → rouge."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="chaussure", genre="homme",
                        prix=1000, stock=2, seuil_haut=10, seuil_bas=3)
            assert p.indicateur_stock() == "rouge"

    def test_indicateur_rupture(self, app):
        """Un produit avec stock = 0 → rupture."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="parfum", genre="mixte",
                        prix=1000, stock=0)
            assert p.indicateur_stock() == "rupture"

    def test_vers_dict_ne_pas_exposer_stock_brut(self, app):
        """vers_dict() expose stock_indicateur mais PAS le stock réel."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="parfum", genre="femme",
                        prix=1000, stock=7)
            d = p.vers_dict()
            # Le client ne doit jamais voir le stock numérique
            assert "stock_indicateur" in d
            assert "stock" not in d   # stock brut masqué

    def test_vers_dict_admin_expose_stock(self, app):
        """vers_dict_admin() doit exposer le stock réel pour l'admin."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="parfum", genre="femme",
                        prix=1000, stock=7)
            d = p.vers_dict_admin()
            assert "stock" in d
            assert d["stock"] == 7

    def test_reference_generee_automatiquement(self, app):
        """La référence IKL-YYYY-XXXXX doit être générée à la création."""
        with app.app_context():
            from backend.database import db
            from backend.models.produit import Produit
            p = Produit(nom="Ref Test", categorie="sac", genre="femme",
                        prix=5000, stock=1)
            db.session.add(p)
            db.session.commit()
            assert p.reference is not None
            assert p.reference.startswith("IKL-")
            db.session.delete(p)
            db.session.commit()

    def test_prix_actuel_retourne_promo_si_disponible(self, app):
        """prix_actuel doit retourner prix_promo s'il est défini."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="parfum", genre="femme",
                        prix=28500, prix_promo=19900)
            d = p.vers_dict()
            assert d["prix_actuel"] == 19900

    def test_prix_actuel_retourne_prix_normal(self, app):
        """Sans prix_promo, prix_actuel = prix normal."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit(nom="Test", categorie="sac", genre="femme",
                        prix=45000, prix_promo=None)
            d = p.vers_dict()
            assert d["prix_actuel"] == 45000


class TestCommande:
    """Tests du modèle Commande — numéros, workflow, libellés."""

    def test_numero_format_correct(self, app):
        """Le numéro de commande doit respecter le format IK###-YYYYMMDD."""
        with app.app_context():
            from backend.database import db
            from backend.models.commande import Commande
            c = Commande(
                client_nom="Test", client_telephone="0700000000",
                articles_json="[]", total=1000, statut="recue"
            )
            db.session.add(c)
            db.session.commit()

            # Format : IK + 3 chiffres + tiret + 8 chiffres date
            import re
            assert re.match(r"^IK\d{3}-\d{8}$", c.numero), f"Format invalide: {c.numero}"
            db.session.delete(c)
            db.session.commit()

    def test_libelle_statut_recue(self, app):
        """libelle_statut() doit retourner un texte lisible pour 'recue'."""
        with app.app_context():
            from backend.models.commande import Commande
            c = Commande(statut="recue", client_nom="T", client_telephone="0",
                         articles_json="[]", total=0)
            assert c.libelle_statut()  # non vide
            assert isinstance(c.libelle_statut(), str)

    def test_etape_workflow_valeurs(self, app):
        """etape_workflow() doit retourner 0-4 selon le statut."""
        with app.app_context():
            from backend.models.commande import Commande
            etapes = {
                "recue"         : 0,
                "confirmee"     : 1,
                "en_preparation": 2,
                "expediee"      : 3,
                "livree"        : 4,
            }
            for statut, etape_attendue in etapes.items():
                c = Commande(statut=statut, client_nom="T", client_telephone="0",
                             articles_json="[]", total=0)
                assert c.etape_workflow() == etape_attendue, \
                    f"Statut {statut} → attendu {etape_attendue}, obtenu {c.etape_workflow()}"

    def test_vers_dict_contient_champs_essentiels(self, app):
        """vers_dict() doit contenir les champs nécessaires au frontend."""
        with app.app_context():
            from backend.models.commande import Commande
            c = Commande(
                client_nom="Koné", client_telephone="0700000000",
                articles_json='[{"nom":"Parfum","prix_unitaire":1000,"quantite":1}]',
                total=1000, statut="recue"
            )
            d = c.vers_dict()
            champs = ["numero", "statut", "total", "libelle_statut", "etape_workflow"]
            for champ in champs:
                assert champ in d, f"Champ manquant dans vers_dict() : {champ}"


class TestCodePromo:
    """Tests du service codes promo — validation et calcul de remise."""

    def test_code_inactif_invalide(self, app):
        """Un code désactivé doit être refusé."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="TEST_INACTIF", reduction_pct=10, actif=False
            )
            assert not code.est_valide(panier_total=10000, nb_commandes_client=0)

    def test_code_expire_invalide(self, app):
        """Un code expiré doit être refusé même s'il est actif."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="TEST_EXPIRE", reduction_pct=10, actif=True,
                expire_le=datetime(2020, 1, 1)  # passé
            )
            assert not code.est_valide(panier_total=10000, nb_commandes_client=0)

    def test_code_valide_retourne_true(self, app):
        """Un code actif et non expiré doit être accepté."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="TEST_OK", reduction_pct=10, actif=True,
                expire_le=datetime(2030, 1, 1), conditions="tous"
            )
            assert code.est_valide(panier_total=10000, nb_commandes_client=5)

    def test_calculer_remise_pourcentage(self, app):
        """calculer_remise() doit appliquer le bon pourcentage."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="PCT", reduction_pct=10,
                type_reduction="pourcentage", actif=True
            )
            remise = code.calculer_remise(panier_total=50000)
            assert remise == 5000, f"Remise attendue 5000, obtenue {remise}"

    def test_code_nouveaux_clients_refuse_client_existant(self, app):
        """Un code 'nouveaux_clients' doit être refusé si le client a déjà commandé."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="NEW", reduction_pct=5, actif=True,
                conditions="nouveaux_clients"
            )
            # Client avec 2 commandes = pas nouveau
            assert not code.est_valide(panier_total=10000, nb_commandes_client=2)
            # Client avec 0 commandes = nouveau ✓
            assert code.est_valide(panier_total=10000, nb_commandes_client=0)

    def test_montant_minimum_panier(self, app):
        """Un code avec montant_min doit être refusé si le panier est trop petit."""
        with app.app_context():
            from backend.models.code_promo import CodePromo
            code = CodePromo(
                code="MIN5000", reduction_pct=10, actif=True,
                montant_min=5000, conditions="tous"
            )
            # Panier trop petit
            assert not code.est_valide(panier_total=3000, nb_commandes_client=0)
            # Panier suffisant
            assert code.est_valide(panier_total=5000, nb_commandes_client=0)


class TestBanniere:
    """Tests du modèle Bannière — visibilité selon dates."""

    def test_banniere_active_sans_dates_visible(self, app):
        """Une bannière active sans dates de début/fin est toujours visible."""
        with app.app_context():
            from backend.models.banniere import Banniere
            b = Banniere(titre="Test", actif=True,
                         date_debut=None, date_fin=None)
            assert b.est_visible()

    def test_banniere_inactive_non_visible(self, app):
        """Une bannière désactivée ne doit jamais être visible."""
        with app.app_context():
            from backend.models.banniere import Banniere
            b = Banniere(titre="Test", actif=False)
            assert not b.est_visible()

    def test_banniere_avant_date_debut_non_visible(self, app):
        """Une bannière dont la date de début est dans le futur n'est pas visible."""
        with app.app_context():
            from backend.models.banniere import Banniere
            b = Banniere(
                titre="Test", actif=True,
                date_debut=datetime.utcnow() + timedelta(days=7)
            )
            assert not b.est_visible()

    def test_banniere_apres_date_fin_non_visible(self, app):
        """Une bannière dont la date de fin est passée n'est plus visible."""
        with app.app_context():
            from backend.models.banniere import Banniere
            b = Banniere(
                titre="Test", actif=True,
                date_fin=datetime.utcnow() - timedelta(days=1)
            )
            assert not b.est_visible()

    def test_banniere_dans_plage_visible(self, app):
        """Une bannière avec dates passées/futures encadrant maintenant est visible."""
        with app.app_context():
            from backend.models.banniere import Banniere
            b = Banniere(
                titre="Test", actif=True,
                date_debut=datetime.utcnow() - timedelta(days=5),
                date_fin=datetime.utcnow() + timedelta(days=5)
            )
            assert b.est_visible()
