# =============================================================
# main.py — Point d'entrée de l'application IKLILOUNE
# Lance le serveur : python main.py
# =============================================================

from flask import Flask
from flask_login import LoginManager
from backend import config
from backend.database import db, initialiser_db
from backend.models.admin import Admin


def creer_app():
    """
    Crée, configure et retourne l'application Flask.
    Séparée de if __name__ == '__main__' pour les tests.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # --- Configuration Flask -----------------------------------
    app.config["SECRET_KEY"]                  = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"]     = config.URL_DB
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"]          = config.TAILLE_MAX_UPLOAD
    app.config["WTF_CSRF_ENABLED"]            = False

    # --- Base de données ---------------------------------------
    initialiser_db(app)

    # --- Flask-Login -------------------------------------------
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"   # redirect si non connecté
    login_manager.login_message = "Connexion requise."

    @login_manager.user_loader
    def charger_admin(admin_id):
        """Flask-Login appelle cette fonction à chaque requête admin."""
        return db.session.get(Admin, int(admin_id))

    # --- Enregistrement des routes (Blueprints) ----------------
    from backend.routes.boutique  import boutique_bp
    from backend.routes.commande  import commande_bp
    from backend.routes.admin     import admin_bp
    from backend.routes.auth      import auth_bp

    app.register_blueprint(boutique_bp)
    app.register_blueprint(commande_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # --- Créer le compte admin au premier lancement ------------
    with app.app_context():
        if Admin.query.count() == 0:
            admin = Admin(username=config.ADMIN_USERNAME)
            admin.set_password(config.ADMIN_PASSWORD)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Compte admin créé : {config.ADMIN_USERNAME}")

    return app


# --- Lancement -------------------------------------------------
if __name__ == "__main__":
    app = creer_app()

    print("=" * 50)
    print("🌸  IKLILOUNE — La Maison du Chic")
    print("=" * 50)
    print(f"🔗  Boutique → http://localhost:{config.PORT}")
    print(f"⚙️   Admin   → http://localhost:{config.PORT}/admin")
    print(f"🔑  Login   → http://localhost:{config.PORT}/admin/login")
    print("=" * 50)

    app.run(debug=config.DEBUG, host="0.0.0.0", port=config.PORT)
