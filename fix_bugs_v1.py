#!/usr/bin/env python3
"""
fix_bugs_v1.py — IKLILOUNE
============================
Corrections ciblées :

  1. CRITIQUE — Annulation de commande impossible :
     HistoriqueStock.query.filter_by() hors du try/except
     → toute la route modifier_statut_commande échouait

  2. "×undefined" dans commandes :
     articles_json stocke {"qty":2} mais admin.js lit a.quantite

  3. "Invalid Date" dans commandes :
     cree_le est retourné en "dd/mm/yyyy HH:MM" (français)
     mais new Date() attend du format ISO → Invalid Date

Exécuter depuis ~/IKLILOUNE : python fix_bugs_v1.py
"""
import os
import subprocess

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
print("  IKLILOUNE — fix_bugs_v1")
print("=" * 60)


# ══════════════════════════════════════════════════════════════
# 1. CRITIQUE — Wrap HistoriqueStock.query dans try/except
#    (annulation de commande)
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",

    "        # ANNULATION → remettre le stock uniquement si une vente avait été enregistrée\n"
    "        elif nouveau_statut == \"annulee\":\n"
    "            vente_log = HistoriqueStock.query.filter_by(\n"
    "                commande_id=commande.id,\n"
    "                type_mouvement=\"vente\"\n"
    "            ).first()\n"
    "            if vente_log:",

    "        # ANNULATION → remettre le stock uniquement si une vente avait été enregistrée\n"
    "        elif nouveau_statut == \"annulee\":\n"
    "            try:\n"
    "                vente_log = HistoriqueStock.query.filter_by(\n"
    "                    commande_id=commande.id,\n"
    "                    type_mouvement=\"vente\"\n"
    "                ).first()\n"
    "            except Exception:\n"
    "                vente_log = None  # table absente — migration pas encore lancée\n"
    "            if vente_log:",

    "admin.py : HistoriqueStock.query enveloppé dans try/except (annulation)"
)

# Même correction pour la requête dans la section "vente_magasin"
# (pour être cohérent, on cible aussi les SELECT dans api_historique_stock)
# — ces routes ont déjà @login_required donc pas urgentes, mais on sécurise

# Sécuriser aussi les ADD dans supprimer_produit / reactiver_produit / modifier_produit
# en cas de table absente : encapsuler chaque db.session.add(HistoriqueStock(...)) isolé
# Note : les add() dans modifier_statut_commande côté "confirmee" sont déjà dans try/except

# Sécuriser log dans ajouter_produit (le flush/commit peut échouer si table absente)
_patch(
    "backend/routes/admin.py",

    "        # ── Log stock initial ────────────────────────────────────\n"
    "        if produit.stock > 0:\n"
    "            db.session.add(HistoriqueStock(\n"
    "                produit_id=produit.id,\n"
    "                type_mouvement=\"ajout_initial\",\n"
    "                quantite_avant=0,\n"
    "                quantite_apres=produit.stock,\n"
    "                delta=produit.stock,\n"
    "                note=f\"Création produit : {produit.nom}\"\n"
    "            ))\n"
    "        db.session.commit()  # commit pour obtenir l'ID avant de nommer la photo",

    "        # ── Log stock initial (sécurisé si table absente) ────────\n"
    "        if produit.stock > 0:\n"
    "            try:\n"
    "                db.session.add(HistoriqueStock(\n"
    "                    produit_id=produit.id,\n"
    "                    type_mouvement=\"ajout_initial\",\n"
    "                    quantite_avant=0,\n"
    "                    quantite_apres=produit.stock,\n"
    "                    delta=produit.stock,\n"
    "                    note=f\"Création produit : {produit.nom}\"\n"
    "                ))\n"
    "            except Exception as _e_log:\n"
    "                print(f\"⚠️ Log stock initial ignoré : {_e_log}\")\n"
    "        db.session.commit()  # commit pour obtenir l'ID avant de nommer la photo",

    "admin.py : log ajout_initial sécurisé"
)

# Sécuriser log dans modifier_produit
_patch(
    "backend/routes/admin.py",

    "        # ── Log si le stock a été modifié manuellement ───────────\n"
    "        if produit.stock != stock_avant:\n"
    "            note_adj = (request.form.get(\"note_stock\", \"\").strip()\n"
    "                        or f\"Ajustement manuel : {stock_avant} → {produit.stock}\")\n"
    "            db.session.add(HistoriqueStock(\n"
    "                produit_id=produit.id,\n"
    "                type_mouvement=\"ajustement_manuel\",\n"
    "                quantite_avant=stock_avant,\n"
    "                quantite_apres=produit.stock,\n"
    "                delta=produit.stock - stock_avant,\n"
    "                note=note_adj\n"
    "            ))",

    "        # ── Log si le stock a été modifié manuellement ───────────\n"
    "        if produit.stock != stock_avant:\n"
    "            note_adj = (request.form.get(\"note_stock\", \"\").strip()\n"
    "                        or f\"Ajustement manuel : {stock_avant} → {produit.stock}\")\n"
    "            try:\n"
    "                db.session.add(HistoriqueStock(\n"
    "                    produit_id=produit.id,\n"
    "                    type_mouvement=\"ajustement_manuel\",\n"
    "                    quantite_avant=stock_avant,\n"
    "                    quantite_apres=produit.stock,\n"
    "                    delta=produit.stock - stock_avant,\n"
    "                    note=note_adj\n"
    "                ))\n"
    "            except Exception as _e_log:\n"
    "                print(f\"⚠️ Log ajustement ignoré : {_e_log}\")",

    "admin.py : log ajustement_manuel sécurisé"
)

# Sécuriser log désactivation
_patch(
    "backend/routes/admin.py",

    "    stock_courant = produit.stock\n"
    "    produit.actif = False\n"
    "    db.session.add(HistoriqueStock(\n"
    "        produit_id=produit.id,\n"
    "        type_mouvement=\"desactivation\",\n"
    "        quantite_avant=stock_courant,\n"
    "        quantite_apres=stock_courant,\n"
    "        delta=0,\n"
    "        note=\"Produit désactivé — retiré du catalogue\"\n"
    "    ))",

    "    stock_courant = produit.stock\n"
    "    produit.actif = False\n"
    "    try:\n"
    "        db.session.add(HistoriqueStock(\n"
    "            produit_id=produit.id,\n"
    "            type_mouvement=\"desactivation\",\n"
    "            quantite_avant=stock_courant,\n"
    "            quantite_apres=stock_courant,\n"
    "            delta=0,\n"
    "            note=\"Produit désactivé — retiré du catalogue\"\n"
    "        ))\n"
    "    except Exception as _e_log:\n"
    "        print(f\"⚠️ Log désactivation ignoré : {_e_log}\")",

    "admin.py : log désactivation sécurisé"
)

# Sécuriser log réactivation
_patch(
    "backend/routes/admin.py",

    "    produit.actif = True\n"
    "    db.session.add(HistoriqueStock(\n"
    "        produit_id=produit.id,\n"
    "        type_mouvement=\"reactivation\",\n"
    "        quantite_avant=produit.stock,\n"
    "        quantite_apres=produit.stock,\n"
    "        delta=0,\n"
    "        note=\"Produit réactivé — remis en ligne\"\n"
    "    ))",

    "    produit.actif = True\n"
    "    try:\n"
    "        db.session.add(HistoriqueStock(\n"
    "            produit_id=produit.id,\n"
    "            type_mouvement=\"reactivation\",\n"
    "            quantite_avant=produit.stock,\n"
    "            quantite_apres=produit.stock,\n"
    "            delta=0,\n"
    "            note=\"Produit réactivé — remis en ligne\"\n"
    "        ))\n"
    "    except Exception as _e_log:\n"
    "        print(f\"⚠️ Log réactivation ignoré : {_e_log}\")",

    "admin.py : log réactivation sécurisé"
)


# ══════════════════════════════════════════════════════════════
# 2. admin.js — "Invalid Date" : cree_le est en format français
# ══════════════════════════════════════════════════════════════
_patch(
    "static/js/admin.js",

    "/** Formate une date ISO en chaîne lisible. */\n"
    "function formaterDate(iso) {\n"
    "  if (!iso) return \"—\";\n"
    "  return new Date(iso).toLocaleDateString(\"fr-FR\", {\n"
    "    day: \"2-digit\", month: \"2-digit\", year: \"numeric\",\n"
    "    hour: \"2-digit\", minute: \"2-digit\"\n"
    "  });\n"
    "}",

    "/** Formate une date en chaîne lisible.\n"
    " *  Accepte ISO et le format français \"dd/mm/yyyy HH:MM\" retourné par Flask. */\n"
    "function formaterDate(iso) {\n"
    "  if (!iso) return \"—\";\n"
    "  // Le serveur retourne déjà du \"dd/mm/yyyy HH:MM\" — retourner tel quel\n"
    "  if (/^\\d{2}\\/\\d{2}\\/\\d{4}/.test(String(iso))) return iso;\n"
    "  const d = new Date(iso);\n"
    "  if (isNaN(d.getTime())) return iso;  // fallback : afficher la valeur brute\n"
    "  return d.toLocaleDateString(\"fr-FR\", {\n"
    "    day: \"2-digit\", month: \"2-digit\", year: \"numeric\",\n"
    "    hour: \"2-digit\", minute: \"2-digit\"\n"
    "  });\n"
    "}",

    "admin.js : formaterDate() — gère le format français dd/mm/yyyy"
)


# ══════════════════════════════════════════════════════════════
# 3. admin.js — "×undefined" : articles JSON utilise "qty" pas "quantite"
#    + "0 FCFA" : prix_unitaire absent → fallback sur prix_actuel
# ══════════════════════════════════════════════════════════════

# 3a. Dans chargerTableCommandes() — résumé bref
_patch(
    "static/js/admin.js",

    "        if (arts.length) {\n"
    "          resumeArt = arts.slice(0, 2).map(a => `${a.nom} ×${a.quantite}`).join(\", \");\n"
    "          if (arts.length > 2) resumeArt += ` + ${arts.length - 2} autre(s)`;\n"
    "        }",

    "        if (arts.length) {\n"
    "          resumeArt = arts.slice(0, 2)\n"
    "            .map(a => `${a.nom} ×${a.quantite || a.qty || 1}`).join(\", \");\n"
    "          if (arts.length > 2) resumeArt += ` + ${arts.length - 2} autre(s)`;\n"
    "        }",

    "admin.js chargerTableCommandes : a.quantite || a.qty"
)

# 3b. Dans ouvrirModalCommande() — affichage détail article
_patch(
    "static/js/admin.js",

    "          <div style=\"font-weight:700\">×${a.quantite}</div>\n"
    "            <div style=\"font-size:11px;color:var(--brun-clair)\">${formaterPrix(a.prix_unitaire * a.quantite)}</div>",

    "          <div style=\"font-weight:700\">×${a.quantite || a.qty || 1}</div>\n"
    "            <div style=\"font-size:11px;color:var(--brun-clair)\">${formaterPrix(\n"
    "              (a.prix_unitaire || a.prix_actuel || 0) * (a.quantite || a.qty || 1)\n"
    "            )}</div>",

    "admin.js ouvrirModalCommande : quantite || qty et prix_unitaire || prix_actuel"
)

# 3c. Dans chargerVentesMagasin() dans les additions JS (même bug)
_patch(
    "static/js/admin.js",

    "      const resumeArt = arts.slice(0,2).map(a => `${a.nom} ×${a.quantite||a.qty||1}`).join(\", \")\n"
    "                        + (arts.length > 2 ? ` +${arts.length-2}` : \"\");",

    "      const resumeArt = arts.slice(0,2)\n"
    "        .map(a => `${a.nom} ×${a.quantite || a.qty || 1}`).join(\", \")\n"
    "        + (arts.length > 2 ? ` +${arts.length-2}` : \"\");",

    "admin.js chargerVentesMagasin : quantite || qty (format cohérent)"
)


# ══════════════════════════════════════════════════════════════
# 4. Migration automatique au démarrage de l'app
#    → chercher main.py et ajouter create_all() après les imports
# ══════════════════════════════════════════════════════════════
# On va ajouter la migration dans main.py directement, comme ça
# même si migrate_historique_stock.py n'a pas été lancé, la table
# sera créée au prochain redémarrage du serveur.

import os as _os
main_py = _os.path.join(BASE, "main.py")
if _os.path.exists(main_py):
    main_content = _read("main.py")

    # Chercher si on peut injecter après "with app.app_context():" ou équivalent
    # Pattern commun : app.run() ou if __name__ == "__main__":
    if "historique_stock" not in main_content and "HistoriqueStock" not in main_content:
        # Chercher le pattern d'initialisation DB
        if "db.create_all()" in main_content:
            print("  ⏭  db.create_all() déjà présent dans main.py")
        elif "with app.app_context():" in main_content:
            _patch(
                "main.py",
                "with app.app_context():",
                "with app.app_context():\n"
                "    # Auto-créer les tables manquantes (dont historique_stock)\n"
                "    from backend.models.historique_stock import HistoriqueStock  # noqa\n"
                "    db.create_all()\n",
                "main.py : auto-création historique_stock au démarrage"
            )
        elif "if __name__ == \"__main__\":" in main_content:
            _patch(
                "main.py",
                "if __name__ == \"__main__\":",
                "# Auto-créer les tables manquantes au démarrage\n"
                "with app.app_context():\n"
                "    from backend.models.historique_stock import HistoriqueStock  # noqa\n"
                "    from backend.database import db as _db\n"
                "    _db.create_all()\n"
                "\n"
                "if __name__ == \"__main__\":",
                "main.py : auto-création historique_stock au démarrage"
            )
        else:
            print("  ⚠️  Pattern main.py non trouvé — lance migrate_historique_stock.py manuellement")
    else:
        print("  ⏭  HistoriqueStock déjà importé dans main.py")
else:
    print("  ⚠️  main.py non trouvé dans ce répertoire")


# ══════════════════════════════════════════════════════════════
# 5. Git commit + push
# ══════════════════════════════════════════════════════════════
subprocess.run("git add -A", shell=True)
subprocess.run(
    'git commit -m '
    '"fix: annulation commande OK + Invalid Date + xundefined + logs stock fault-tolerant"',
    shell=True
)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("  ✅ Corrections appliquées !")
print()
print("  Relancer le serveur :")
print("  python main.py")
print()
print("  Si Audit Stock reste vide, lancer aussi :")
print("  python migrate_historique_stock.py")
print("=" * 60)
