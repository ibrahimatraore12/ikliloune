# =============================================================
# routes/commande.py — Workflow de commande client
# =============================================================
# Flux :
#   1. Client remplit le formulaire (panier côté JS)
#   2. POST /api/commande → enregistrement BDD + numéro IK###
#   3. Réponse JSON → JS ouvre WhatsApp avec récapitulatif
# =============================================================

import json
from flask import Blueprint, request, jsonify
from backend.database import db
from backend.models.commande import Commande
from backend.models.client   import Client
from backend.services.commande_service import formater_message_whatsapp
from backend.utils.erreurs import (
    message_convivial, valider_champs, nettoyer_int, nettoyer_telephone
)

commande_bp = Blueprint("commande", __name__)


# ── Validation des champs obligatoires ─────────────────────────
CHAMPS_REQUIS = ["client_nom", "client_telephone", "articles"]


@commande_bp.route("/api/commande", methods=["POST"])
def passer_commande():
    """
    Enregistre une commande en base de données.

    Payload JSON attendu :
        client_nom        (str, requis)
        client_telephone  (str, requis)
        client_email      (str, optionnel)
        client_adresse    (str, optionnel)
        articles          (list, requis — au moins 1 article)
        sous_total        (int, FCFA)
        total             (int, FCFA après remise)
        remise            (int, montant remise en FCFA)
        paiement          (str — "orange" | "momo" | "wave")
        canal             (str — "site_web" par défaut)

    Retourne :
        { succes, numero, url_whatsapp }
    """
    # ── 1. Récupérer et vérifier le JSON ──────────────────────
    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "erreur": "Aucune donnée reçue. Vérifiez votre connexion et réessayez."
        }), 400

    # ── 2. Champs obligatoires ─────────────────────────────────
    err = valider_champs(data, ["client_nom", "client_telephone"])
    if err:
        return jsonify({"erreur": err}), 400

    # Nom : minimum 2 caractères
    nom = data["client_nom"].strip()
    if len(nom) < 2:
        return jsonify({
            "erreur": "Le nom doit contenir au moins 2 caractères."
        }), 400

    # Téléphone : normalisation +225
    try:
        telephone = nettoyer_telephone(data["client_telephone"])
    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400

    # Panier non vide
    articles = data.get("articles", [])
    if not articles or len(articles) == 0:
        return jsonify({
            "erreur": "Votre panier est vide. Ajoutez au moins un article avant de commander."
        }), 400

    # ── 2b. Mode de livraison ─────────────────────────────────
    ZONES = {
        "zone_1": {"label": "Songon / Yopougon",       "frais": 1500},
        "zone_2": {"label": "Abidjan Centre",           "frais": 2500},
        "zone_3": {"label": "Banlieue / Hors Abidjan", "frais": 3500},
    }
    mode_livraison = data.get("mode_livraison", "click_collect")
    if mode_livraison not in ("click_collect", "livraison"):
        mode_livraison = "click_collect"
    zone_livraison  = None
    frais_livraison = 0
    if mode_livraison == "livraison":
        zone_livraison = data.get("zone_livraison", "zone_1")
        if zone_livraison not in ZONES:
            zone_livraison = "zone_1"
        frais_livraison = ZONES[zone_livraison]["frais"]
    adresse_livraison = (data.get("adresse_livraison") or "").strip()

    # ── 2b. Mode de livraison ─────────────────────────────────
    ZONES = {
        "zone_1": {"label": "Songon / Yopougon",       "frais": 1500},
        "zone_2": {"label": "Abidjan Centre",           "frais": 2500},
        "zone_3": {"label": "Banlieue / Hors Abidjan", "frais": 3500},
    }
    mode_livraison = data.get("mode_livraison", "click_collect")
    if mode_livraison not in ("click_collect", "livraison"):
        mode_livraison = "click_collect"
    zone_livraison  = None
    frais_livraison = 0
    if mode_livraison == "livraison":
        zone_livraison = data.get("zone_livraison", "zone_1")
        if zone_livraison not in ZONES:
            zone_livraison = "zone_1"
        frais_livraison = ZONES[zone_livraison]["frais"]
    adresse_livraison = (data.get("adresse_livraison") or "").strip()

    # ── 3. Conversion sécurisée des montants ──────────────────
    try:
        sous_total      = nettoyer_int(data.get("sous_total") or data.get("total"), 0, "sous-total")
        remise_montant  = nettoyer_int(data.get("remise"),    0, "remise")
        total           = nettoyer_int(data.get("total"),     0, "total")
    except ValueError as e:
        return jsonify({"erreur": str(e)}), 400

    # Ajouter frais de livraison au total
    total = total + frais_livraison

    # Ajouter frais de livraison au total
    total = total + frais_livraison

    # Cohérence : total doit être >= 0
    if total < 0:
        return jsonify({
            "erreur": "Le montant total ne peut pas être négatif."
        }), 400

    # ── 4. Créer la commande en base ──────────────────────────
    try:
        # Séparer prénom / nom si format "Prénom Nom"
        mots = nom.split()
        prenom = mots[0] if len(mots) >= 2 else ""
        nom_famille = " ".join(mots[1:]) if len(mots) >= 2 else nom

        commande = Commande(
            # numero généré automatiquement par _generer_numero()
            client_nom       = nom,
            client_prenom    = data.get("client_prenom", prenom).strip(),
            client_telephone = telephone,
            client_adresse   = (data.get("client_adresse") or "").strip(),
            articles_json    = json.dumps(articles, ensure_ascii=False),
            sous_total       = sous_total,
            remise_montant   = remise_montant,
            total            = total,
            mode_paiement    = data.get("paiement", "") or data.get("mode_paiement", ""),
            canal            = data.get("canal", "site_web"),
            mode_livraison   = mode_livraison,
            zone_livraison   = zone_livraison,
            frais_livraison  = frais_livraison,
            adresse_livraison= adresse_livraison,
            statut           = "recue"
        )
        db.session.add(commande)

        # ── 5. Registre client (optionnel) ─────────────────────
        email = (data.get("client_email") or "").strip().lower()
        if email:
            client = Client.query.filter_by(email=email).first()
            if client:
                # Client connu : incrémenter ses commandes
                client.nb_commandes  = (client.nb_commandes or 0) + 1
                client.telephone     = telephone   # mettre à jour si changé
            else:
                # Nouveau client : l'enregistrer
                client = Client(
                    prenom       = prenom or nom,
                    nom          = nom_famille,
                    email        = email,
                    telephone    = telephone,
                    source       = "commande_site",
                    nb_commandes = 1
                )
                db.session.add(client)

        db.session.commit()

        # ── 6. URL WhatsApp de confirmation ───────────────────
        url_wa = formater_message_whatsapp(commande)

        print(f"✅ Commande enregistrée : {commande.numero} — {nom} — {total} FCFA")
        return jsonify({
            "succes"       : True,
            "numero"       : commande.numero,
            "url_whatsapp" : url_wa
        })

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur commande : {e}")
        return jsonify({"erreur": message_convivial(e)}), 500


@commande_bp.route("/api/verifier-promo", methods=["POST"])
def verifier_code_promo():
    """
    Vérifie un code promo saisi par le client en temps réel.

    Payload : { "code": "IKLI5" }
    Réponse : { valide, reduction_pct, message }
    """
    from backend.models.code_promo import CodePromo

    data = request.get_json(silent=True) or {}
    code_str = (data.get("code") or "").strip().upper()

    if not code_str:
        return jsonify({
            "valide"  : False,
            "message" : "Veuillez saisir un code promo."
        }), 400

    if len(code_str) > 20:
        return jsonify({
            "valide"  : False,
            "message" : "Ce code promo est trop long."
        }), 400

    # ── Codes fixes intégrés (toujours actifs) ─────────────────
    codes_fixes = {
        "IKLI5"     : 5,
        "BIENVENUE" : 5,
    }
    if code_str in codes_fixes:
        pct = codes_fixes[code_str]
        return jsonify({
            "valide"        : True,
            "reduction_pct" : pct,
            "message"       : f"✅ Code valide ! -{pct}% appliqué sur votre commande."
        })

    # ── Recherche en base de données ───────────────────────────
    try:
        code = CodePromo.query.filter_by(code=code_str).first()
    except Exception as e:
        return jsonify({
            "valide"  : False,
            "message" : "Impossible de vérifier le code pour l'instant. Réessayez."
        }), 500

    if not code:
        return jsonify({
            "valide"  : False,
            "message" : "❌ Ce code promo n'existe pas ou a expiré."
        })

    valide, msg = code.est_valide()
    if not valide:
        # Traduire les messages techniques éventuels
        msg_propre = msg or "Ce code n'est plus valide."
        return jsonify({
            "valide"  : False,
            "message" : f"❌ {msg_propre}"
        })

    return jsonify({
        "valide"        : True,
        "reduction_pct" : code.reduction_pct,
        "message"       : f"✅ -{code.reduction_pct}% appliqué — {code.description or 'Code valide !'}"
    })
