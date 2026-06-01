# =============================================================
# routes/boutique.py — Pages et API publiques du site client
# =============================================================

from flask import Blueprint, render_template, jsonify, request
from backend.database import db
from backend.models.produit  import Produit
from backend.models.commande import Commande, HistoriqueStatut
from backend.models.banniere import Banniere

boutique_bp = Blueprint("boutique", __name__)


@boutique_bp.route("/")
def accueil():
    """Page d'accueil — catalogue principal."""
    return render_template("boutique/index.html")


@boutique_bp.route("/suivi")
def page_suivi():
    """Page de suivi de commande."""
    return render_template("boutique/suivi.html")


# ── API Produits ───────────────────────────────────────────────

@boutique_bp.route("/api/produits")
def api_produits():
    """
    API JSON — liste des produits avec filtres optionnels.

    Paramètres URL :
        ?categorie=parfum|sac|chaussure|vetement|accessoire
        ?genre=femme|homme|mixte
        ?promo=true
        ?q=mot_cle  (recherche par nom)
        ?tri=prix-asc|prix-desc|nouveau|populaire

    Retourne :
        {"produits": [...], "total": N}
    """
    requete = Produit.query.filter_by(actif=True)

    # Filtre catégorie
    categorie = request.args.get("categorie")
    if categorie and categorie not in ("tous", ""):
        if categorie == "promo":
            requete = requete.filter(Produit.prix_promo.isnot(None))
        elif categorie == "best_seller":
            requete = requete.filter(Produit.badge == "best_seller")
        elif categorie == "nouveau":
            requete = requete.filter(Produit.badge == "nouveau")
        else:
            requete = requete.filter(Produit.categorie == categorie)

    # Filtre genre (collection)
    genre = request.args.get("genre")
    if genre and genre not in ("tous", ""):
        if genre == "femme":
            requete = requete.filter(Produit.genre.in_(["femme", "mixte"]))
        elif genre == "homme":
            requete = requete.filter(Produit.genre.in_(["homme", "mixte"]))
        else:
            requete = requete.filter(Produit.genre == genre)

    # Recherche textuelle
    q = request.args.get("q", "").strip()
    if q:
        requete = requete.filter(Produit.nom.ilike(f"%{q}%"))

    # Tri
    tri = request.args.get("tri", "")
    if tri == "prix-asc":
        requete = requete.order_by(Produit.prix.asc())
    elif tri == "prix-desc":
        requete = requete.order_by(Produit.prix.desc())
    elif tri == "populaire":
        requete = requete.order_by(Produit.nb_consultations.desc())
    else:
        requete = requete.order_by(Produit.cree_le.desc())

    produits = requete.all()

    return jsonify({
        "produits": [p.vers_dict() for p in produits],
        "total"   : len(produits)
    })


@boutique_bp.route("/api/produits/<int:pid>")
def api_produit_detail(pid):
    """
    Retourne les détails d'un produit ET incrémente le compteur de vues.
    Le stock n'est jamais exposé — uniquement l'indicateur couleur.
    """
    produit = db.get_or_404(Produit, pid)

    # Incrémenter le compteur de consultations (statistiques)
    try:
        produit.nb_consultations += 1
        db.session.commit()
    except Exception:
        db.session.rollback()

    return jsonify(produit.vers_dict())


# ── API Bannières ──────────────────────────────────────────────

@boutique_bp.route("/api/bannieres")
def api_bannieres():
    """
    Retourne les bannières actives et visibles maintenant.
    Triées par ordre d'affichage défini dans l'admin.
    """
    bannieres = (Banniere.query
                 .filter_by(actif=True)
                 .order_by(Banniere.ordre.asc())
                 .all())
    visibles = [b.vers_dict() for b in bannieres if b.est_visible()]
    return jsonify({"bannieres": visibles})


# ── API Suivi commande ─────────────────────────────────────────

@boutique_bp.route("/api/commandes/suivi")
def api_suivi_commande():
    """
    Permet à un client de suivre sa commande.
    Accessible sans authentification — vérifié par numéro + téléphone.

    Paramètres URL :
        ?numero=IK047-20260601
        ?telephone=0748956959

    Retourne :
        {"commande": {..., "historique": [...]}}
    """
    numero    = request.args.get("numero", "").strip().upper()
    telephone = request.args.get("telephone", "").strip()

    if not numero or not telephone:
        return jsonify({"erreur": "Numéro de commande et téléphone requis"}), 400

    commande = Commande.query.filter_by(numero=numero).first()

    if not commande:
        return jsonify({"erreur": "Commande introuvable. Vérifiez le numéro."}), 404

    # Vérification sécurité : le téléphone doit correspondre
    tel_nettoye = telephone.replace(" ", "").replace("+", "").replace("-", "")
    tel_cmd     = commande.client_telephone.replace(" ", "").replace("+", "").replace("-", "")
    # Comparer les 8 derniers chiffres (flexible)
    if tel_nettoye[-8:] != tel_cmd[-8:]:
        return jsonify({"erreur": "Téléphone incorrect pour cette commande."}), 403

    # Récupérer l'historique des statuts
    historique = [h.vers_dict() for h in commande.historique]

    data = commande.vers_dict()
    data["historique"] = historique

    return jsonify({"commande": data})
