# =============================================================
# routes/commande.py — Workflow de commande client
# =============================================================

import json
from flask import Blueprint, request, jsonify
from backend.database import db
from backend.models.commande import Commande
from backend.models.client   import Client
from backend.services.commande_service import (
    generer_numero_commande,
    formater_message_whatsapp
)

commande_bp = Blueprint("commande", __name__)


@commande_bp.route("/api/commande", methods=["POST"])
def passer_commande():
    """
    Enregistre une commande en base de données.

    Reçoit (JSON) :
        client_nom, client_telephone, client_email,
        client_adresse, articles, total, paiement, remise

    Retourne :
        JSON : {succes, numero, url_whatsapp}
    """
    try:
        data = request.get_json()

        # Validation des champs obligatoires
        if not data.get("client_nom") or not data.get("client_telephone"):
            return jsonify({"erreur": "Nom et téléphone obligatoires"}), 400

        if not data.get("articles"):
            return jsonify({"erreur": "Panier vide"}), 400

        # Créer la commande
        commande = Commande(
            numero           = generer_numero_commande(),
            client_nom       = data["client_nom"].strip(),
            client_telephone = data["client_telephone"].strip(),
            client_email     = data.get("client_email", "").strip(),
            client_adresse   = data.get("client_adresse", "").strip(),
            articles_json    = json.dumps(data["articles"]),
            total            = int(data.get("total", 0)),
            remise           = int(data.get("remise", 0)),
            paiement         = data.get("paiement", ""),
            statut           = "en_attente"
        )

        db.session.add(commande)

        # Enregistrer ou mettre à jour le client dans le registre
        email = data.get("client_email", "").strip()
        if email:
            client = Client.query.filter_by(email=email).first()
            if client:
                client.nb_commandes += 1
            else:
                client = Client(
                    prenom       = data["client_nom"].split()[0],
                    nom          = " ".join(data["client_nom"].split()[1:]),
                    email        = email,
                    telephone    = data["client_telephone"],
                    source       = "commande",
                    nb_commandes = 1
                )
                db.session.add(client)

        db.session.commit()

        # Générer l'URL WhatsApp pour confirmation
        url_wa = formater_message_whatsapp(commande)

        print(f"✅ Commande enregistrée : {commande.numero}")
        return jsonify({
            "succes"        : True,
            "numero"        : commande.numero,
            "url_whatsapp"  : url_wa
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur commande : {e}")
        return jsonify({"erreur": str(e)}), 500
