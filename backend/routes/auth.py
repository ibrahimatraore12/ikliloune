# =============================================================
# routes/auth.py — Connexion / déconnexion admin
# URL secrète — ne jamais exposer sur le site client
# =============================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from backend.database import db
from backend.models.admin import Admin
from backend import config
from datetime import datetime, timedelta

auth_bp = Blueprint("auth", __name__)

# Nombre de tentatives avant blocage
MAX_TENTATIVES = 5
DUREE_BLOCAGE  = timedelta(minutes=15)


@auth_bp.route(f"/{config.ADMIN_URL_SECRET}", methods=["GET", "POST"])
def login():
    """
    Page de connexion admin.
    URL secrète définie dans config.py — jamais /admin/login.
    """
    # Si déjà connecté → rediriger vers le dashboard
    if current_user.is_authenticated:
        return redirect(url_for("admin.tableau_de_bord"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        # Vérifier si le compte est bloqué
        if admin and admin.bloque_jusqu and datetime.utcnow() < admin.bloque_jusqu:
            minutes_restantes = int((admin.bloque_jusqu - datetime.utcnow()).seconds / 60) + 1
            flash(f"Compte temporairement bloqué. Réessayez dans {minutes_restantes} min.", "erreur")
            return render_template("admin/login.html")

        if admin and admin.verifier_password(password):
            # Connexion réussie — réinitialiser les tentatives
            admin.tentatives_echec   = 0
            admin.bloque_jusqu       = None
            admin.derniere_connexion = datetime.utcnow()
            db.session.commit()
            login_user(admin, remember=False)
            return redirect(url_for("admin.tableau_de_bord"))

        # Échec de connexion
        if admin:
            admin.tentatives_echec = (admin.tentatives_echec or 0) + 1
            if admin.tentatives_echec >= MAX_TENTATIVES:
                admin.bloque_jusqu = datetime.utcnow() + DUREE_BLOCAGE
                flash(f"Trop de tentatives. Compte bloqué {int(DUREE_BLOCAGE.seconds/60)} min.", "erreur")
            else:
                restantes = MAX_TENTATIVES - admin.tentatives_echec
                flash(f"Identifiants incorrects. {restantes} tentative(s) restante(s).", "erreur")
            db.session.commit()
        else:
            flash("Identifiants incorrects.", "erreur")

    return render_template("admin/login.html")


@auth_bp.route(f"/{config.ADMIN_URL_LOGOUT}")
@login_required
def deconnexion():
    """Déconnecte l'admin et redirige vers la page de login."""
    logout_user()
    return redirect(url_for("auth.login"))
