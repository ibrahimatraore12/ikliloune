# =============================================================
# tests/test_routes_boutique.py — Tests d'intégration des routes
# publiques (boutique, API produits, suivi commande)
# =============================================================

import json
import pytest


class TestRoutesPubliques:
    """Tests des pages HTML accessibles sans authentification."""

    def test_page_accueil_200(self, client_test):
        """La page d'accueil doit retourner HTTP 200."""
        rep = client_test.get("/")
        assert rep.status_code == 200

    def test_page_suivi_200(self, client_test):
        """La page de suivi de commande doit être accessible."""
        rep = client_test.get("/suivi")
        assert rep.status_code == 200

    def test_health_check(self, client_test):
        """Le endpoint /health doit retourner {"status": "ok"}."""
        rep  = client_test.get("/health")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert data["status"] == "ok"
        assert data["app"] == "IKLILOUNE"


class TestAPIProduits:
    """Tests de l'API produits — filtres, tri, détail."""

    def test_api_produits_retourne_liste(self, client_test):
        """GET /api/produits doit retourner une liste et un total."""
        rep  = client_test.get("/api/produits")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert "produits" in data
        assert "total" in data
        assert isinstance(data["produits"], list)

    def test_api_produits_seulement_actifs(self, client_test):
        """L'API ne doit retourner que les produits actifs."""
        rep  = client_test.get("/api/produits")
        data = json.loads(rep.data)
        for p in data["produits"]:
            # actif n'est pas exposé dans vers_dict() — vérifions via le nom
            assert p["nom"] != "Produit Retiré"

    def test_api_produits_filtre_categorie(self, client_test):
        """Le filtre ?categorie=parfum doit retourner uniquement les parfums."""
        rep  = client_test.get("/api/produits?categorie=parfum")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        for p in data["produits"]:
            assert p["categorie"] == "parfum"

    def test_api_produits_filtre_genre_femme(self, client_test):
        """Le filtre ?genre=femme doit inclure femme et mixte."""
        rep  = client_test.get("/api/produits?genre=femme")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        for p in data["produits"]:
            assert p["genre"] in ("femme", "mixte")

    def test_api_produits_recherche(self, client_test):
        """?q=Rose doit trouver le produit "Rose d'Or Test"."""
        rep  = client_test.get("/api/produits?q=Rose")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert any("Rose" in p["nom"] for p in data["produits"])

    def test_api_produits_tri_prix_asc(self, client_test):
        """?tri=prix-asc doit retourner les produits du moins cher au plus cher."""
        rep  = client_test.get("/api/produits?tri=prix-asc")
        data = json.loads(rep.data)
        prix = [p["prix"] for p in data["produits"]]
        assert prix == sorted(prix)

    def test_api_produit_detail(self, client_test, app):
        """GET /api/produits/<id> doit retourner le détail du produit."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit.query.filter_by(actif=True).first()
            assert p is not None
            rep  = client_test.get(f"/api/produits/{p.id}")
            data = json.loads(rep.data)
            assert rep.status_code == 200
            assert data["id"] == p.id
            assert data["nom"] == p.nom

    def test_api_produit_inexistant_404(self, client_test):
        """Un ID de produit inexistant doit retourner 404."""
        rep = client_test.get("/api/produits/999999")
        assert rep.status_code == 404

    def test_api_produit_ne_pas_exposer_stock_brut(self, client_test, app):
        """L'API publique ne doit pas exposer le stock numérique."""
        with app.app_context():
            from backend.models.produit import Produit
            p = Produit.query.filter_by(actif=True).first()
            rep  = client_test.get(f"/api/produits/{p.id}")
            data = json.loads(rep.data)
            # stock brut masqué, indicateur couleur exposé
            assert "stock" not in data
            assert "stock_indicateur" in data
            assert data["stock_indicateur"] in ("vert", "orange", "rouge", "rupture")

    def test_api_produit_incremente_nb_consultations(self, client_test, app):
        """Chaque appel à /api/produits/<id> doit incrémenter nb_consultations."""
        with app.app_context():
            from backend.models.produit import Produit
            from backend.database import db
            p = Produit.query.filter_by(actif=True).first()
            nb_avant = p.nb_consultations or 0

            client_test.get(f"/api/produits/{p.id}")

            db.session.refresh(p)
            assert p.nb_consultations == nb_avant + 1


class TestAPIBannieres:
    """Tests de l'API bannières publique."""

    def test_api_bannieres_retourne_liste(self, client_test):
        """GET /api/bannieres doit retourner une liste de bannières visibles."""
        rep  = client_test.get("/api/bannieres")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert "bannieres" in data
        assert isinstance(data["bannieres"], list)


class TestAPISuiviCommande:
    """Tests de l'API de suivi commande — sécurité et données."""

    def test_suivi_sans_parametres_400(self, client_test):
        """Appel sans numéro et téléphone → 400."""
        rep = client_test.get("/api/commandes/suivi")
        assert rep.status_code == 400

    def test_suivi_commande_inexistante_404(self, client_test):
        """Numéro inexistant → 404."""
        rep = client_test.get("/api/commandes/suivi?numero=IK999-99999999&telephone=0700000000")
        assert rep.status_code == 404

    def test_suivi_telephone_incorrect_403(self, client_test, app):
        """Bon numéro mais mauvais téléphone → 403."""
        with app.app_context():
            from backend.models.commande import Commande
            c = Commande.query.first()
            rep = client_test.get(
                f"/api/commandes/suivi?numero={c.numero}&telephone=0000000000"
            )
            assert rep.status_code == 403

    def test_suivi_commande_valide(self, client_test, app):
        """Bon numéro + bon téléphone → 200 avec données commande."""
        with app.app_context():
            from backend.models.commande import Commande
            c = Commande.query.first()
            rep  = client_test.get(
                f"/api/commandes/suivi?numero={c.numero}&telephone={c.client_telephone}"
            )
            data = json.loads(rep.data)
            assert rep.status_code == 200
            assert "commande" in data
            assert data["commande"]["numero"] == c.numero
