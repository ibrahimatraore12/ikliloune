# =============================================================
# services/stats_service.py — Graphiques du dashboard admin
# Retourne des images base64 directement intégrables en HTML.
# =============================================================

import io
import base64
import matplotlib
matplotlib.use("Agg")          # mode sans interface graphique
import matplotlib.pyplot as plt

# Couleurs identité IKLILOUNE
OR       = "#C9922A"
OR_CLAIR = "#F0C96B"
ROSE     = "#F2AEBB"
FOND     = "#1A1208"
TEXTE    = "#FBF3E8"


def _fig_vers_base64(fig):
    """Convertit une figure Matplotlib en chaîne base64 pour HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight",
                dpi=110, facecolor=FOND)
    buf.seek(0)
    data = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    plt.close(fig)
    return f"data:image/png;base64,{data}"


def graphique_ventes_mensuelles(donnees=None):
    """
    Graphique en barres des ventes mensuelles.

    Paramètre :
        donnees (list) : [(mois, montant), ...] — données réelles de la DB
                         Si None, affiche des données d'exemple.

    Retourne :
        str : image PNG encodée en base64
    """
    if donnees is None:
        # Données d'exemple — remplacées par de vraies requêtes SQL plus tard
        donnees = [
            ("Jan", 78000), ("Fév", 95000), ("Mar", 112000),
            ("Avr", 89000), ("Mai", 134000), ("Jun", 187000),
        ]

    mois    = [d[0] for d in donnees]
    valeurs = [d[1] for d in donnees]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor("#2D1F0A")

    barres = ax.bar(mois, valeurs, color=OR,
                    edgecolor=OR_CLAIR, linewidth=0.8,
                    width=0.6, zorder=3)

    # Valeur au-dessus de chaque barre
    for b in barres:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 1500,
                f"{h:,}".replace(",", " "),
                ha="center", va="bottom",
                color=OR_CLAIR, fontsize=7.5, fontweight="bold")

    ax.set_xlabel("Mois", color=TEXTE, fontsize=9)
    ax.set_ylabel("FCFA", color=TEXTE, fontsize=9)
    ax.tick_params(colors=TEXTE, labelsize=8)

    for spine in ax.spines.values():
        spine.set_edgecolor(OR + "44")

    ax.yaxis.grid(True, linestyle="--", alpha=0.2, color=OR, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout(pad=1.2)

    return _fig_vers_base64(fig)


def graphique_categories(donnees=None):
    """
    Graphique camembert de la répartition par catégorie.

    Paramètre :
        donnees (list) : [("Parfums", 35), ...] — données réelles ou exemple
    """
    if donnees is None:
        donnees = [("Parfums", 35), ("Sacs", 25),
                   ("Vêtements", 22), ("Chaussures", 18)]

    labels  = [d[0] for d in donnees]
    valeurs = [d[1] for d in donnees]
    couleurs = [OR, OR_CLAIR, ROSE, "#8A6118"]

    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    fig.patch.set_facecolor(FOND)
    ax.set_facecolor(FOND)

    ax.pie(valeurs, labels=labels, colors=couleurs,
           autopct="%1.0f%%", startangle=90,
           textprops={"color": TEXTE, "fontsize": 9})

    plt.tight_layout()
    return _fig_vers_base64(fig)
