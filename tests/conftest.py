# =============================================================
# tests/conftest.py — Configuration pytest pour IKLILOUNE
# Crée une application Flask de test avec SQLite en mémoire.
# Les fixtures sont partagées par tous les fichiers de test.
# =============================================================

import pytest
from main import creer_app
from backend.database import db as _db


@pytest.fixture(scope="session")
def app():
    """
    Crée une instance de l'application Flask configurée pour les tests.
    - Base de données SQLite en mémoire (rapide, isolée)
    - TESTING=True pour désactiver certaines protections (CSRF, etc.)
    - DEBUG=False pour tester le comportement de production

    scope="session" → l'app est créée une seule fois pour toute la session.
    """
    _app = creer_app()
    _app.config.update({
        "TESTING"                    : True,
        "SQLALCHEMY_DATABASE_URI"    : "sqlite:///:memory:",
        "WTF_CSRF_ENABLED"           : False,   # désactivé en test
        "SERVER_NAME"                : "localhost",
        "SECRET_KEY"                 : "test-secret-key-ikliloune",
    })

    with _app.app_context():
        _db.create_all()
        _init_donnees_test()
        yield _app
        _db.drop_all()


def _init_donnees_test():
    """
    Peuple la base de test avec des données minimales :
    - 1 compte admin
    - 2 produits (parfum + sac)
    - 1 commande
    - 1 code promo
    """
    from backend.models.admin      import Admin
    from backend.models.produit    import Produit
    from backend.models.commande   import Commande
    from backend.models.client     import Client
    from backend.models.code_promo import CodePromo
    import json

    # Admin
    admin = Admin(username="admin_test")
    admin.set_password("MotDePasse123!")
    _db.session.add(admin)

    # Produit 1 — parfum
    parfum = Produit(
        nom       = "Rose d'Or Test",
        categorie = "parfum",
        genre     = "femme",
        prix      = 28500,
        stock     = 10,
        actif     = True,
    )
    _db.session.add(parfum)

    # Produit 2 — sac (stock bas)
    sac = Produit(
        nom       = "Sac Python Test",
        categorie = "sac",
        genre     = "femme",
        prix      = 45000,
        stock     = 2,   # stock bas → indicateur rouge
        actif     = True,
    )
    _db.session.add(sac)

    # Produit 3 — désactivé
    inactif = Produit(
        nom       = "Produit Retiré",
        categorie = "vetement",
        genre     = "homme",
        prix      = 15000,
        stock     = 5,
        actif     = False,
    )
    _db.session.add(inactif)

    _db.session.flush()  # pour avoir les IDs

    # Client
    client = Client(
        prenom    = "Fatou",
        nom       = "Koné",
        telephone = "0748956959",
        email     = "fatou.test@example.com",
        source    = "commande",
    )
    _db.session.add(client)
    _db.session.flush()

    # Commande
    articles = json.dumps([{
        "id": parfum.id, "nom": "Rose d'Or Test",
        "prix_unitaire": 28500, "quantite": 1,
        "categorie": "parfum"
    }])
    commande = Commande(
        client_nom       = "Koné",
        client_prenom    = "Fatou",
        client_telephone = "0748956959",
        client_adresse   = "Cocody, Abidjan",
        articles_json    = articles,
        sous_total       = 28500,
        total            = 28500,
        statut           = "recue",
        canal            = "site_web",
        paiement         = "orange",
    )
    _db.session.add(commande)

    # Code promo
    promo = CodePromo(
        code          = "TESTCODE",
        description   = "Code test",
        reduction_pct = 10,
        actif         = True,
        conditions    = "tous",
    )
    _db.session.add(promo)

    _db.session.commit()


@pytest.fixture(scope="function")
def client_test(app):
    """
    Client HTTP Flask pour les tests de routes.
    scope="function" → nouveau client pour chaque test.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def ctx(app):
    """Contexte d'application pour accéder à la BDD directement."""
    with app.app_context():
        yield


@pytest.fixture(scope="function")
def admin_connecte(client_test, app):
    """
    Client HTTP avec un admin déjà connecté.
    Utile pour tester les routes @login_required.
    """
    with app.app_context():
        from backend.models.admin import Admin
        admin = Admin.query.first()
        # Simuler la connexion Flask-Login via le test client
        with client_test.session_transaction() as sess:
            sess["_user_id"] = str(admin.id)
    return client_test
