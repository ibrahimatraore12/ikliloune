# =============================================================
# database.py — Connexion SQLAlchemy + initialisation des tables
# =============================================================

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def initialiser_db(app):
    """
    Connecte SQLAlchemy à Flask et crée toutes les tables.
    Appelée une seule fois dans main.py (factory pattern).
    """
    db.init_app(app)

    with app.app_context():
        # Importer tous les modèles pour que SQLAlchemy les connaisse
        from backend.models.produit    import Produit        # noqa
        from backend.models.commande   import Commande, HistoriqueStatut  # noqa
        from backend.models.client     import Client         # noqa
        from backend.models.admin      import Admin          # noqa
        from backend.models.code_promo import CodePromo      # noqa
        from backend.models.banniere   import Banniere       # noqa

        db.create_all()   # crée les tables manquantes sans effacer les existantes

    print("✅ Base de données prête")
