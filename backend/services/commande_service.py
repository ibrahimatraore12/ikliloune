# =============================================================
# services/commande_service.py — Gestion des commandes
# Génère les numéros, les messages WhatsApp, les notifications.
# =============================================================

from urllib.parse import quote
from backend import config


def formater_message_whatsapp(commande):
    """
    Génère l'URL WhatsApp pré-remplie pour une commande.

    Paramètre :
        commande (Commande) : objet commande avec ses articles

    Retourne :
        str : URL wa.me prête à ouvrir dans le navigateur
    """
    lignes_articles = ""
    for article in commande.articles():
        nom       = article.get("nom", "Article")
        qty       = article.get("qty", 1)
        coloris   = article.get("coloris", "")
        taille    = article.get("taille", "")
        prix      = article.get("prix_actuel", 0)
        sous_total = qty * prix

        detail = f" · {coloris}" if coloris else ""
        detail += f" · {taille}" if taille else ""
        lignes_articles += (
            f"• {nom}{detail} × {qty} = "
            f"{sous_total:,} FCFA\n".replace(",", " ")
        )

    total_fmt    = f"{commande.total:,} FCFA".replace(",", " ")
    sous_total_fmt = f"{commande.sous_total:,} FCFA".replace(",", " ")

    # Ligne remise si applicable
    ligne_remise = ""
    if commande.remise_montant and commande.remise_montant > 0:
        remise_fmt   = f"{commande.remise_montant:,} FCFA".replace(",", " ")
        code         = commande.code_promo_utilise or ""
        ligne_remise = f"🎁 Remise {code} : -{remise_fmt}\n"

    paiement_labels = {
        "orange_money" : "🟠 Orange Money",
        "mtn_momo"     : "🟡 MTN MoMo",
        "wave"         : "🔵 Wave",
        "a_definir"    : "À définir",
    }
    paiement = paiement_labels.get(commande.mode_paiement or "", "À définir")

    message = (
        f"Bonjour IKLILOUNE 🌸 *La Maison du Chic*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛒 *Commande {commande.numero}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{lignes_articles}\n"
        f"💰 Sous-total : {sous_total_fmt}\n"
        f"{ligne_remise}"
        f"✅ *TOTAL : {total_fmt}*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Client :* {commande.client_nom}\n"
        f"📞 *Tél :* {commande.client_telephone}\n"
        f"📍 *Adresse :* {commande.client_adresse or 'À préciser'}\n"
        f"💳 *Paiement :* {paiement}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Merci pour votre commande ! 🙏"
    )

    url = f"https://wa.me/{config.NUMERO_WHATSAPP}?text={quote(message)}"
    return url


def message_notification_statut(commande):
    """
    Génère le message WhatsApp de notification de changement de statut.
    Envoyé automatiquement au client quand le marchand change le statut.

    Paramètre :
        commande (Commande) : commande dont le statut vient de changer

    Retourne :
        str : URL wa.me pré-remplie pour notifier le client
    """
    emojis_statut = {
        "confirmee"      : "✅",
        "en_preparation" : "🔄",
        "expediee"       : "🚚",
        "livree"         : "🎉",
        "annulee"        : "❌",
    }
    emoji = emojis_statut.get(commande.statut, "📦")
    libelle = commande.libelle_statut()
    total_fmt = f"{commande.total:,} FCFA".replace(",", " ")

    message = (
        f"Bonjour *{commande.client_nom}* 🌸\n\n"
        f"{emoji} *Mise à jour de votre commande*\n\n"
        f"📦 Commande : *{commande.numero}*\n"
        f"💰 Montant : *{total_fmt}*\n\n"
        f"Nouveau statut : *{libelle}*\n\n"
        f"Pour toute question : wa.me/{config.NUMERO_WHATSAPP}\n\n"
        f"Merci de votre confiance 🙏 *IKLILOUNE*"
    )

    # Le numéro client doit commencer par le code pays
    tel = commande.client_telephone.replace(" ", "").replace("+", "")
    if not tel.startswith("225"):
        tel = "225" + tel.lstrip("0")

    url = f"https://wa.me/{tel}?text={quote(message)}"
    return url
