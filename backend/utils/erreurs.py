# =============================================================
# backend/utils/erreurs.py — Traduction des erreurs techniques
# en messages compréhensibles pour l'utilisateur final.
#
# Principe : jamais d'exception Python brute côté client.
# Chaque exception est mappée sur un message en français clair.
# =============================================================

import logging

logger = logging.getLogger(__name__)


# ── Table de correspondance exception → message humain ────────
_MESSAGES = [
    # Valeurs manquantes / types incorrects
    ("NoneType",           "Un champ obligatoire est manquant ou vide."),
    ("int()",              "Un montant ou une quantité saisie est invalide."),
    ("float()",            "Un montant saisi n'est pas un nombre valide."),
    ("argument must be",   "Un champ contient une valeur incorrecte."),
    ("real number",        "Un montant ou une quantité doit être un nombre entier."),

    # Base de données
    ("UNIQUE constraint",  "Cette valeur existe déjà (doublon détecté)."),
    ("NOT NULL constraint","Un champ obligatoire n'a pas été renseigné."),
    ("FOREIGN KEY",        "Référence introuvable — l'élément lié n'existe pas."),
    ("no such table",      "La base de données n'est pas encore initialisée."),
    ("OperationalError",   "Problème de connexion à la base de données."),
    ("IntegrityError",     "Données en conflit — vérifiez les informations saisies."),

    # Fichiers / images
    ("No such file",       "Le fichier image est introuvable."),
    ("Permission denied",  "Accès refusé au fichier — contactez l'administrateur."),
    ("OSError",            "Erreur lors du traitement du fichier."),

    # Réseau / HTTP
    ("ConnectionRefused",  "Le serveur est momentanément inaccessible."),
    ("TimeoutError",       "La requête a pris trop de temps — réessayez."),

    # JSON / données
    ("JSONDecodeError",    "Les données reçues sont mal formées."),
    ("KeyError",           "Un champ attendu est absent des données."),
    ("ValueError",         "Une valeur saisie est incorrecte ou hors limites."),
    ("AttributeError",     "Erreur de traitement interne — contactez le support."),
    ("TypeError",          "Type de données incorrect — vérifiez vos saisies."),
]

# Message générique de repli
_MESSAGE_GENERIQUE = (
    "Une erreur inattendue s'est produite. "
    "Veuillez réessayer ou contacter le support."
)


def message_convivial(exception: Exception) -> str:
    """
    Transforme une exception Python en message lisible par un humain.

    Usage :
        except Exception as e:
            return jsonify({"erreur": message_convivial(e)}), 500

    Args:
        exception: n'importe quelle exception Python

    Returns:
        str: message d'erreur en français, sans jargon technique
    """
    # Logger l'erreur brute côté serveur (pour le débogage)
    logger.error("Erreur interne : %s — %s", type(exception).__name__, exception)

    texte = str(exception)
    nom   = type(exception).__name__

    # Chercher une correspondance dans la table
    for motif, message in _MESSAGES:
        if motif.lower() in texte.lower() or motif.lower() in nom.lower():
            return message

    return _MESSAGE_GENERIQUE


def valider_champs(data: dict, requis: list[str]) -> str | None:
    """
    Vérifie que tous les champs requis sont présents et non vides.

    Args:
        data   : dictionnaire des données reçues (ex: request.get_json())
        requis : liste des clés obligatoires

    Returns:
        str  : message d'erreur si un champ manque
        None : si tout est valide
    """
    for champ in requis:
        valeur = data.get(champ)
        if valeur is None or str(valeur).strip() == "":
            # Transformer "client_telephone" en "Téléphone client"
            label = champ.replace("client_", "").replace("_", " ").capitalize()
            return f"Le champ « {label} » est obligatoire."
    return None


def nettoyer_int(valeur, defaut: int = 0, nom_champ: str = "montant") -> int:
    """
    Convertit une valeur en entier de manière sécurisée.
    Lève une ValueError avec un message lisible si impossible.

    Args:
        valeur     : valeur à convertir
        defaut     : valeur par défaut si valeur est None ou ""
        nom_champ  : nom du champ (pour le message d'erreur)

    Returns:
        int: valeur convertie
    """
    if valeur is None or valeur == "":
        return defaut
    try:
        return int(float(str(valeur).replace(" ", "").replace(" ", "")))
    except (ValueError, TypeError):
        raise ValueError(
            f"Le champ « {nom_champ} » doit contenir un nombre entier valide "
            f"(reçu : {repr(valeur)})."
        )


def nettoyer_telephone(tel: str) -> str:
    """
    Normalise un numéro de téléphone ivoirien.
    - Supprime les espaces, tirets, points
    - Ajoute le préfixe +225 si absent
    - Vérifie la longueur minimale

    Args:
        tel: numéro brut saisi par l'utilisateur

    Returns:
        str: numéro normalisé (+225XXXXXXXXXX)

    Raises:
        ValueError: si le numéro est invalide
    """
    if not tel:
        raise ValueError("Le numéro de téléphone est obligatoire.")

    # Supprimer tous les séparateurs non numériques sauf le +
    propre = ""
    for c in tel:
        if c.isdigit() or c == "+":
            propre += c

    # Normaliser le préfixe 00225 → +225
    if propre.startswith("00225"):
        propre = "+225" + propre[5:]
    elif propre.startswith("225") and not propre.startswith("+"):
        propre = "+225" + propre[3:]
    elif propre.startswith("0") and len(propre) == 10:
        # Format local côte d'ivoire : 0XXXXXXXXX → +2250XXXXXXXXX
        propre = "+225" + propre
    elif not propre.startswith("+"):
        propre = "+225" + propre

    # Vérification longueur : +225 + 10 chiffres = 14 caractères
    chiffres = propre.replace("+", "")
    if len(chiffres) < 11:
        raise ValueError(
            f"Le numéro de téléphone « {tel} » semble incomplet. "
            "Vérifiez qu'il contient bien 10 chiffres après l'indicatif +225."
        )

    return propre
