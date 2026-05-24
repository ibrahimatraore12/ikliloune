# =============================================================
# routes/auth.py — Connexion / déconnexion de l'admin
# =============================================================

from flask import (Blueprint, render_template, request,
                   redirect, url_for, flash)
from flask_login import login_user, logout_user, login_required
from backend.database import db
from backend.models.admin import Admin
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/ik-gestion-2025-prive", methods=["GET", "POST"])
def login():
    """Page de connexion admin."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()

        if admin and admin.verifier_password(password):
            login_user(admin, remember=False)
            admin.derniere_connexion = datetime.utcnow()
            db.session.commit()
            print(f"✅ Admin connecté : {username}")
            return redirect(url_for("admin.tableau_de_bord"))

        print(f"❌ Echec login : {username}")
        flash("Identifiants incorrects.", "erreur")

    return render_template("admin/login.html")


@auth_bp.route("/ik-gestion-logout")
@login_required
def logout():
    """Déconnecte l'admin."""
    logout_user()
    return redirect(url_for("auth.login"))
