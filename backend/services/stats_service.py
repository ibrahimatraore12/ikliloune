# =============================================================
# services/stats_service.py — Statistiques et graphiques admin
#
# Philosophie : chaque fonction fait UNE chose.
# Les données viennent de la vraie base de données SQLAlchemy.
# Les graphiques sont générés par Matplotlib et encodés en base64
# pour être directement intégrés dans le HTML sans fichier intermédiaire.
# =============================================================

import io
import base64
from datetime import datetime, timedelta
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")   # mode non-interactif (pas d'écran requis)
import matplotlib.pyplot as plt

# ── Couleurs identité IKLILOUNE ────────────────────────────────
OR        = "#C9922A"
OR_CLAIR  = "#F0C96B"
OR_SOMBRE = "#8A6118"
ROSE      = "#F2AEBB"
VERT      = "#1E8A3C"
FOND      = "#1A1208"      # fond sombre du dashboard
FOND_BARRE= "#2D1F0A"      # fond légèrement plus clair
TEXTE     = "#FBF3E8"      # texte clair sur fond sombre


# =============================================================
# Fonctions utilitaires internes
# =============================================================

def _fig_vers_base64(fig):
    """
    Convertit une figure Matplotlib en chaîne base64 pour l'HTML.
    Permet d'intégrer le graphique directement dans <img src="...">.

    Paramètre :
        fig (Figure) : figure Matplotlib à convertir

    Retourne :
        str : "data:image/png;base64,..." prêt pour src=""
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                dpi=110, facecolor=FOND)
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)   # libérer la mémoire
    return f"data:image/png;base64,{data}"


def _style_axes(ax):
    """
    Applique le style IKLILOUNE à un axe Matplotlib.
    Appeler après avoir créé le graphique.

    Paramètre :
        ax (Axes) : axe à styliser
    """
    ax.set_facecolor(FOND_BARRE)
    ax.tick_params(colors=TEXTE, labelsize=8)
    ax.xaxis.label.set_color(TEXTE)
    ax.yaxis.label.set_color(TEXTE)
    for spine in ax.spines.values():
        spine.set_edgecolor(OR + "44")   # bordures semi-transparentes
    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color=OR, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


# =============================================================
# Fonctions de calcul des KPIs (indicateurs clés)
# =============================================================

def calculer_kpis():
    """
    Calcule les KPIs du dashboard admin en temps réel.
    Interroge directement la base de données SQLAlchemy.

    Retourne :
        dict : {
            nb_produits, nb_commandes, nb_clients, ruptures,
            ca_jour, ca_mois, ca_annee, panier_moyen,
            commandes_recentes, alertes_stock
        }
    """
    from backend.models.produit  import Produit
    from backend.models.commande import Commande
    from backend.models.client   import Client

    maintenant  = datetime.utcnow()
    debut_jour  = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
    debut_mois  = maintenant.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    debut_annee = maintenant.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── Comptes de base ────────────────────────────────────────
    nb_produits  = Produit.query.filter_by(actif=True).count()
    nb_commandes = Commande.query.count()
    nb_clients   = Client.query.filter_by(actif=True).count()

    # Produits en rupture de stock (stock = 0)
    ruptures = (Produit.query
                .filter_by(actif=True)
                .filter(Produit.stock == 0)
                .count())

    # Produits avec stock faible (stock > 0 mais <= seuil_bas)
    alertes_stock = (Produit.query
                     .filter_by(actif=True)
                     .filter(Produit.stock > 0)
                     .filter(Produit.stock <= Produit.seuil_bas)
                     .all())

    # ── Chiffre d'affaires ─────────────────────────────────────
    # Uniquement les commandes livrées ou confirmées (pas annulées)
    statuts_valides = ["confirmee", "en_preparation", "expediee", "livree"]

    def ca_periode(debut):
        """Calcule le CA total pour une période donnée."""
        result = (Commande.query
                  .filter(Commande.statut.in_(statuts_valides))
                  .filter(Commande.cree_le >= debut)
                  .with_entities(Commande.total)
                  .all())
        return sum(r[0] for r in result if r[0])

    ca_jour  = ca_periode(debut_jour)
    ca_mois  = ca_periode(debut_mois)
    ca_annee = ca_periode(debut_annee)

    # ── Panier moyen ───────────────────────────────────────────
    toutes_commandes = (Commande.query
                        .filter(Commande.statut.in_(statuts_valides))
                        .with_entities(Commande.total)
                        .all())
    panier_moyen = (
        sum(r[0] for r in toutes_commandes if r[0]) // len(toutes_commandes)
        if toutes_commandes else 0
    )

    # ── Commandes récentes (5 dernières) ──────────────────────
    commandes_recentes = (Commande.query
                          .order_by(Commande.cree_le.desc())
                          .limit(5)
                          .all())

    return {
        "nb_produits"       : nb_produits,
        "nb_commandes"      : nb_commandes,
        "nb_clients"        : nb_clients,
        "ruptures"          : ruptures,
        "ca_jour"           : ca_jour,
        "ca_mois"           : ca_mois,
        "ca_annee"          : ca_annee,
        "panier_moyen"      : panier_moyen,
        "commandes_recentes": [c.vers_dict() for c in commandes_recentes],
        "alertes_stock"     : [p.vers_dict_admin() for p in alertes_stock],
    }


# =============================================================
# Fonctions de statistiques avancées
# =============================================================

def top_produits_consultes(limite=10):
    """
    Retourne les produits les plus consultés par les visiteurs.

    Paramètre :
        limite (int) : nombre de produits à retourner (défaut : 10)

    Retourne :
        list : [{"nom": ..., "nb_consultations": ..., "reference": ...}]
    """
    from backend.models.produit import Produit

    produits = (Produit.query
                .filter_by(actif=True)
                .filter(Produit.nb_consultations > 0)
                .order_by(Produit.nb_consultations.desc())
                .limit(limite)
                .all())

    return [{"nom": p.nom, "reference": p.reference,
             "nb_consultations": p.nb_consultations,
             "categorie": p.categorie} for p in produits]


def top_produits_commandes(limite=10):
    """
    Retourne les produits les plus vendus (par nombre de commandes).

    Paramètre :
        limite (int) : nombre de produits à retourner (défaut : 10)

    Retourne :
        list : [{"nom": ..., "nb_commandes": ..., "reference": ...}]
    """
    from backend.models.produit import Produit

    produits = (Produit.query
                .filter_by(actif=True)
                .filter(Produit.nb_commandes > 0)
                .order_by(Produit.nb_commandes.desc())
                .limit(limite)
                .all())

    return [{"nom": p.nom, "reference": p.reference,
             "nb_commandes": p.nb_commandes,
             "categorie": p.categorie} for p in produits]


def ventes_par_jour(nb_jours=30):
    """
    Calcule le CA jour par jour sur les N derniers jours.
    Utilisé pour le graphique de tendance des ventes.

    Paramètre :
        nb_jours (int) : nombre de jours à analyser (défaut : 30)

    Retourne :
        list : [{"date": "01/06", "ca": 85000, "nb": 3}, ...]
    """
    from backend.models.commande import Commande

    statuts_valides = ["confirmee", "en_preparation", "expediee", "livree"]
    debut = datetime.utcnow() - timedelta(days=nb_jours)

    commandes = (Commande.query
                 .filter(Commande.statut.in_(statuts_valides))
                 .filter(Commande.cree_le >= debut)
                 .all())

    # Regrouper par date
    par_jour = defaultdict(lambda: {"ca": 0, "nb": 0})
    for cmd in commandes:
        cle = cmd.cree_le.strftime("%d/%m")
        par_jour[cle]["ca"] += cmd.total or 0
        par_jour[cle]["nb"] += 1

    # Générer toutes les dates (même celles sans vente = 0)
    resultat = []
    for i in range(nb_jours, 0, -1):
        date_obj = datetime.utcnow() - timedelta(days=i)
        cle      = date_obj.strftime("%d/%m")
        resultat.append({
            "date": cle,
            "ca"  : par_jour[cle]["ca"],
            "nb"  : par_jour[cle]["nb"],
        })

    return resultat


def ventes_par_mois(annee=None):
    """
    Calcule le CA mois par mois pour une année donnée.

    Paramètre :
        annee (int) : année à analyser (défaut : année en cours)

    Retourne :
        list : [{"mois": "Jan", "ca": 150000, "nb": 12}, ...]
    """
    from backend.models.commande import Commande

    if annee is None:
        annee = datetime.utcnow().year

    statuts_valides = ["confirmee", "en_preparation", "expediee", "livree"]
    debut_annee = datetime(annee, 1, 1)
    fin_annee   = datetime(annee, 12, 31, 23, 59, 59)

    commandes = (Commande.query
                 .filter(Commande.statut.in_(statuts_valides))
                 .filter(Commande.cree_le >= debut_annee)
                 .filter(Commande.cree_le <= fin_annee)
                 .all())

    # Noms des mois en français
    noms_mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                 "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]

    # Initialiser tous les mois à zéro
    par_mois = {i: {"ca": 0, "nb": 0} for i in range(1, 13)}

    for cmd in commandes:
        m = cmd.cree_le.month
        par_mois[m]["ca"] += cmd.total or 0
        par_mois[m]["nb"] += 1

    return [
        {"mois": noms_mois[m - 1], "ca": par_mois[m]["ca"], "nb": par_mois[m]["nb"]}
        for m in range(1, 13)
    ]


def repartition_categories():
    """
    Calcule la répartition des ventes par catégorie de produit.
    Basé sur les articles JSON des commandes.

    Retourne :
        list : [{"categorie": "Parfums", "ca": 85000, "nb": 12}]
    """
    from backend.models.commande import Commande

    statuts_valides = ["confirmee", "en_preparation", "expediee", "livree"]
    commandes = Commande.query.filter(
        Commande.statut.in_(statuts_valides)
    ).all()

    # Compter les ventes par catégorie depuis articles_json
    par_cat = defaultdict(lambda: {"ca": 0, "nb": 0})
    for cmd in commandes:
        for article in cmd.articles():
            cat = article.get("categorie", "autre")
            qty = article.get("qty", 1)
            prix = article.get("prix_actuel", 0)
            par_cat[cat]["ca"] += prix * qty
            par_cat[cat]["nb"] += qty

    # Trier par CA décroissant
    return sorted(
        [{"categorie": cat.capitalize(), "ca": v["ca"], "nb": v["nb"]}
         for cat, v in par_cat.items()],
        key=lambda x: x["ca"], reverse=True
    )


# =============================================================
# Fonctions de génération des graphiques Matplotlib
# =============================================================

def graphique_ventes_mensuelles(annee=None):
    """
    Graphique en barres des ventes mensuelles (données réelles BDD).

    Paramètre :
        annee (int) : année à afficher (défaut : année en cours)

    Retourne :
        str : image PNG encodée en base64 pour <img src="...">
    """
    donnees = ventes_par_mois(annee)
    mois    = [d["mois"]  for d in donnees]
    valeurs = [d["ca"]    for d in donnees]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor(FOND)
    _style_axes(ax)

    # Colorer différemment les barres avec CA > 0
    couleurs = [OR if v > 0 else OR + "44" for v in valeurs]
    barres = ax.bar(mois, valeurs, color=couleurs,
                    edgecolor=OR_CLAIR, linewidth=0.6,
                    width=0.65, zorder=3)

    # Afficher le CA au-dessus de chaque barre non nulle
    for b, v in zip(barres, valeurs):
        if v > 0:
            label = f"{v//1000}k" if v >= 10000 else str(v)
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 500,
                    label, ha="center", va="bottom",
                    color=OR_CLAIR, fontsize=7, fontweight="bold")

    ax.set_ylabel("CA (FCFA)", color=TEXTE, fontsize=8)
    ax.set_title(f"Ventes mensuelles {annee or datetime.utcnow().year}",
                 color=TEXTE, fontsize=10, pad=12)
    plt.tight_layout(pad=1.2)

    return _fig_vers_base64(fig)


def graphique_categories():
    """
    Graphique camembert de la répartition des ventes par catégorie (données réelles).

    Retourne :
        str : image PNG encodée en base64
    """
    donnees = repartition_categories()

    # Si aucune vente encore — afficher un message
    if not donnees:
        fig, ax = plt.subplots(figsize=(4.5, 3.5))
        fig.patch.set_facecolor(FOND)
        ax.set_facecolor(FOND)
        ax.text(0.5, 0.5, "Aucune vente\nencore enregistrée",
                ha="center", va="center", color=TEXTE,
                fontsize=12, transform=ax.transAxes)
        ax.axis("off")
        return _fig_vers_base64(fig)

    labels  = [d["categorie"] for d in donnees]
    valeurs = [d["ca"]        for d in donnees]
    couleurs = [OR, OR_CLAIR, ROSE, OR_SOMBRE, "#A85870", VERT][:len(donnees)]

    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)

    wedges, texts, autotexts = ax.pie(
        valeurs, labels=labels, colors=couleurs,
        autopct="%1.0f%%", startangle=90,
        textprops={"color": TEXTE, "fontsize": 8},
        wedgeprops={"edgecolor": FOND, "linewidth": 2}
    )
    for at in autotexts:
        at.set_fontweight("bold")

    ax.set_title("Répartition par catégorie", color=TEXTE, fontsize=9, pad=8)
    plt.tight_layout()

    return _fig_vers_base64(fig)


def graphique_ventes_30_jours():
    """
    Graphique en courbe des ventes journalières sur 30 jours.

    Retourne :
        str : image PNG encodée en base64
    """
    donnees = ventes_par_jour(30)

    # Afficher 1 label sur 5 pour éviter la surcharge
    dates   = [d["date"] for d in donnees]
    valeurs = [d["ca"]   for d in donnees]
    labels_x = [d if i % 5 == 0 else "" for i, d in enumerate(dates)]

    fig, ax = plt.subplots(figsize=(10, 2.8))
    fig.patch.set_facecolor(FOND)
    _style_axes(ax)

    # Remplissage sous la courbe pour effet "area chart"
    ax.fill_between(range(len(valeurs)), valeurs,
                    alpha=0.15, color=OR, zorder=2)
    ax.plot(range(len(valeurs)), valeurs,
            color=OR, linewidth=2, marker="o",
            markersize=3, zorder=3)

    ax.set_xticks(range(len(labels_x)))
    ax.set_xticklabels(labels_x, rotation=0)
    ax.set_ylabel("CA (FCFA)", color=TEXTE, fontsize=8)
    ax.set_title("Ventes — 30 derniers jours",
                 color=TEXTE, fontsize=9, pad=8)
    plt.tight_layout(pad=1.2)

    return _fig_vers_base64(fig)
