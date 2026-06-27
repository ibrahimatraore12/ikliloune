# =============================================================
# services/commande_service.py — Messages WhatsApp + workflow
# =============================================================

from urllib.parse import quote
from backend import config


# ── Labels des modes de paiement ──────────────────────────────
LABELS_PAIEMENT = {
    "orange"       : "🟠 Orange Money",
    "orange_money" : "🟠 Orange Money",
    "momo"         : "🟡 MTN MoMo",
    "mtn_momo"     : "🟡 MTN MoMo",
    "wave"         : "🔵 Wave",
    "whatsapp"     : "💬 WhatsApp",
    "a_definir"    : "À définir",
    ""             : "À définir",
}

# ── Labels des statuts de commande ────────────────────────────
LABELS_STATUT = {
    "recue"          : ("📬", "Commande reçue"),
    "confirmee"      : ("✅", "Commande confirmée"),
    "en_preparation" : ("🔄", "En cours de préparation"),
    "expediee"       : ("🚚", "Expédiée — en route !"),
    "livree"         : ("🎉", "Livrée avec succès"),
    "annulee"        : ("❌", "Annulée"),
}


def _formater_montant(montant: int) -> str:
    """Formate un montant FCFA avec espace comme séparateur des milliers."""
    return f"{montant:,} FCFA".replace(",", " ")


def _normaliser_telephone(tel: str) -> str:
    """
    Normalise un numéro pour l'URL wa.me.
    Supprime le + et s'assure que le code pays 225 est présent.
    """
    propre = tel.replace(" ", "").replace("+", "").replace("-", "")
    if not propre.startswith("225"):
        propre = "225" + propre.lstrip("0")
    return propre


def formater_message_whatsapp(commande) -> str:
    """
    Génère l'URL WhatsApp pré-remplie envoyée vers la boutique
    quand le client valide sa commande.

    Le message récapitule :
    - Le numéro de commande
    - Les articles commandés (nom, coloris, taille, quantité, prix)
    - Le sous-total, la remise éventuelle, le total
    - Les coordonnées du client
    - Le mode de paiement choisi

    Args:
        commande (Commande): objet commande validé et enregistré en BDD

    Returns:
        str: URL wa.me/{numero_boutique}?text=... prête à ouvrir
    """
    # ── Détail des articles ───────────────────────────────────
    lignes_articles = ""
    for article in commande.articles():
        nom    = article.get("nom", "Article")
        qty    = article.get("qty", article.get("qte", 1))
        prix   = article.get("prix_actuel", article.get("prix", 0))
        coloris = article.get("coloris", article.get("couleur", ""))
        taille  = article.get("taille", article.get("pointure", ""))
        sous_t  = qty * prix

        details = ""
        if coloris:
            details += f" · {coloris}"
        if taille:
            details += f" · Taille {taille}"

        lignes_articles += f"• {nom}{details} × {qty} = {_formater_montant(sous_t)}\n"

    if not lignes_articles.strip():
        lignes_articles = "• Articles commandés\n"

    # ── Remise ────────────────────────────────────────────────
    ligne_remise = ""
    if commande.remise_montant and commande.remise_montant > 0:
        code = getattr(commande, "code_promo_utilise", "") or ""
        suffix = f" ({code})" if code else ""
        ligne_remise = f"🎁 Remise{suffix} : -{_formater_montant(commande.remise_montant)}\n"

    # ── Paiement ──────────────────────────────────────────────
    mode_pmt = getattr(commande, "mode_paiement", "") or getattr(commande, "paiement", "") or ""
    paiement = LABELS_PAIEMENT.get(mode_pmt.lower(), mode_pmt or "À définir")

    # ── Adresse ───────────────────────────────────────────────
    # Livraison
    mode_liv    = getattr(commande, "mode_livraison",    "click_collect") or "click_collect"
    frais_liv   = getattr(commande, "frais_livraison",   0) or 0
    zone_liv    = getattr(commande, "zone_livraison",    "") or ""
    adresse_liv = (getattr(commande, "adresse_livraison", "") or "").strip()
    adresse_cli = (getattr(commande, "client_adresse",    "") or "").strip()
    adresse     = adresse_liv or adresse_cli or "À préciser"
    ZONES_LBL = {
        "zone_1": "Zone 1 — Songon / Yopougon",
        "zone_2": "Zone 2 — Abidjan Centre",
        "zone_3": "Zone 3 — Banlieue / Hors Abidjan",
    }
    if mode_liv == "click_collect":
        ligne_livraison = "🏪 *Retrait magasin* — Songon 17, près Pharmacie de la Paix\n"
    else:
        zone_label = ZONES_LBL.get(zone_liv, zone_liv)
        ligne_livraison = (
            f"🚚 *Livraison* — {zone_label}\n"
            f"📍 Adresse : {adresse}\n"
            f"💸 Frais livraison : {_formater_montant(frais_liv)}\n"
        )

    # ── Composition du message ────────────────────────────────
    message = (
        f"Bonjour IKLILOUNE 🌸 *La Maison du Chic*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 *Commande {commande.numero}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{lignes_articles}\n"
        f"💰 Sous-total : {_formater_montant(commande.sous_total)}\n"
        f"{ligne_remise}"
        f"✅ *TOTAL À PAYER : {_formater_montant(commande.total)}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Client :* {commande.client_nom}\n"
        f"📞 *Tél :* {commande.client_telephone}\n"
        f"{ligne_livraison}"
        f"💳 *Paiement :* {paiement}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Je souhaite confirmer cette commande. Merci ! 🙏"
    )

    numero_boutique = config.NUMERO_WHATSAPP
    url = f"https://wa.me/{numero_boutique}?text={quote(message)}"
    return url


def message_notification_statut(commande) -> dict:
    """
    Génère le message WhatsApp de notification au CLIENT
    quand le commerçant change le statut d'une commande.

    Args:
        commande (Commande): commande dont le statut vient de changer

    Returns:
        dict: { "url": "https://wa.me/...", "message": "texte preview" }
    """
    emoji, libelle = LABELS_STATUT.get(commande.statut, ("📦", commande.statut))

    # Messages personnalisés selon le statut
    messages_statut = {
        "confirmee": (
            f"Votre commande *{commande.numero}* est confirmee !\n"
            f"Nous preparons votre colis avec soin.\n"
            f"Montant : *{_formater_montant(commande.total)}*"
        ),
        "en_preparation": (
            f"Votre commande *{commande.numero}* est en cours de preparation.\n"
            f"Nous vous contacterons des qu'elle est expediee."
        ),
        "expediee": (
            f"Votre commande *{commande.numero}* est en route !\n"
            f"Un livreur vous contactera pour la livraison.\n"
            f"Adresse : {getattr(commande, 'client_adresse', '') or 'voir details'}"
        ),
        "livree": (
            f"Votre commande *{commande.numero}* a bien ete livree !\n"
            f"Merci de votre confiance. N'hesitez pas a nous laisser un retour."
        ),
        "annulee": (
            f"Votre commande *{commande.numero}* a ete annulee.\n"
            f"Pour toute question, contactez-nous."
        ),
    }
    corps = messages_statut.get(commande.statut, f"Statut mis a jour : *{libelle}*")

    # Messages sans emojis → compatibles tous téléphones
    message = (
        f"Bonjour *{commande.client_nom}*\n\n"
        f"*IKLILOUNE* | Mise a jour commande\n"
        f"---\n\n"
        f"{corps}\n\n"
        f"Ref : *{commande.numero}*\n"
        f"Total : *{_formater_montant(commande.total)}*\n\n"
        f"Des questions ? Repondez a ce message.\n"
        f"*IKLILOUNE - La Maison du Chic*"
    )

    tel = _normaliser_telephone(commande.client_telephone)
    url = f"https://wa.me/{tel}?text={quote(message)}"

    return {
        "url"     : url,
        "message" : message[:120] + "…" if len(message) > 120 else message
    }


def generer_ticket_acheteur(commande) -> dict:
    """
    Génère un ticket/reçu formaté pour l'ACHETEUR via WhatsApp.
    Distinct de message_notification_statut() qui s'adresse au client
    pour un changement de statut.

    Ce ticket est envoyé :
    - À la confirmation d'une commande en ligne
    - Immédiatement après une vente en magasin (canal="magasin")

    Returns:
        dict: { "url": "https://wa.me/...", "texte": "..." }
    """
    # ── Articles ──────────────────────────────────────────────
    lignes = ""
    for a in commande.articles():
        nom    = a.get("nom", "Article")
        qty    = int(a.get("qty", a.get("quantite", a.get("qte", 1))))
        prix_u = a.get("prix_actuel", a.get("prix_unitaire", a.get("prix", 0)))
        coloris = a.get("coloris", a.get("couleur", ""))
        taille  = a.get("taille", a.get("pointure", ""))
        detail  = ""
        if coloris: detail += f" · {coloris}"
        if taille:  detail += f" · {taille}"
        lignes += f"  • {nom}{detail} ×{qty} = {_formater_montant(qty * prix_u)}\n"

    if not lignes:
        lignes = "  • Articles commandés\n"

    # ── Remise ────────────────────────────────────────────────
    ligne_remise = ""
    remise = getattr(commande, "remise_montant", 0) or 0
    if remise > 0:
        code = getattr(commande, "code_promo_utilise", "") or ""
        suffix = f" ({code})" if code else ""
        ligne_remise = f"🎁 Remise{suffix} : -{_formater_montant(remise)}\n"

    # ── Livraison ─────────────────────────────────────────────
    mode_liv  = getattr(commande, "mode_livraison", "click_collect") or "click_collect"
    frais_liv = getattr(commande, "frais_livraison", 0) or 0
    canal     = getattr(commande, "canal", "site_web") or "site_web"

    if canal == "magasin":
        ligne_liv = "🏪 Achat en boutique — IKLILOUNE Songon 17\n"
    elif mode_liv == "click_collect":
        ligne_liv = "🏪 Retrait magasin — Songon 17, près Pharmacie de la Paix\n"
    else:
        ZONES_LBL = {
            "zone_1": "Zone 1 — Songon / Yopougon",
            "zone_2": "Zone 2 — Abidjan Centre",
            "zone_3": "Zone 3 — Banlieue / Hors Abidjan",
        }
        zone_label = ZONES_LBL.get(getattr(commande, "zone_livraison", ""), "")
        ligne_liv  = (
            f"🚚 Livraison {zone_label}\n"
            f"   Frais : {_formater_montant(frais_liv)}\n"
        )

    # ── Message complet ───────────────────────────────────────
    date_str = commande.cree_le.strftime("%d/%m/%Y à %H:%M") if commande.cree_le else "—"
    mode_pmt = getattr(commande, "mode_paiement", "") or ""
    paiement = LABELS_PAIEMENT.get(mode_pmt.lower(), mode_pmt or "—")

    texte = (
        f"🧾 *IKLILOUNE — TICKET D'ACHAT*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 Commande : *{commande.numero}*\n"
        f"📅 Date : {date_str}\n"
        f"👤 Client : {commande.client_nom}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛍️ *Articles :*\n"
        f"{lignes}\n"
        f"💰 Sous-total : {_formater_montant(commande.sous_total or commande.total)}\n"
        f"{ligne_remise}"
    )
    if frais_liv > 0:
        texte += f"🚚 Livraison : {_formater_montant(frais_liv)}\n"

    texte += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 *TOTAL PAYÉ : {_formater_montant(commande.total)} FCFA*\n"
        f"   Paiement : {paiement}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{ligne_liv}\n"
        f"🌸 *IKLILOUNE — La Maison du Chic*\n"
        f"📍 Songon 17, près Pharmacie de la Paix\n"
        f"📞 +225 07 48 95 69 59\n\n"
        f"Merci de votre confiance ! 🙏"
    )

    tel = _normaliser_telephone(commande.client_telephone)
    url = f"https://wa.me/{tel}?text={quote(texte)}"
    return {"url": url, "texte": texte}
