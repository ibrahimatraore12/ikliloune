# =============================================================
# database.py — Connexion SQLite via SQLAlchemy
# Crée l'objet db utilisé dans tous les modèles.
# =============================================================

from flask_sqlalchemy import SQLAlchemy

# Objet central — importé dans chaque modèle
# db.Model    = classe de base pour toutes les tables
# db.session  = pour lire / écrire / supprimer des données
db = SQLAlchemy()


def initialiser_db(app):
    """
    Connecte SQLAlchemy à Flask et crée les tables.
    Appelée une seule fois dans main.py.
    """
    db.init_app(app)

    with app.app_context():
        # Importer les modèles ici pour que SQLAlchemy les connaisse
        # avant de créer les tables
        from backend.models.produit  import Produit   # noqa
        from backend.models.commande import Commande  # noqa
        from backend.models.client   import Client    # noqa
        from backend.models.admin      import Admin      # noqa
        from backend.models.code_promo  import CodePromo  # noqa

        db.create_all()   # crée les tables si elles n'existent pas

    print("✅ Base de données prête — ikliloune.db")
