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
    adresse = (getattr(commande, "client_adresse", "") or "À préciser").strip()

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
        f"📍 *Livraison :* {adresse}\n"
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
            f"Votre commande *{commande.numero}* est confirmée ! 🎉\n"
            f"Nous préparons votre colis avec soin.\n"
            f"Montant : *{_formater_montant(commande.total)}*"
        ),
        "en_preparation": (
            f"Votre commande *{commande.numero}* est en cours de préparation 🔄\n"
            f"Nous vous contacterons dès qu'elle est expédiée."
        ),
        "expediee": (
            f"Votre commande *{commande.numero}* est en route ! 🚚\n"
            f"Un livreur vous contactera pour la livraison.\n"
            f"Adresse enregistrée : {getattr(commande, 'client_adresse', '') or 'voir détails'}"
        ),
        "livree": (
            f"Votre commande *{commande.numero}* a bien été livrée ! 🎉\n"
            f"Merci de votre confiance. N'hésitez pas à nous laisser un retour."
        ),
        "annulee": (
            f"Votre commande *{commande.numero}* a été annulée ❌\n"
            f"Pour toute question, contactez-nous."
        ),
    }
    corps = messages_statut.get(commande.statut, f"Statut mis à jour : *{libelle}*")

    message = (
        f"Bonjour *{commande.client_nom}* 🌸\n\n"
        f"{emoji} *IKLILOUNE — Mise à jour commande*\n\n"
        f"{corps}\n\n"
        f"📦 Réf : *{commande.numero}*\n"
        f"💰 Total : *{_formater_montant(commande.total)}*\n\n"
        f"Des questions ? Répondez à ce message.\n"
        f"*IKLILOUNE — La Maison du Chic* 🛍️"
    )

    tel = _normaliser_telephone(commande.client_telephone)
    url = f"https://wa.me/{tel}?text={quote(message)}"

    return {
        "url"     : url,
        "message" : message[:120] + "…" if len(message) > 120 else message
    }
