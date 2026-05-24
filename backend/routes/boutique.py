# =============================================================
# routes/boutique.py — Pages et API du site client
# =============================================================

from flask import Blueprint, render_template, jsonify, request
from backend.database import db
from backend.models.produit import Produit

boutique_bp = Blueprint("boutique", __name__)


@boutique_bp.route("/")
def accueil():
    """Page d'accueil — sert le fichier HTML principal."""
    return render_template("boutique/index.html")


@boutique_bp.route("/api/produits")
def api_produits():
    """
    API JSON — liste des produits avec filtres optionnels.

    Paramètres URL :
        ?categorie=parfum
        ?genre=femme
        ?promo=true
        ?q=rose  (recherche par nom)

    Retourne :
        JSON : {"produits": [...], "total": N}
    """
    requete = Produit.query.filter_by(actif=True)

    categorie = request.args.get("categorie")
    if categorie and categorie != "tous":
        if categorie == "promo":
            requete = requete.filter(Produit.badge == "promo")
        else:
            requete = requete.filter(Produit.categorie == categorie)

    genre = request.args.get("genre")
    if genre and genre != "tous":
        requete = requete.filter(Produit.genre == genre)

    q = request.args.get("q")
    if q:
        requete = requete.filter(Produit.nom.ilike(f"%{q}%"))

    produits = requete.order_by(Produit.cree_le.desc()).all()

    return jsonify({
        "produits": [p.vers_dict() for p in produits],
        "total"   : len(produits)
    })


@boutique_bp.route("/api/produit/<int:pid>")
def api_produit(pid):
    """Retourne les détails d'un produit."""
    p = db.get_or_404(Produit, pid)
    return jsonify(p.vers_dict())
