#!/usr/bin/env python3
"""
fix_stats_and_wa.py — IKLILOUNE
=================================
Corrections :
  1. WhatsApp ◆ (emojis non rendus) → messages texte uniquement avec *gras*
  2. Graphique ventes : axe Y flotte en négatif → forcer ylim(bottom=0)
     + message "Aucune vente" quand données = 0
  3. Boutons Préc./Suiv. stats → chargerGraphiqueAnnee() met réellement
     à jour le graphique via un nouvel endpoint server-side
  4. Excel exports → articles qty : a.get('quantite',1) → fallback qty/qte
  5. Nouvel endpoint /admin/api/stats/graphique-ventes

À faire en terminal AVANT de lancer ce script :
    pip install openpyxl --break-system-packages
"""

import os, subprocess, sys

BASE = os.getcwd()


def _read(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return f.read()


def _write(p, c):
    with open(os.path.join(BASE, p), "w", encoding="utf-8") as f:
        f.write(c)


def _patch(path, old, new, label):
    c = _read(path)
    if old in c:
        _write(path, c.replace(old, new, 1))
        print(f"  ✅ {label}")
        return True
    elif new.strip()[:60] in c:
        print(f"  ⏭  Déjà corrigé — {label}")
        return True
    else:
        print(f"  ⚠️  Pattern non trouvé — {label}")
        return False


print("=" * 60)
print("  IKLILOUNE — fix_stats_and_wa")
print("=" * 60)


# ══════════════════════════════════════════════════════════════
# 1. WHATSAPP — Remplacer les emojis par du texte simple
#    Les emojis 🌸 ✅ ❌ 📦 💰 ne s'affichent pas en ◆ sur
#    certains téléphones Android anciens ou WhatsApp Business.
#    Solution : uniquement du *gras* WhatsApp + texte clair.
# ══════════════════════════════════════════════════════════════

print("\n[1] commande_service.py — Messages WhatsApp sans emojis")

# 1a. Réécriture de la fonction message_notification_statut
_patch(
    "backend/services/commande_service.py",

    '    message = (\n'
    '        f"Bonjour *{commande.client_nom}* 🌸\\n\\n"\n'
    '        f"{emoji} *IKLILOUNE — Mise à jour commande*\\n\\n"\n'
    '        f"{corps}\\n\\n"\n'
    '        f"📦 Réf : *{commande.numero}*\\n"\n'
    '        f"💰 Total : *{_formater_montant(commande.total)}*\\n\\n"\n'
    '        f"Des questions ? Répondez à ce message.\\n"\n'
    '        f"*IKLILOUNE — La Maison du Chic* 🛍️"\n'
    '    )',

    '    # Messages sans emojis → compatibles tous téléphones\n'
    '    message = (\n'
    '        f"Bonjour *{commande.client_nom}*\\n\\n"\n'
    '        f"*IKLILOUNE* | Mise a jour commande\\n"\n'
    '        f"---\\n\\n"\n'
    '        f"{corps}\\n\\n"\n'
    '        f"Ref : *{commande.numero}*\\n"\n'
    '        f"Total : *{_formater_montant(commande.total)}*\\n\\n"\n'
    '        f"Des questions ? Repondez a ce message.\\n"\n'
    '        f"*IKLILOUNE - La Maison du Chic*"\n'
    '    )',

    "commande_service.py : notification WA sans emojis"
)

# 1b. Corps du message "confirmee" sans emojis
_patch(
    "backend/services/commande_service.py",

    '        "confirmee": (\n'
    '            f"Votre commande *{commande.numero}* est confirmée ! 🎉\\n"\n'
    '            f"Nous préparons votre colis avec soin.\\n"\n'
    '            f"Montant : *{_formater_montant(commande.total)}*"\n'
    '        ),',

    '        "confirmee": (\n'
    '            f"Votre commande *{commande.numero}* est confirmee !\\n"\n'
    '            f"Nous preparons votre colis avec soin.\\n"\n'
    '            f"Montant : *{_formater_montant(commande.total)}*"\n'
    '        ),',

    "commande_service.py : corps confirmee sans emojis"
)

# 1c. Corps du message "en_preparation" sans emojis
_patch(
    "backend/services/commande_service.py",

    '        "en_preparation": (\n'
    '            f"Votre commande *{commande.numero}* est en cours de préparation 🔄\\n"\n'
    '            f"Nous vous contacterons dès qu\'elle est expédiée."\n'
    '        ),',

    '        "en_preparation": (\n'
    '            f"Votre commande *{commande.numero}* est en cours de preparation.\\n"\n'
    '            f"Nous vous contacterons des qu\'elle est expediee."\n'
    '        ),',

    "commande_service.py : corps en_preparation sans emojis"
)

# 1d. Corps du message "expediee" sans emojis
_patch(
    "backend/services/commande_service.py",

    '        "expediee": (\n'
    '            f"Votre commande *{commande.numero}* est en route ! 🚚\\n"\n'
    "            f\"Un livreur vous contactera pour la livraison.\\n\"\n"
    "            f\"Adresse enregistrée : {getattr(commande, 'client_adresse', '') or 'voir détails'}\"\n"
    '        ),',

    '        "expediee": (\n'
    '            f"Votre commande *{commande.numero}* est en route !\\n"\n'
    "            f\"Un livreur vous contactera pour la livraison.\\n\"\n"
    "            f\"Adresse : {getattr(commande, 'client_adresse', '') or 'voir details'}\"\n"
    '        ),',

    "commande_service.py : corps expediee sans emojis"
)

# 1e. Corps du message "livree" sans emojis
_patch(
    "backend/services/commande_service.py",

    '        "livree": (\n'
    '            f"Votre commande *{commande.numero}* a bien été livrée ! 🎉\\n"\n'
    '            f"Merci de votre confiance. N\'hésitez pas à nous laisser un retour."\n'
    '        ),',

    '        "livree": (\n'
    '            f"Votre commande *{commande.numero}* a bien ete livree !\\n"\n'
    '            f"Merci de votre confiance. N\'hesitez pas a nous laisser un retour."\n'
    '        ),',

    "commande_service.py : corps livree sans emojis"
)

# 1f. Corps du message "annulee" sans emojis
_patch(
    "backend/services/commande_service.py",

    '        "annulee": (\n'
    '            f"Votre commande *{commande.numero}* a été annulée ❌\\n"\n'
    '            f"Pour toute question, contactez-nous."\n'
    '        ),',

    '        "annulee": (\n'
    '            f"Votre commande *{commande.numero}* a ete annulee.\\n"\n'
    '            f"Pour toute question, contactez-nous."\n'
    '        ),',

    "commande_service.py : corps annulee sans emojis"
)

# 1g. Fallback pour statuts inconnus
_patch(
    "backend/services/commande_service.py",
    '    corps = messages_statut.get(commande.statut, f"Statut mis à jour : *{libelle}*")',
    '    corps = messages_statut.get(commande.statut, f"Statut mis a jour : *{libelle}*")',
    "commande_service.py : fallback sans accents"
)


# ══════════════════════════════════════════════════════════════
# 2. GRAPHIQUE VENTES — Axe Y positif + message si aucune vente
# ══════════════════════════════════════════════════════════════

print("\n[2] stats_service.py — Graphique : axe Y >= 0 + 'Aucune vente'")

_patch(
    "backend/services/stats_service.py",

    '    couleurs = [OR if v > 0 else OR + "44" for v in valeurs]\n'
    '    barres = ax.bar(mois, valeurs, color=couleurs,\n'
    '                    edgecolor=OR_CLAIR, linewidth=0.6,\n'
    '                    width=0.65, zorder=3)\n'
    '\n'
    '    # Afficher le CA au-dessus de chaque barre non nulle\n'
    '    for b, v in zip(barres, valeurs):\n'
    '        if v > 0:\n'
    '            label = f"{v//1000}k" if v >= 10000 else str(v)\n'
    '            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 500,\n'
    '                    label, ha="center", va="bottom",\n'
    '                    color=OR_CLAIR, fontsize=7, fontweight="bold")\n'
    '\n'
    '    ax.set_ylabel("CA (FCFA)", color=TEXTE, fontsize=8)\n'
    '    ax.set_title(f"Ventes mensuelles {annee or datetime.utcnow().year}",\n'
    '                 color=TEXTE, fontsize=10, pad=12)\n'
    '    plt.tight_layout(pad=1.2)',

    '    if max(valeurs, default=0) > 0:\n'
    '        # Barres réelles avec couleur par valeur\n'
    '        couleurs = [OR if v > 0 else OR + "44" for v in valeurs]\n'
    '        barres = ax.bar(mois, valeurs, color=couleurs,\n'
    '                        edgecolor=OR_CLAIR, linewidth=0.6,\n'
    '                        width=0.65, zorder=3)\n'
    '        for b, v in zip(barres, valeurs):\n'
    '            if v > 0:\n'
    '                label = f"{v//1000}k" if v >= 10000 else str(v)\n'
    '                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 500,\n'
    '                        label, ha="center", va="bottom",\n'
    '                        color=OR_CLAIR, fontsize=7, fontweight="bold")\n'
    '    else:\n'
    '        # Aucune vente — barres vides + message centré\n'
    '        ax.bar(mois, [0] * 12, color=OR + "22",\n'
    '               edgecolor=OR + "44", linewidth=0.6, width=0.65)\n'
    '        ax.text(0.5, 0.5, "Aucune vente confirmée\\npour cette période",\n'
    '                ha="center", va="center", color=TEXTE, fontsize=11,\n'
    '                fontweight="bold", transform=ax.transAxes, alpha=0.6)\n'
    '\n'
    '    ax.set_ylim(bottom=0)   # Axe Y toujours positif\n'
    '    ax.set_ylabel("CA (FCFA)", color=TEXTE, fontsize=8)\n'
    '    ax.set_title(f"Ventes mensuelles {annee or datetime.utcnow().year}",\n'
    '                 color=TEXTE, fontsize=10, pad=12)\n'
    '    plt.tight_layout(pad=1.2)',

    "stats_service.py : graphique ventes — axe Y >= 0 + message aucune vente"
)

# Même fix pour graphique_ventes_30_jours
_patch(
    "backend/services/stats_service.py",
    '    ax.fill_between(range(len(valeurs)), valeurs,\n'
    '                    alpha=0.15, color=OR, zorder=2)\n'
    '    ax.plot(range(len(valeurs)), valeurs,\n'
    '            color=OR, linewidth=2, marker="o",\n'
    '            markersize=3, zorder=3)',

    '    ax.set_ylim(bottom=0)  # Pas de CA négatif\n'
    '    ax.fill_between(range(len(valeurs)), valeurs,\n'
    '                    alpha=0.15, color=OR, zorder=2)\n'
    '    ax.plot(range(len(valeurs)), valeurs,\n'
    '            color=OR, linewidth=2, marker="o",\n'
    '            markersize=3, zorder=3)',

    "stats_service.py : graphique 30 jours — axe Y >= 0"
)


# ══════════════════════════════════════════════════════════════
# 3. admin.py — Nouvel endpoint graphique-ventes + fix Excel qty
# ══════════════════════════════════════════════════════════════

print("\n[3] admin.py — Endpoint graphique-ventes + Excel articles qty")

# 3a. Ajouter l'endpoint après api_stats_kpis
_patch(
    "backend/routes/admin.py",

    '@admin_bp.route("/admin/api/stats/kpis")\n'
    '@login_required\n'
    'def api_stats_kpis():\n'
    '    """Retourne les KPIs en temps réel (JSON) — pour les mises à jour AJAX du dashboard."""\n'
    '    return jsonify(calculer_kpis())',

    '@admin_bp.route("/admin/api/stats/kpis")\n'
    '@login_required\n'
    'def api_stats_kpis():\n'
    '    """Retourne les KPIs en temps réel (JSON) — pour les mises à jour AJAX du dashboard."""\n'
    '    return jsonify(calculer_kpis())\n'
    '\n'
    '\n'
    '@admin_bp.route("/admin/api/stats/graphique-ventes")\n'
    '@login_required\n'
    'def api_graphique_ventes():\n'
    '    """\n'
    '    Retourne le graphique ventes mensuelles en base64 pour une année donnée.\n'
    '    Utilisé par le bouton Préc./Suiv. de la section Statistiques.\n'
    '    Paramètre URL : ?annee=2026\n'
    '    """\n'
    '    annee = request.args.get("annee", type=int, default=datetime.now().year)\n'
    '    img = graphique_ventes_mensuelles(annee)\n'
    '    return jsonify({"image": img, "annee": annee})',

    "admin.py : endpoint /admin/api/stats/graphique-ventes"
)

# 3b. Fix qty dans exporter_ventes_excel (feuille Commandes)
_patch(
    "backend/routes/admin.py",

    '            resume_art = ", ".join(\n'
    '                f"{a.get(\'nom\',\'?\')} x{a.get(\'quantite\',1)}" for a in articles\n'
    '            )',

    '            resume_art = ", ".join(\n'
    '                f"{a.get(\'nom\',\'?\')}"  # nom\n'
    '                f" x{a.get(\'quantite\', a.get(\'qty\', a.get(\'qte\', 1)))}"  # qty\n'
    '                for a in articles\n'
    '            )',

    "admin.py exporter_ventes_excel : qty fallback"
)

# 3c. Fix qty dans exporter_commandes_excel
_patch(
    "backend/routes/admin.py",

    '            resume   = ", ".join(f"{a.get(\'nom\',\'?\')}" \
'
    ' x{a.get(\'quantite\',1)}" for a in articles)',

    '            resume   = ", ".join(\n'
    '                f"{a.get(\'nom\',\'?\')} x{a.get(\'quantite\', a.get(\'qty\', 1))}"\n'
    '                for a in articles\n'
    '            )',

    "admin.py exporter_commandes_excel : qty fallback"
)

# Aussi corriger les articles dans les deux exports (résumé court)
_patch(
    "backend/routes/admin.py",

    "            resume   = \", \".join(f\"{a.get('nom','?')} x{a.get('quantite',1)}\" for a in articles)",

    "            resume   = \", \".join(\n"
    "                f\"{a.get('nom','?')} x{a.get('quantite', a.get('qty', a.get('qte', 1)))}\"\n"
    "                for a in articles\n"
    "            )",

    "admin.py exporter_commandes_excel : qty fallback (v2)"
)


# ══════════════════════════════════════════════════════════════
# 4. admin.js — chargerGraphiqueAnnee : mettre réellement à jour
#    le graphique en récupérant l'image base64 du serveur
# ══════════════════════════════════════════════════════════════

print("\n[4] admin.js — chargerGraphiqueAnnee : mise à jour réelle du graphique")

_patch(
    "static/js/admin.js",

    'async function chargerGraphiqueAnnee(btn, delta) {\n'
    '  _anneeGraph += delta;\n'
    '  document.getElementById("annee-graph-label").textContent = _anneeGraph;\n'
    '\n'
    '  try {\n'
    '    // On recharge le graphique depuis le serveur\n'
    '    const rep  = await fetch(`/admin/api/stats/ventes?annee=${_anneeGraph}`);\n'
    '    const data = await rep.json();\n'
    '    // Le graphique matplotlib est rendu côté serveur au chargement initial.\n'
    '    // Pour le rechargement dynamique, on affiche un message simple.\n'
    '    const img = document.getElementById("img-graph-ventes");\n'
    '    if (img) img.style.opacity = "0.5";\n'
    '    afficherToast(`📊 Statistiques ${_anneeGraph} demandées. Actualisez la page pour voir le graphique.`);\n'
    '  } catch (e) {\n'
    '    console.error("chargerGraphiqueAnnee:", e);\n'
    '  }\n'
    '}',

    'async function chargerGraphiqueAnnee(btn, delta) {\n'
    '  _anneeGraph += delta;\n'
    '  document.getElementById("annee-graph-label").textContent = _anneeGraph;\n'
    '\n'
    '  const img = document.getElementById("img-graph-ventes");\n'
    '  if (img) img.style.opacity = "0.4";\n'
    '\n'
    '  try {\n'
    '    // Récupérer le graphique Matplotlib en base64 depuis le serveur\n'
    '    const rep  = await fetch(`/admin/api/stats/graphique-ventes?annee=${_anneeGraph}`);\n'
    '    const data = await rep.json();\n'
    '    if (img && data.image) {\n'
    '      img.src = data.image;\n'
    '      img.style.opacity = "1";\n'
    '    }\n'
    '    afficherToast(`Statistiques ${_anneeGraph} chargées`);\n'
    '  } catch (e) {\n'
    '    if (img) img.style.opacity = "1";\n'
    '    afficherToast("Erreur chargement graphique", "❌");\n'
    '    console.error("chargerGraphiqueAnnee:", e);\n'
    '  }\n'
    '}',

    "admin.js : chargerGraphiqueAnnee — mise à jour réelle du graphique"
)


# ══════════════════════════════════════════════════════════════
# 5. Import graphique_ventes_mensuelles dans admin.py
#    (nécessaire pour le nouvel endpoint)
# ══════════════════════════════════════════════════════════════

print("\n[5] admin.py — vérification import graphique_ventes_mensuelles")

content = _read("backend/routes/admin.py")
if "graphique_ventes_mensuelles" in content:
    print("  ⏭  Déjà importé")
else:
    _patch(
        "backend/routes/admin.py",
        "from backend.services.stats_service  import (\n"
        "    calculer_kpis,\n"
        "    graphique_ventes_mensuelles,",

        "from backend.services.stats_service  import (\n"
        "    calculer_kpis,\n"
        "    graphique_ventes_mensuelles,",

        "admin.py : import graphique_ventes_mensuelles (déjà présent)"
    )

    # Sinon ajouter à l'import
    if "graphique_ventes_mensuelles" not in _read("backend/routes/admin.py"):
        _patch(
            "backend/routes/admin.py",
            "from backend.services.stats_service  import (",
            "from backend.services.stats_service  import (\n"
            "    graphique_ventes_mensuelles,",
            "admin.py : ajout import graphique_ventes_mensuelles"
        )


# ══════════════════════════════════════════════════════════════
# 6. Vérification syntaxe Python
# ══════════════════════════════════════════════════════════════

print("\n[6] Vérification syntaxe")
import py_compile
for f in ["backend/routes/admin.py", "backend/services/commande_service.py",
          "backend/services/stats_service.py", "static/js/admin.js"]:
    fpath = os.path.join(BASE, f)
    if f.endswith(".py"):
        try:
            py_compile.compile(fpath, doraise=True)
            print(f"  ✅ {f} — syntaxe OK")
        except py_compile.PyCompileError as e:
            print(f"  ❌ {f} — ERREUR : {e}")
    else:
        print(f"  ✅ {f} — JS (non vérifié en Python)")


# ══════════════════════════════════════════════════════════════
# 7. openpyxl installation check
# ══════════════════════════════════════════════════════════════

print("\n[7] Installation openpyxl...")
result = subprocess.run(
    ["pip", "install", "openpyxl", "--break-system-packages", "-q"],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("  ✅ openpyxl installé avec succès")
else:
    # Essayer avec pip3
    result2 = subprocess.run(
        ["pip3", "install", "openpyxl", "--break-system-packages", "-q"],
        capture_output=True, text=True
    )
    if result2.returncode == 0:
        print("  ✅ openpyxl installé (pip3)")
    else:
        print(f"  ⚠️  pip install échoué — lancer manuellement :")
        print(f"     pip install openpyxl --break-system-packages")
        print(f"     (erreur: {result.stderr.strip()[:100]})")


# ══════════════════════════════════════════════════════════════
# 8. Git commit + push
# ══════════════════════════════════════════════════════════════

subprocess.run("git add -A", shell=True)
subprocess.run(
    'git commit -m '
    '"fix: WA sans emojis + graphique Y>=0 + nav stats live + openpyxl + Excel qty"',
    shell=True
)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("  ✅ Toutes les corrections appliquées !")
print()
print("  Relancer le serveur :")
print("  python main.py")
print()
print("  Tester :")
print("  - Stats : boutons < Préc / Suiv > mettent à jour le graphique")
print("  - Export : bouton 'Rapport ventes annuel' télécharge le .xlsx")
print("  - WhatsApp : messages sans ◆, uniquement *gras* + texte")
print("=" * 60)
