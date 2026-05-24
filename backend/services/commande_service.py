# =============================================================
# services/commande_service.py — Gestion des commandes
# Génère les numéros de commande et les messages WhatsApp.
# =============================================================

import random
import string
from datetime import datetime
from backend import config


def generer_numero_commande():
    """
    Génère un numéro de commande unique lisible.
    Format : CMD-2025-XXXXX  (X = chiffre aléatoire)

    Exemple : CMD-2025-04821
    """
    annee = datetime.utcnow().year
    suffixe = ''.join(random.choices(string.digits, k=5))
    return f"CMD-{annee}-{suffixe}"


def formater_message_whatsapp(commande):
    """
    Génère le message WhatsApp pré-rempli pour une commande.

    Paramètre :
        commande (Commande) : objet commande avec ses articles

    Retourne :
        str : URL WhatsApp prête à ouvrir dans le navigateur
    """
    from urllib.parse import quote

    # Construire la liste des articles
    lignes_articles = ""
    for article in commande.articles():
        nom   = article.get("nom", "")
        qty   = article.get("qty", 1)
        prix  = article.get("prix_actuel", 0)
        sous_total = qty * prix
        lignes_articles += (
            f"• {nom} × {qty} = "
            f"{sous_total:,} FCFA\n".replace(",", " ")
        )

    total_formate = f"{commande.total:,} FCFA".replace(",", " ")

    message = (
        f"Bonjour IKLILOUNE 🌸\n\n"
        f"*Commande {commande.numero}*\n\n"
        f"{lignes_articles}\n"
        f"💰 *Total : {total_formate}*\n\n"
        f"👤 Nom : {commande.client_nom}\n"
        f"📞 Tél : {commande.client_telephone}\n"
        f"📍 Adresse : {commande.client_adresse or 'À préciser'}\n"
        f"💳 Paiement : {commande.paiement or 'À préciser'}\n\n"
        f"Merci !"
    )

    url = f"https://wa.me/{config.NUMERO_WHATSAPP}?text={quote(message)}"
    return url
