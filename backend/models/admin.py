# =============================================================
# models/admin.py — Compte administrateur du site
# Accès exclusif et privé au dashboard
# =============================================================

from datetime import datetime
from backend.database import db
from flask_login import UserMixin
import bcrypt


class Admin(db.Model, UserMixin):
    """
    Le responsable du site — seul utilisateur du dashboard admin.
    UserMixin ajoute les méthodes requises par Flask-Login
    (is_authenticated, is_active, get_id).
    """

    __tablename__ = "admins"

    id              = db.Column(db.Integer, primary_key=True)
    username        = db.Column(db.String(80), unique=True, nullable=False)

    # Mot de passe hashé avec bcrypt — jamais stocké en clair
    password_hash   = db.Column(db.String(200), nullable=False)

    # Dernière connexion (pour le suivi de sécurité)
    derniere_connexion = db.Column(db.DateTime, nullable=True)
    cree_le            = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, mot_de_passe):
        """
        Hashe et stocke le mot de passe.
        bcrypt ajoute automatiquement un sel aléatoire.

        Exemple :
            admin.set_password("MonMotDePasse2025!")
        """
        # encode() = convertir la chaîne en bytes (requis par bcrypt)
        hash_bytes = bcrypt.hashpw(
            mot_de_passe.encode("utf-8"),
            bcrypt.gensalt()           # sel aléatoire unique
        )
        # decode() = reconvertir en chaîne pour stocker en base
        self.password_hash = hash_bytes.decode("utf-8")

    def verifier_password(self, mot_de_passe):
        """
        Vérifie si le mot de passe saisi correspond au hash stocké.

        Retourne True si correct, False sinon.
        """
        return bcrypt.checkpw(
            mot_de_passe.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )

    def get_id(self):
        """Requis par Flask-Login — retourne l'ID comme chaîne."""
        return str(self.id)

    def __repr__(self):
        return f"<Admin #{self.id} | {self.username}>"
