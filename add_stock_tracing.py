#!/usr/bin/env python3
"""
add_stock_tracing.py — IKLILOUNE
==================================
Traçabilité complète de chaque mouvement de stock :
  1. Crée backend/models/historique_stock.py
  2. Patche admin.py :
       - Log "ajout_initial" dans ajouter_produit()
       - Log "ajustement_manuel" dans modifier_produit() si stock change
       - Log "desactivation" / "reactivation" dans les routes soft-delete
       - Décrémente automatiquement le stock à la CONFIRMATION d'une commande
       - Récremente automatiquement le stock à l'ANNULATION
       - Nouvelles routes GET /admin/api/historique-stock[/<pid>]
  3. Crée migrate_historique_stock.py (à lancer séparément)
  4. Git commit + push

Exécuter depuis ~/IKLILOUNE : python add_stock_tracing.py
"""
import os
import re
import subprocess

BASE = os.getcwd()


def _read(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return f.read()


def _write(p, c):
    fp = os.path.join(BASE, p)
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    with open(fp, "w", encoding="utf-8") as f:
        f.write(c)


def _patch(path, old, new, label):
    c = _read(path)
    if old in c:
        _write(path, c.replace(old, new, 1))
        print(f"  ✅ {label}")
        return True
    elif new.strip()[:40] in c:
        print(f"  ⏭  Déjà appliqué — {label}")
        return True
    else:
        print(f"  ⚠️  Pattern non trouvé — {label}")
        return False


print("=" * 60)
print("  IKLILOUNE — Traçabilité stock (HistoriqueStock)")
print("=" * 60)

# ══════════════════════════════════════════════════════════════
# 1. Modèle HistoriqueStock
# ══════════════════════════════════════════════════════════════
HISTORIQUE_STOCK_PY = '''\
# =============================================================
# models/historique_stock.py — Audit complet des mouvements de stock
# OBJECTIF SÉCURITÉ : détecter toute manipulation frauduleuse.
# =============================================================
from datetime import datetime
from backend.database import db


class HistoriqueStock(db.Model):
    """
    Trace CHAQUE modification de stock, quelle qu'en soit la cause.

    Types de mouvement :
        ajout_initial       — création d'un produit avec stock > 0
        ajustement_manuel   — admin modifie le stock depuis l'interface
        vente               — commande confirmée → stock décrémenté
        annulation_commande — commande annulée  → stock remis en rayon
        desactivation       — produit désactivé (retiré du catalogue)
        reactivation        — produit réactivé (remis en ligne)
        correction          — correction ponctuelle documentée
        vente_magasin       — vente directe en boutique (caisse)
    """
    __tablename__ = "historique_stock"

    id             = db.Column(db.Integer, primary_key=True)
    produit_id     = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    type_mouvement = db.Column(db.String(40), nullable=False, index=True)
    quantite_avant = db.Column(db.Integer, nullable=False)
    quantite_apres = db.Column(db.Integer, nullable=False)
    delta          = db.Column(db.Integer, nullable=False)   # + entrée, - sortie
    commande_id    = db.Column(db.Integer, db.ForeignKey("commandes.id"), nullable=True)
    note           = db.Column(db.String(300), nullable=True)

    produit  = db.relationship("Produit",
                               backref=db.backref("mouvements_stock", lazy="dynamic"))
    commande = db.relationship("Commande",
                               backref=db.backref("mouvements_stock", lazy="dynamic"))

    def __repr__(self):
        signe = "+" if self.delta >= 0 else ""
        return (f"<HistoriqueStock [{self.type_mouvement}] "
                f"{signe}{self.delta} produit_id={self.produit_id}>")

    def vers_dict(self):
        return {
            "id"           : self.id,
            "produit_id"   : self.produit_id,
            "produit_nom"  : self.produit.nom if self.produit else "—",
            "produit_ref"  : self.produit.reference if self.produit else "—",
            "date"         : self.date_mouvement.strftime("%d/%m/%Y %H:%M"),
            "type"         : self.type_mouvement,
            "avant"        : self.quantite_avant,
            "apres"        : self.quantite_apres,
            "delta"        : self.delta,
            "commande_id"  : self.commande_id,
            "commande_num" : self.commande.numero if self.commande else "",
            "note"         : self.note or "",
        }
'''
_write("backend/models/historique_stock.py", HISTORIQUE_STOCK_PY)
print("  ✅ backend/models/historique_stock.py créé")


# ══════════════════════════════════════════════════════════════
# 2. Patch admin.py — import HistoriqueStock
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",
    "from backend.services.commande_service import message_notification_statut",
    "from backend.services.commande_service import message_notification_statut\n"
    "from backend.models.historique_stock   import HistoriqueStock",
    "Import HistoriqueStock"
)


# ══════════════════════════════════════════════════════════════
# 3. Patch ajouter_produit() — log ajout_initial
#    flush() pour obtenir l'ID, on ajoute le log, puis commit unique
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",
    "        db.session.add(produit)\n"
    "        db.session.commit()  # commit pour obtenir l'ID avant de nommer la photo",

    "        db.session.add(produit)\n"
    "        db.session.flush()  # flush pour obtenir l'ID (dans la transaction courante)\n"
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

    "Log ajout_initial dans ajouter_produit()"
)


# ══════════════════════════════════════════════════════════════
# 4. Patch modifier_produit() — capturer stock_avant
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",
    "    produit = db.get_or_404(Produit, pid)\n"
    "    try:\n"
    "        produit.nom            = request.form.get(\"nom\",       produit.nom).strip()\n"
    "        produit.categorie      = request.form.get(\"categorie\", produit.categorie)\n"
    "        produit.genre          = request.form.get(\"genre\",     produit.genre)\n"
    "        produit.prix           = int(request.form.get(\"prix\",  produit.prix))\n"
    "        produit.stock          = int(request.form.get(\"stock\", produit.stock))",

    "    produit = db.get_or_404(Produit, pid)\n"
    "    try:\n"
    "        stock_avant = produit.stock  # mémoriser avant toute modification\n"
    "        produit.nom            = request.form.get(\"nom\",       produit.nom).strip()\n"
    "        produit.categorie      = request.form.get(\"categorie\", produit.categorie)\n"
    "        produit.genre          = request.form.get(\"genre\",     produit.genre)\n"
    "        produit.prix           = int(request.form.get(\"prix\",  produit.prix))\n"
    "        produit.stock          = int(request.form.get(\"stock\", produit.stock))",

    "Capture stock_avant dans modifier_produit()"
)

# Injecter le log juste avant db.session.commit() de modifier_produit
_patch(
    "backend/routes/admin.py",
    "        db.session.commit()\n"
    "        print(f\"✅ Produit modifié : [{produit.reference}] {produit.nom}\")\n"
    "        return jsonify({\"succes\": True, \"produit\": produit.vers_dict_admin()})\n"
    "\n"
    "    except Exception as e:\n"
    "        db.session.rollback()\n"
    "        print(f\"❌ Erreur modifier_produit : {e}\")\n"
    "        return jsonify({\"erreur\": str(e)}), 500",

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
    "            ))\n"
    "        db.session.commit()\n"
    "        print(f\"✅ Produit modifié : [{produit.reference}] {produit.nom}\")\n"
    "        return jsonify({\"succes\": True, \"produit\": produit.vers_dict_admin()})\n"
    "\n"
    "    except Exception as e:\n"
    "        db.session.rollback()\n"
    "        print(f\"❌ Erreur modifier_produit : {e}\")\n"
    "        return jsonify({\"erreur\": str(e)}), 500",

    "Log ajustement_manuel dans modifier_produit()"
)


# ══════════════════════════════════════════════════════════════
# 5. Patch supprimer_produit() — log désactivation
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",
    "    produit = db.get_or_404(Produit, pid)\n"
    "    produit.actif = False\n"
    "    db.session.commit()\n"
    "    print(f\"🗑️ Produit désactivé : [{produit.reference}] {produit.nom}\")\n"
    "    return jsonify({\"succes\": True, \"message\": f\"'{produit.nom}' retiré du catalogue\"})",

    "    produit = db.get_or_404(Produit, pid)\n"
    "    stock_courant = produit.stock\n"
    "    produit.actif = False\n"
    "    db.session.add(HistoriqueStock(\n"
    "        produit_id=produit.id,\n"
    "        type_mouvement=\"desactivation\",\n"
    "        quantite_avant=stock_courant,\n"
    "        quantite_apres=stock_courant,\n"
    "        delta=0,\n"
    "        note=\"Produit désactivé — retiré du catalogue\"\n"
    "    ))\n"
    "    db.session.commit()\n"
    "    print(f\"🗑️ Produit désactivé : [{produit.reference}] {produit.nom}\")\n"
    "    return jsonify({\"succes\": True, \"message\": f\"'{produit.nom}' retiré du catalogue\"})",

    "Log désactivation dans supprimer_produit()"
)


# ══════════════════════════════════════════════════════════════
# 6. Patch reactiver_produit() — log réactivation
# ══════════════════════════════════════════════════════════════
_patch(
    "backend/routes/admin.py",
    "    produit = db.get_or_404(Produit, pid)\n"
    "    produit.actif = True\n"
    "    db.session.commit()\n"
    "    return jsonify({\"succes\": True, \"message\": f\"'{produit.nom}' remis en ligne\"})",

    "    produit = db.get_or_404(Produit, pid)\n"
    "    produit.actif = True\n"
    "    db.session.add(HistoriqueStock(\n"
    "        produit_id=produit.id,\n"
    "        type_mouvement=\"reactivation\",\n"
    "        quantite_avant=produit.stock,\n"
    "        quantite_apres=produit.stock,\n"
    "        delta=0,\n"
    "        note=\"Produit réactivé — remis en ligne\"\n"
    "    ))\n"
    "    db.session.commit()\n"
    "    return jsonify({\"succes\": True, \"message\": f\"'{produit.nom}' remis en ligne\"})",

    "Log réactivation dans reactiver_produit()"
)


# ══════════════════════════════════════════════════════════════
# 7. Patch modifier_statut_commande() — décrément / récrément auto
# ══════════════════════════════════════════════════════════════
OLD_STATUT = (
    "        # ── Enregistrement de l'historique ───────────────────────\n"
    "        # Chaque changement est tracé avec qui l'a fait et quand\n"
    "        historique_entry = HistoriqueStatut(\n"
    "            commande_id  = commande.id,\n"
    "            statut_avant = statut_avant,\n"
    "            statut_apres = nouveau_statut,\n"
    "            note         = note_admin or f\"Statut changé de '{statut_avant}' vers '{nouveau_statut}'\",\n"
    "            modifie_par  = current_user.email if current_user.is_authenticated else \"système\",\n"
    "        )\n"
    "        db.session.add(historique_entry)\n"
    "        db.session.commit()"
)

NEW_STATUT = (
    "        # ── Enregistrement de l'historique statut ────────────────\n"
    "        historique_entry = HistoriqueStatut(\n"
    "            commande_id  = commande.id,\n"
    "            statut_avant = statut_avant,\n"
    "            statut_apres = nouveau_statut,\n"
    "            note         = note_admin or f\"Statut changé de '{statut_avant}' vers '{nouveau_statut}'\",\n"
    "            modifie_par  = current_user.email if current_user.is_authenticated else \"système\",\n"
    "        )\n"
    "        db.session.add(historique_entry)\n"
    "\n"
    "        # ── Mouvement de stock automatique ────────────────────────\n"
    "        # CONFIRMATION → décrémenter le stock de chaque article\n"
    "        if nouveau_statut == \"confirmee\" and statut_avant != \"confirmee\":\n"
    "            try:\n"
    "                import json as _json\n"
    "                for article in _json.loads(commande.articles_json or \"[]\"):\n"
    "                    pid_art = article.get(\"id\")\n"
    "                    qty = int(article.get(\"qty\",\n"
    "                              article.get(\"quantite\",\n"
    "                              article.get(\"qte\", 1))))\n"
    "                    if pid_art:\n"
    "                        prod = db.session.get(Produit, pid_art)\n"
    "                    else:\n"
    "                        ref = article.get(\"reference\", \"\")\n"
    "                        prod = Produit.query.filter_by(reference=ref).first() if ref else None\n"
    "                    if prod and qty > 0:\n"
    "                        avant = prod.stock\n"
    "                        prod.stock = max(0, prod.stock - qty)\n"
    "                        db.session.add(HistoriqueStock(\n"
    "                            produit_id=prod.id,\n"
    "                            type_mouvement=\"vente\",\n"
    "                            quantite_avant=avant,\n"
    "                            quantite_apres=prod.stock,\n"
    "                            delta=prod.stock - avant,\n"
    "                            commande_id=commande.id,\n"
    "                            note=f\"Vente — commande {commande.numero}\"\n"
    "                        ))\n"
    "            except Exception as e_stock:\n"
    "                print(f\"⚠️ Erreur décrément stock : {e_stock}\")\n"
    "\n"
    "        # ANNULATION → remettre le stock uniquement si une vente avait été enregistrée\n"
    "        elif nouveau_statut == \"annulee\":\n"
    "            vente_log = HistoriqueStock.query.filter_by(\n"
    "                commande_id=commande.id,\n"
    "                type_mouvement=\"vente\"\n"
    "            ).first()\n"
    "            if vente_log:\n"
    "                try:\n"
    "                    import json as _json\n"
    "                    for article in _json.loads(commande.articles_json or \"[]\"):\n"
    "                        pid_art = article.get(\"id\")\n"
    "                        qty = int(article.get(\"qty\",\n"
    "                                  article.get(\"quantite\",\n"
    "                                  article.get(\"qte\", 1))))\n"
    "                        if pid_art:\n"
    "                            prod = db.session.get(Produit, pid_art)\n"
    "                        else:\n"
    "                            ref = article.get(\"reference\", \"\")\n"
    "                            prod = Produit.query.filter_by(reference=ref).first() if ref else None\n"
    "                        if prod and qty > 0:\n"
    "                            avant = prod.stock\n"
    "                            prod.stock = prod.stock + qty\n"
    "                            db.session.add(HistoriqueStock(\n"
    "                                produit_id=prod.id,\n"
    "                                type_mouvement=\"annulation_commande\",\n"
    "                                quantite_avant=avant,\n"
    "                                quantite_apres=prod.stock,\n"
    "                                delta=qty,\n"
    "                                commande_id=commande.id,\n"
    "                                note=f\"Annulation — stock remis ({commande.numero})\"\n"
    "                            ))\n"
    "                except Exception as e_stock:\n"
    "                    print(f\"⚠️ Erreur récrément stock : {e_stock}\")\n"
    "\n"
    "        db.session.commit()"
)

_patch("backend/routes/admin.py", OLD_STATUT, NEW_STATUT,
       "Décrément/récrément auto dans modifier_statut_commande()")


# ══════════════════════════════════════════════════════════════
# 8. Nouvelles routes — historique stock (fin de admin.py)
# ══════════════════════════════════════════════════════════════
ROUTES_HISTO = """

# ══════════════════════════════════════════════════════════════
# HISTORIQUE STOCK — Audit et traçabilité sécurisée
# ══════════════════════════════════════════════════════════════

@admin_bp.route("/admin/api/historique-stock")
@login_required
def api_historique_stock():
    \"\"\"
    Tous les mouvements de stock, du plus récent au plus ancien.
    Filtres optionnels : ?type=vente|ajustement_manuel|... & ?limite=200
    \"\"\"
    type_filtre = request.args.get("type", "")
    limite      = request.args.get("limite", 200, type=int)

    q = HistoriqueStock.query.order_by(HistoriqueStock.date_mouvement.desc())
    if type_filtre:
        q = q.filter(HistoriqueStock.type_mouvement == type_filtre)

    return jsonify([m.vers_dict() for m in q.limit(limite).all()])


@admin_bp.route("/admin/api/historique-stock/<int:pid>")
@login_required
def api_historique_stock_produit(pid):
    \"\"\"Tous les mouvements pour un produit donné + infos du produit.\"\"\"
    produit    = db.get_or_404(Produit, pid)
    mouvements = (
        HistoriqueStock.query
        .filter_by(produit_id=pid)
        .order_by(HistoriqueStock.date_mouvement.desc())
        .all()
    )
    return jsonify({
        "produit"    : produit.vers_dict_admin(),
        "mouvements" : [m.vers_dict() for m in mouvements],
    })
"""

admin_content = _read("backend/routes/admin.py")
if "api_historique_stock" not in admin_content:
    _write("backend/routes/admin.py", admin_content.rstrip() + "\n" + ROUTES_HISTO)
    print("  ✅ Routes api_historique_stock ajoutées")
else:
    print("  ⏭  Routes historique stock déjà présentes")


# ══════════════════════════════════════════════════════════════
# 9. Script de migration DB
# ══════════════════════════════════════════════════════════════
MIGRATION = '''\
#!/usr/bin/env python3
"""
migrate_historique_stock.py
Crée la table historique_stock si elle n'existe pas encore.
Exécuter depuis ~/IKLILOUNE : python migrate_historique_stock.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from backend.database import db
from backend.models.historique_stock import HistoriqueStock  # noqa — force l'import du modèle

with app.app_context():
    inspector = db.inspect(db.engine)
    tables    = inspector.get_table_names()
    if "historique_stock" not in tables:
        HistoriqueStock.__table__.create(db.engine)
        print("  ✅ Table historique_stock créée")
    else:
        print("  ⏭  Table historique_stock existe déjà")
    print("  Migration terminée.")
'''
_write("migrate_historique_stock.py", MIGRATION)
print("  ✅ migrate_historique_stock.py créé")


# ══════════════════════════════════════════════════════════════
# 10. Git commit + push
# ══════════════════════════════════════════════════════════════
subprocess.run("git add -A", shell=True)
subprocess.run(
    'git commit -m '
    '"feat: HistoriqueStock — traçabilité stock + auto décrément/récrément sur statut commande"',
    shell=True
)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("  ✅ Script terminé !")
print()
print("  Étapes suivantes (dans le terminal) :")
print("  1. python migrate_historique_stock.py")
print("  2. python add_magasin_features.py")
print("=" * 60)
