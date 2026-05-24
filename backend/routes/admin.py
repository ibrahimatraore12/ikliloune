# =============================================================
# routes/admin.py — Dashboard privé — accès restreint
# Toutes les routes sont protégées par @login_required
# =============================================================

import os, json
from flask import (Blueprint, render_template, request,
                   jsonify, redirect, url_for)
from flask_login import login_required
from backend.database import db
from backend.models.produit  import Produit
from backend.models.commande import Commande
from backend.models.client   import Client
from backend.services.image_service  import traiter_image, supprimer_image
from backend.services.stats_service  import (
    graphique_ventes_mensuelles, graphique_categories
)
from backend import config

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required          # redirige vers /admin/login si non connecté
def tableau_de_bord():
    """Dashboard principal — KPIs et graphiques."""
    kpis = {
        "nb_produits"  : Produit.query.filter_by(actif=True).count(),
        "nb_commandes" : Commande.query.count(),
        "nb_clients"   : Client.query.count(),
        "ruptures"     : Produit.query.filter_by(actif=True)
                                      .filter(Produit.stock == 0).count(),
    }
    graphique_v = graphique_ventes_mensuelles()
    graphique_c = graphique_categories()

    return render_template("admin/dashboard.html",
                           kpis=kpis,
                           graphique_ventes=graphique_v,
                           graphique_cats=graphique_c)


# --- Produits --------------------------------------------------

@admin_bp.route("/admin/api/produits")
@login_required
def api_produits_admin():
    """Liste tous les produits (actifs + inactifs)."""
    produits = Produit.query.order_by(Produit.cree_le.desc()).all()
    return jsonify([p.vers_dict() for p in produits])


@admin_bp.route("/admin/api/produit/ajouter", methods=["POST"])
@login_required
def ajouter_produit():
    """Ajoute un nouvel article avec sa photo."""
    try:
        nom       = request.form.get("nom", "").strip()
        categorie = request.form.get("categorie", "").strip()
        prix      = int(request.form.get("prix", 0))
        stock     = int(request.form.get("stock", 0))

        if not nom or not categorie or prix <= 0:
            return jsonify({"erreur": "Nom, catégorie et prix obligatoires"}), 400

        prix_promo_val = request.form.get("prix_promo")

        produit = Produit(
            nom            = nom,
            categorie      = categorie,
            genre          = request.form.get("genre", "mixte"),
            prix           = prix,
            prix_promo     = int(prix_promo_val) if prix_promo_val else None,
            stock          = stock,
            description    = request.form.get("description", ""),
            badge          = request.form.get("badge", ""),
            couleurs_json  = request.form.get("couleurs", "[]"),
            tailles_json   = request.form.get("tailles", "[]"),
            attributs_json = request.form.get("attributs", "{}"),
        )
        db.session.add(produit)
        db.session.commit()  # obtenir l'ID avant de traiter la photo

        # Traiter la photo si fournie
        photo = request.files.get("photo")
        if photo and photo.filename:
            ext = photo.filename.rsplit(".", 1)[-1].lower()
            if ext not in config.FORMATS_ACCEPTES:
                return jsonify({"erreur": f"Format non accepté : {ext}"}), 400

            os.makedirs(config.DOSSIER_TEMP, exist_ok=True)
            chemin_temp = os.path.join(config.DOSSIER_TEMP,
                                       f"tmp_{produit.id}.{ext}")
            photo.save(chemin_temp)

            nom_webp = traiter_image(chemin_temp, f"produit_{produit.id}")
            if os.path.exists(chemin_temp):
                os.remove(chemin_temp)

            if nom_webp:
                produit.photo = nom_webp
                db.session.commit()

        return jsonify({"succes": True, "produit": produit.vers_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/produit/modifier/<int:pid>", methods=["POST"])
@login_required
def modifier_produit(pid):
    """Modifie un article existant."""
    produit = db.get_or_404(Produit, pid)
    try:
        produit.nom            = request.form.get("nom", produit.nom).strip()
        produit.categorie      = request.form.get("categorie", produit.categorie)
        produit.genre          = request.form.get("genre", produit.genre)
        produit.prix           = int(request.form.get("prix", produit.prix))
        produit.stock          = int(request.form.get("stock", produit.stock))
        produit.description    = request.form.get("description", produit.description)
        produit.badge          = request.form.get("badge", produit.badge)
        produit.couleurs_json  = request.form.get("couleurs", produit.couleurs_json)
        produit.tailles_json   = request.form.get("tailles", produit.tailles_json)
        produit.attributs_json = request.form.get("attributs", produit.attributs_json)

        pp = request.form.get("prix_promo")
        produit.prix_promo = int(pp) if pp else None

        # Nouvelle photo ?
        photo = request.files.get("photo")
        if photo and photo.filename:
            if produit.photo:
                supprimer_image(produit.photo)
            ext = photo.filename.rsplit(".", 1)[-1].lower()
            chemin_temp = os.path.join(config.DOSSIER_TEMP,
                                       f"tmp_{produit.id}.{ext}")
            photo.save(chemin_temp)
            nom_webp = traiter_image(chemin_temp, f"produit_{produit.id}")
            if os.path.exists(chemin_temp):
                os.remove(chemin_temp)
            if nom_webp:
                produit.photo = nom_webp

        db.session.commit()
        return jsonify({"succes": True, "produit": produit.vers_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/produit/supprimer/<int:pid>", methods=["DELETE"])
@login_required
def supprimer_produit(pid):
    """Désactive un article (ne supprime pas de la DB)."""
    produit = db.get_or_404(Produit, pid)
    produit.actif = False
    db.session.commit()
    return jsonify({"succes": True, "message": f"'{produit.nom}' retiré"})


# --- Commandes -------------------------------------------------

@admin_bp.route("/admin/api/commandes")
@login_required
def api_commandes():
    """Liste toutes les commandes, de la plus récente à la plus ancienne."""
    commandes = Commande.query.order_by(Commande.cree_le.desc()).all()
    return jsonify([c.vers_dict() for c in commandes])


@admin_bp.route("/admin/api/commande/statut/<int:cid>", methods=["POST"])
@login_required
def modifier_statut_commande(cid):
    """Met à jour le statut d'une commande."""
    commande = db.get_or_404(Commande, cid)
    data = request.get_json()
    statuts_valides = ["en_attente", "confirmee",
                       "en_preparation", "livree", "annulee"]
    nouveau = data.get("statut", "")
    if nouveau not in statuts_valides:
        return jsonify({"erreur": "Statut invalide"}), 400
    commande.statut = nouveau
    commande.notes_admin = data.get("notes", commande.notes_admin)
    db.session.commit()
    return jsonify({"succes": True, "commande": commande.vers_dict()})


# --- Clients ---------------------------------------------------

@admin_bp.route("/admin/api/clients")
@login_required
def api_clients():
    """Liste tous les clients enregistrés."""
    clients = Client.query.order_by(Client.cree_le.desc()).all()
    return jsonify([c.vers_dict() for c in clients])


@admin_bp.route("/admin/api/clients/export")
@login_required
def exporter_clients():
    """Exporte le registre clients en CSV."""
    import csv, io
    from flask import Response

    clients = Client.query.filter_by(actif=True).all()
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "prenom", "nom", "email",
        "telephone", "interet", "source", "nb_commandes", "cree_le"
    ])
    writer.writeheader()
    for c in clients:
        writer.writerow(c.vers_dict())

    return Response(
        "\ufeff" + output.getvalue(),   # BOM UTF-8 pour Excel
        mimetype="text/csv",
        headers={"Content-Disposition":
                 "attachment; filename=clients_ikliloune.csv"}
    )


# --- Leads (pop-up -5%) ----------------------------------------

@admin_bp.route("/api/lead", methods=["POST"])
def enregistrer_lead():
    """
    Enregistre un prospect depuis le pop-up -5%.
    Route publique (pas de @login_required).
    """
    try:
        data = request.get_json()
        email = data.get("email", "").strip()
        if not email:
            return jsonify({"erreur": "Email obligatoire"}), 400

        # Ne pas créer de doublon
        if Client.query.filter_by(email=email).first():
            return jsonify({"succes": True, "code": "IKLI5",
                            "message": "Déjà inscrit !"})

        client = Client(
            prenom      = data.get("prenom", "").strip(),
            nom         = data.get("nom", "").strip(),
            email       = email,
            telephone   = data.get("telephone", "").strip(),
            interet     = data.get("interet", ""),
            source      = "popup",
            code_promo  = "IKLI5",
            consentement = True
        )
        db.session.add(client)
        db.session.commit()

        return jsonify({"succes": True, "code": "IKLI5"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/client/ajouter", methods=["POST"])
@login_required
def ajouter_client_manuel():
    """
    Ajoute un client manuellement depuis l'admin.
    Pour les clients reçus par téléphone, WhatsApp ou en boutique.
    """
    try:
        data = request.get_json()

        email = data.get("email", "").strip()

        # Vérifier doublon si email fourni
        if email and Client.query.filter_by(email=email).first():
            return jsonify({"erreur": "Email déjà enregistré"}), 400

        # Email fictif si non fourni (clients sans email)
        if not email:
            import time
            email = f"client_{int(time.time())}@sans-email.ikliloune"

        client = Client(
            prenom       = data.get("prenom", "").strip(),
            nom          = data.get("nom", "").strip(),
            email        = email,
            telephone    = data.get("telephone", "").strip(),
            interet      = data.get("interet", "tout"),
            source       = "manuel",   # saisie manuelle par l'admin
            nb_commandes = int(data.get("nb_commandes", 0)),
            consentement = True,
            actif        = True
        )
        db.session.add(client)
        db.session.commit()

        print(f"✅ Client ajouté manuellement : {client.prenom} {client.nom}")
        return jsonify({"succes": True, "client": client.vers_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/client/modifier/<int:cid>", methods=["POST"])
@login_required
def modifier_client(cid):
    """Met à jour les infos d'un client."""
    client = db.get_or_404(Client, cid)
    try:
        data = request.get_json()
        client.prenom      = data.get("prenom", client.prenom)
        client.nom         = data.get("nom", client.nom)
        client.telephone   = data.get("telephone", client.telephone)
        client.interet     = data.get("interet", client.interet)
        client.nb_commandes = int(data.get("nb_commandes", client.nb_commandes))
        client.actif       = data.get("actif", client.actif)
        db.session.commit()
        return jsonify({"succes": True, "client": client.vers_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


# ── Codes Promo ────────────────────────────────────────────────

@admin_bp.route("/admin/api/codes-promo")
@login_required
def api_codes_promo():
    """Liste tous les codes promo."""
    from backend.models.code_promo import CodePromo
    codes = CodePromo.query.order_by(CodePromo.cree_le.desc()).all()
    return jsonify([c.vers_dict() for c in codes])


@admin_bp.route("/admin/api/code-promo/creer", methods=["POST"])
@login_required
def creer_code_promo():
    """Crée un nouveau code promo."""
    from backend.models.code_promo import CodePromo
    from datetime import datetime
    try:
        data = request.get_json()
        code_str = data.get("code", "").strip().upper()

        if not code_str:
            return jsonify({"erreur": "Code obligatoire"}), 400

        if CodePromo.query.filter_by(code=code_str).first():
            return jsonify({"erreur": "Ce code existe déjà"}), 400

        # Parser la date d'expiration si fournie
        expire = None
        if data.get("expire_le"):
            try:
                expire = datetime.strptime(data["expire_le"], "%Y-%m-%d")
            except:
                pass

        code = CodePromo(
            code             = code_str,
            description      = data.get("description", ""),
            reduction_pct    = int(data.get("reduction_pct", 5)),
            max_utilisations = int(data["max_utilisations"]) if data.get("max_utilisations") else None,
            expire_le        = expire,
            actif            = True
        )
        db.session.add(code)
        db.session.commit()

        print(f"✅ Code promo créé : {code.code} (-{code.reduction_pct}%)")
        return jsonify({"succes": True, "code": code.vers_dict()})

    except Exception as e:
        db.session.rollback()
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/code-promo/desactiver/<int:cid>", methods=["POST"])
@login_required
def desactiver_code_promo(cid):
    """Désactive un code promo."""
    from backend.models.code_promo import CodePromo
    code = db.get_or_404(CodePromo, cid)
    code.actif = False
    db.session.commit()
    return jsonify({"succes": True})
