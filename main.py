# =============================================================
# main.py — Point d'entrée de l'application IKLILOUNE
# Lance le serveur : python main.py
# =============================================================

from flask import Flask, jsonify
from flask_login import LoginManager
from backend import config
from backend.database import db, initialiser_db
from backend.models.admin import Admin


def creer_app():
    """
    Crée, configure et retourne l'application Flask.
    Pattern factory — séparée pour faciliter les tests.
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    # --- Configuration Flask -----------------------------------
    app.config["SECRET_KEY"]                     = config.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"]        = config.URL_DB
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"]             = config.TAILLE_MAX_UPLOAD
    # CSRF : False en dev local, True en production (via .env)
    app.config["WTF_CSRF_ENABLED"] = not config.DEBUG

    # --- Base de données ---------------------------------------
    initialiser_db(app)

    # --- Flask-Login -------------------------------------------
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view    = "auth.login"        # nom de la vue
    login_manager.login_message = "Connexion requise."
    # Surcharger l'URL de redirection avec l'URL secrète réelle
    app.config["LOGIN_DISABLED"] = False

    @login_manager.user_loader
    def charger_admin(admin_id):
        """Flask-Login appelle cette fonction à chaque requête protégée."""
        return db.session.get(Admin, int(admin_id))

    # --- Blueprints (routes) -----------------------------------
    from backend.routes.boutique import boutique_bp
    from backend.routes.commande import commande_bp
    from backend.routes.admin    import admin_bp
    from backend.routes.auth     import auth_bp

    app.register_blueprint(boutique_bp)
    app.register_blueprint(commande_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    # --- Route santé (health check Render.com) ----------------
    @app.route("/health")
    def health():
        """Vérifie que l'application est en ligne. Utilisée par Render.com."""
        return jsonify({"status": "ok", "app": "IKLILOUNE"}), 200

    # --- Bannières par défaut au premier lancement -----------
    with app.app_context():
    # Auto-créer les tables manquantes (dont historique_stock)
    from backend.models.historique_stock import HistoriqueStock  # noqa
    db.create_all()

        _init_donnees_defaut(app)

    return app


def _init_donnees_defaut(app):
    """
    Initialise les données par défaut au premier lancement :
    - Compte admin
    - Codes promo IKLI5 et BIENVENUE
    - Bannières de démonstration
    """
    from backend.models.admin      import Admin
    from backend.models.code_promo import CodePromo
    from backend.models.banniere   import Banniere

    # Compte admin
    if Admin.query.count() == 0:
        admin = Admin(username=config.ADMIN_USERNAME)
        admin.set_password(config.ADMIN_PASSWORD)
        db.session.add(admin)
        print(f"✅ Compte admin créé : {config.ADMIN_USERNAME}")

    # Codes promo par défaut
    for code_str, pct, desc, cond in [
        ("IKLI5",     5, "Bienvenue — 1ère commande",   "nouveaux_clients"),
        ("BIENVENUE", 5, "Code bienvenue permanent",     "nouveaux_clients"),
    ]:
        if not CodePromo.query.filter_by(code=code_str).first():
            db.session.add(CodePromo(
                code=code_str, description=desc,
                type_reduction="pourcentage", reduction_pct=pct,
                conditions=cond, actif=True
            ))
            print(f"✅ Code promo créé : {code_str}")

    # Bannières par défaut si aucune n'existe
    if Banniere.query.count() == 0:
        bannieres = [
            Banniere(titre="La Maison du Chic", sous_titre="Parfums · Sacs · Vêtements · Chaussures",
                     texte_bouton="Découvrir les Parfums →", lien_bouton="/#catalogue",
                     collection="perles", deco_emoji="🌸", style="clair", ordre=0),
            Banniere(titre="L'Élégance Masculine", sous_titre="Oud Prestige · Boubous brodés · Derbys raffinés",
                     texte_bouton="Voir la collection →", lien_bouton="/#catalogue",
                     collection="corail", deco_emoji="🪸", style="sombre", ordre=1),
            Banniere(titre="Jusqu'à -30%", sous_titre="Sur une sélection Perles & Corail. Livraison offerte.",
                     texte_bouton="Voir les promos →", lien_bouton="/#catalogue",
                     collection="promo", deco_emoji="🛍️", style="promo", ordre=2),
        ]
        for b in bannieres:
            db.session.add(b)
        print("✅ Bannières par défaut créées")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"⚠️  Init données : {e}")


# --- Lancement -------------------------------------------------
if __name__ == "__main__":
    app = creer_app()

    print("=" * 55)
    print("🌸  IKLILOUNE — La Maison du Chic")
    print("=" * 55)
    print(f"🔗  Boutique → http://localhost:{config.PORT}")
    print(f"⚙️   Admin   → http://localhost:{config.PORT}/{config.ADMIN_URL_SECRET}")
    print(f"🏥  Health  → http://localhost:{config.PORT}/health")
    print("=" * 55)

    app.run(debug=config.DEBUG, host="0.0.0.0", port=config.PORT)
