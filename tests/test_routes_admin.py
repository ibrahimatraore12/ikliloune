# =============================================================
# tests/test_routes_admin.py — Tests des routes admin protégées
# Vérifie : authentification, CRUD produits, statuts commandes
# =============================================================

import json
import io
import pytest


class TestAuthentification:
    """Tests des routes de connexion / déconnexion admin."""

    def test_acces_dashboard_sans_connexion_redirige(self, client_test, app):
        """Un utilisateur non connecté doit être redirigé vers le login."""
        from backend import config
        rep = client_test.get("/" + config.ADMIN_URL_DASHBOARD)
        # Flask-Login redirige vers login_view → 302
        assert rep.status_code == 302

    def test_page_login_accessible(self, client_test, app):
        """La page de login doit être accessible sans authentification."""
        from backend import config
        rep = client_test.get("/" + config.ADMIN_URL_SECRET)
        assert rep.status_code == 200

    def test_login_credentials_incorrects(self, client_test, app):
        """Des credentials incorrects doivent renvoyer 401 ou afficher une erreur."""
        from backend import config
        rep = client_test.post(
            "/" + config.ADMIN_URL_SECRET,
            data={"username": "mauvais", "password": "mauvais"},
            follow_redirects=True
        )
        # La page de login est re-affichée (pas de redirection vers dashboard)
        assert rep.status_code == 200
        assert b"incorrect" in rep.data.lower() or b"invalid" in rep.data.lower() or \
               b"erreur" in rep.data.lower() or rep.status_code == 401

    def test_dashboard_accessible_apres_connexion(self, admin_connecte, app):
        """Un admin connecté doit pouvoir accéder au dashboard."""
        from backend import config
        rep = admin_connecte.get("/" + config.ADMIN_URL_DASHBOARD)
        assert rep.status_code == 200


class TestAPIProduitAdmin:
    """Tests du CRUD produits via l'API admin."""

    def test_liste_produits_admin_requiert_connexion(self, client_test):
        """Sans connexion, /admin/api/produits doit rediriger."""
        rep = client_test.get("/admin/api/produits")
        assert rep.status_code in (302, 401)

    def test_liste_produits_admin_avec_connexion(self, admin_connecte):
        """Avec connexion, l'API retourne tous les produits (actifs + inactifs)."""
        rep  = admin_connecte.get("/admin/api/produits")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert isinstance(data, list)
        # Doit inclure le produit inactif (visible uniquement en admin)
        noms = [p["nom"] for p in data]
        assert "Produit Retiré" in noms

    def test_liste_produits_admin_expose_stock_reel(self, admin_connecte):
        """vers_dict_admin() doit exposer le stock numérique réel."""
        rep  = admin_connecte.get("/admin/api/produits")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        # Au moins un produit doit avoir un stock numérique (entier)
        stocks = [p.get("stock") for p in data if p.get("stock") is not None]
        assert len(stocks) > 0
        assert all(isinstance(s, int) for s in stocks)

    def test_ajouter_produit_manque_champs(self, admin_connecte):
        """Créer un produit sans nom ni prix → 400."""
        rep = admin_connecte.post(
            "/admin/api/produit/ajouter",
            data={"categorie": "parfum"},
            content_type="multipart/form-data"
        )
        assert rep.status_code == 400

    def test_ajouter_produit_succes(self, admin_connecte, app):
        """Créer un produit complet → 200 avec succes=True."""
        rep  = admin_connecte.post(
            "/admin/api/produit/ajouter",
            data={
                "nom"      : "Parfum Intégration Test",
                "categorie": "parfum",
                "genre"    : "femme",
                "prix"     : "25000",
                "stock"    : "5",
            },
            content_type="multipart/form-data"
        )
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert data["succes"] is True
        assert data["produit"]["nom"] == "Parfum Intégration Test"

        # Nettoyer — soft delete
        pid = data["produit"]["id"]
        with app.app_context():
            from backend.models.produit import Produit
            from backend.database import db
            p = db.session.get(Produit, pid)
            if p:
                db.session.delete(p)
                db.session.commit()

    def test_supprimer_produit_soft_delete(self, admin_connecte, app):
        """Supprimer un produit → actif=False (pas de DELETE physique)."""
        # Créer un produit temporaire
        rep_create = admin_connecte.post(
            "/admin/api/produit/ajouter",
            data={"nom": "Temp Delete", "categorie": "sac", "genre": "femme",
                  "prix": "1000", "stock": "1"},
            content_type="multipart/form-data"
        )
        pid = json.loads(rep_create.data)["produit"]["id"]

        # Le supprimer (soft delete)
        rep = admin_connecte.delete(f"/admin/api/produit/supprimer/{pid}")
        assert rep.status_code == 200
        assert json.loads(rep.data)["succes"] is True

        # Vérifier qu'il est bien désactivé et pas supprimé
        with app.app_context():
            from backend.models.produit import Produit
            from backend.database import db
            p = db.session.get(Produit, pid)
            assert p is not None     # toujours en base
            assert p.actif is False  # mais désactivé
            db.session.delete(p)
            db.session.commit()


class TestAPICommandesAdmin:
    """Tests de la gestion des commandes en admin."""

    def test_liste_commandes_requiert_connexion(self, client_test):
        """Sans connexion → redirige."""
        rep = client_test.get("/admin/api/commandes")
        assert rep.status_code in (302, 401)

    def test_liste_commandes_avec_connexion(self, admin_connecte):
        """Avec connexion → retourne la liste des commandes."""
        rep  = admin_connecte.get("/admin/api/commandes")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert isinstance(data, list)

    def test_changer_statut_commande(self, admin_connecte, app):
        """Changer le statut → succes + historique créé + notif WA."""
        with app.app_context():
            from backend.models.commande import Commande, HistoriqueStatut
            from backend.database import db

            c = Commande.query.first()
            statut_avant = c.statut

            rep  = admin_connecte.post(
                f"/admin/api/commande/statut/{c.id}",
                data=json.dumps({"statut": "confirmee", "note": "Test pytest"}),
                content_type="application/json"
            )
            data = json.loads(rep.data)
            assert rep.status_code == 200
            assert data["succes"] is True

            # Vérifier la persistance
            db.session.refresh(c)
            assert c.statut == "confirmee"

            # Vérifier que l'historique a été enregistré
            hist = HistoriqueStatut.query.filter_by(commande_id=c.id).first()
            assert hist is not None
            assert hist.statut_avant == statut_avant
            assert hist.statut_apres == "confirmee"

            # Remettre le statut initial
            c.statut = statut_avant
            db.session.commit()

    def test_changer_statut_invalide_400(self, admin_connecte, app):
        """Un statut invalide doit retourner 400."""
        with app.app_context():
            from backend.models.commande import Commande
            c = Commande.query.first()

            rep = admin_connecte.post(
                f"/admin/api/commande/statut/{c.id}",
                data=json.dumps({"statut": "statut_inexistant"}),
                content_type="application/json"
            )
            assert rep.status_code == 400


class TestAPIBanniereCRUD:
    """Tests du CRUD bannières en admin."""

    def test_creer_banniere(self, admin_connecte):
        """Créer une bannière avec titre → 201."""
        rep  = admin_connecte.post(
            "/admin/api/banniere/creer",
            data=json.dumps({
                "titre"        : "Bannière Test Pytest",
                "sous_titre"   : "Test de création",
                "texte_bouton" : "Voir",
                "lien_bouton"  : "/",
                "collection"   : "les-deux",
                "ordre"        : 99,
            }),
            content_type="application/json"
        )
        data = json.loads(rep.data)
        assert rep.status_code == 201
        assert data["succes"] is True
        assert data["banniere"]["titre"] == "Bannière Test Pytest"
        return data["banniere"]["id"]

    def test_creer_banniere_sans_titre_400(self, admin_connecte):
        """Créer une bannière sans titre → 400."""
        rep = admin_connecte.post(
            "/admin/api/banniere/creer",
            data=json.dumps({"sous_titre": "Pas de titre"}),
            content_type="application/json"
        )
        assert rep.status_code == 400

    def test_liste_bannieres_admin(self, admin_connecte):
        """La liste admin retourne toutes les bannières."""
        rep  = admin_connecte.get("/admin/api/bannieres")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        assert isinstance(data, list)


class TestExportAdmin:
    """Tests des exports de données (Excel, CSV)."""

    def test_export_clients_csv(self, admin_connecte):
        """L'export CSV clients doit retourner un fichier CSV."""
        rep = admin_connecte.get("/admin/api/clients/export-csv")
        assert rep.status_code == 200
        assert "text/csv" in rep.content_type
        assert b"telephone" in rep.data.lower() or b"prenom" in rep.data.lower()

    def test_stats_kpis_json(self, admin_connecte):
        """Le endpoint KPIs JSON doit retourner les champs attendus."""
        rep  = admin_connecte.get("/admin/api/stats/kpis")
        data = json.loads(rep.data)
        assert rep.status_code == 200
        champs = ["nb_produits", "nb_commandes", "nb_clients", "ruptures", "ca_mois"]
        for champ in champs:
            assert champ in data, f"KPI manquant : {champ}"
