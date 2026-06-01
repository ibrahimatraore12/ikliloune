# =============================================================
# models/banniere.py — Bannières homepage gérées par l'admin
# =============================================================

from datetime import datetime
from backend.database import db


class Banniere(db.Model):
    """
    Une bannière affichée dans le carrousel de la homepage.
    Créée, modifiée et désactivée depuis le dashboard admin.
    """

    __tablename__ = "bannieres"

    id           = db.Column(db.Integer, primary_key=True)
    titre        = db.Column(db.String(100), nullable=False)
    sous_titre   = db.Column(db.String(200), nullable=True)
    texte_bouton = db.Column(db.String(50),  nullable=True, default="Découvrir →")
    lien_bouton  = db.Column(db.String(255), nullable=True)  # URL ou filtre

    # Collection ciblée : "perles" | "corail" | "toutes" | "promo"
    collection   = db.Column(db.String(20), nullable=False, default="toutes")

    # Emoji ou icône décorative (affiché en grand en fond)
    deco_emoji   = db.Column(db.String(10), nullable=True)

    # Style de fond : "clair" | "sombre" | "promo"
    style        = db.Column(db.String(20), nullable=False, default="clair")

    # Photo de fond (WebP, optionnelle)
    image        = db.Column(db.String(200), nullable=True)

    # Ordre d'affichage dans le carrousel (0 = premier)
    ordre        = db.Column(db.Integer, nullable=False, default=0)

    # Planification (None = permanente)
    date_debut   = db.Column(db.DateTime, nullable=True)
    date_fin     = db.Column(db.DateTime, nullable=True)

    # Soft delete
    actif        = db.Column(db.Boolean, nullable=False, default=True)

    cree_le      = db.Column(db.DateTime, default=datetime.utcnow)
    modifie_le   = db.Column(db.DateTime, default=datetime.utcnow,
                             onupdate=datetime.utcnow)

    def est_visible(self):
        """
        Vérifie si la bannière doit être affichée maintenant.
        Prend en compte : actif + dates de diffusion.
        """
        if not self.actif:
            return False
        maintenant = datetime.utcnow()
        if self.date_debut and maintenant < self.date_debut:
            return False
        if self.date_fin and maintenant > self.date_fin:
            return False
        return True

    def vers_dict(self):
        """Convertit en dict pour l'API JSON et les templates."""
        return {
            "id"           : self.id,
            "titre"        : self.titre,
            "sous_titre"   : self.sous_titre or "",
            "texte_bouton" : self.texte_bouton or "Découvrir →",
            "lien_bouton"  : self.lien_bouton or "#catalogue",
            "collection"   : self.collection,
            "deco_emoji"   : self.deco_emoji or "",
            "style"        : self.style,
            "image"        : self.image or "",
            "ordre"        : self.ordre,
            "date_debut"   : self.date_debut.strftime("%Y-%m-%d") if self.date_debut else "",
            "date_fin"     : self.date_fin.strftime("%Y-%m-%d")   if self.date_fin   else "",
            "est_visible"  : self.est_visible(),
            "actif"        : self.actif,
            "cree_le"      : self.cree_le.strftime("%d/%m/%Y"),
        }

    def __repr__(self):
        return f"<Banniere #{self.id} | {self.titre} | {'✅' if self.actif else '❌'}>"
