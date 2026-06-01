# =============================================================
# models/admin.py — Compte administrateur / responsable vente
# =============================================================

from datetime import datetime
from flask_login import UserMixin
from backend.database import db
import bcrypt


class Admin(UserMixin, db.Model):
    """Compte admin — accès au dashboard de gestion."""

    __tablename__ = "admins"

    id                  = db.Column(db.Integer, primary_key=True)
    username            = db.Column(db.String(80), unique=True, nullable=False)
    email               = db.Column(db.String(120), unique=True, nullable=True)
    password_hash       = db.Column(db.String(255), nullable=False)

    # Anti brute-force
    tentatives_echec    = db.Column(db.Integer, nullable=False, default=0)
    bloque_jusqu        = db.Column(db.DateTime, nullable=True)

    derniere_connexion  = db.Column(db.DateTime, nullable=True)
    actif               = db.Column(db.Boolean, nullable=False, default=True)
    cree_le             = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, mot_de_passe):
        """
        Hash le mot de passe avec bcrypt (coût 12) et le stocke.
        Ne jamais stocker un mot de passe en clair.
        """
        self.password_hash = bcrypt.hashpw(
            mot_de_passe.encode("utf-8"),
            bcrypt.gensalt(rounds=12)
        ).decode("utf-8")

    def verifier_password(self, mot_de_passe):
        """
        Vérifie si le mot de passe fourni correspond au hash stocké.

        Retourne :
            bool : True si correct, False sinon
        """
        try:
            return bcrypt.checkpw(
                mot_de_passe.encode("utf-8"),
                self.password_hash.encode("utf-8")
            )
        except Exception:
            return False

    def __repr__(self):
        return f"<Admin #{self.id} | {self.username}>"
