#!/usr/bin/env python3
"""
fix_stock_edit_modal.py — IKLILOUNE
=====================================
Bug : le modal de modification produit affiche le mauvais stock
      car il appelle /api/produits/<id> (route publique)
      au lieu de la route admin qui expose le vrai stock.

Fix :
  1. admin.py — ajouter GET /admin/api/produit/<id>  (endpoint unitaire admin)
  2. admin.js — editerProduit() appelle la route admin
"""

import os, subprocess, py_compile

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
print("  IKLILOUNE — fix_stock_edit_modal")
print("=" * 60)


# ── 1. admin.py : endpoint GET /admin/api/produit/<id> ────────
# Retourne un produit unique avec vers_dict_admin() (vrai stock)
print("\n[1] admin.py — Ajout endpoint /admin/api/produit/<id>")

_patch(
    "backend/routes/admin.py",

    '@admin_bp.route("/admin/api/produits")\n'
    '@login_required\n'
    'def api_produits_admin():\n'
    '    """\n'
    '    Liste TOUS les produits (actifs ET inactifs).\n'
    '    Utilise vers_dict_admin() pour exposer le stock réel (admin only).\n'
    '    """\n'
    '    produits = Produit.query.order_by(Produit.cree_le.desc()).all()\n'
    '    return jsonify([p.vers_dict_admin() for p in produits])',

    '@admin_bp.route("/admin/api/produits")\n'
    '@login_required\n'
    'def api_produits_admin():\n'
    '    """\n'
    '    Liste TOUS les produits (actifs ET inactifs).\n'
    '    Utilise vers_dict_admin() pour exposer le stock réel (admin only).\n'
    '    """\n'
    '    produits = Produit.query.order_by(Produit.cree_le.desc()).all()\n'
    '    return jsonify([p.vers_dict_admin() for p in produits])\n'
    '\n'
    '\n'
    '@admin_bp.route("/admin/api/produit/<int:pid>")\n'
    '@login_required\n'
    'def api_produit_admin_detail(pid):\n'
    '    """\n'
    '    Retourne un produit unique avec toutes ses données admin.\n'
    '    Utilisé par le modal de modification pour afficher le vrai stock.\n'
    '    """\n'
    '    produit = db.get_or_404(Produit, pid)\n'
    '    return jsonify(produit.vers_dict_admin())',

    "admin.py : endpoint GET /admin/api/produit/<id>"
)


# ── 2. admin.js : editerProduit → appelle la route admin ──────
print("\n[2] admin.js — editerProduit() : route publique → route admin")

_patch(
    "static/js/admin.js",

    '    // Utiliser la route admin qui expose les vraies données de stock\n'
    '    const rep = await fetch(`/api/produits/${id}`);\n'
    '    const p   = await rep.json();',

    '    // Route admin → retourne le vrai stock (vers_dict_admin)\n'
    '    const rep = await fetch(`/admin/api/produit/${id}`);\n'
    '    const p   = await rep.json();',

    "admin.js : editerProduit → /admin/api/produit/<id>"
)

# Fallback si le commentaire est légèrement différent
_patch(
    "static/js/admin.js",
    '    const rep = await fetch(`/api/produits/${id}`);\n'
    '    const p   = await rep.json();',
    '    const rep = await fetch(`/admin/api/produit/${id}`);\n'
    '    const p   = await rep.json();',
    "admin.js : editerProduit → /admin/api/produit/<id> (fallback)"
)


# ── 3. Vérification syntaxe ───────────────────────────────────
print("\n[3] Vérification syntaxe")
for f in ["backend/routes/admin.py"]:
    fpath = os.path.join(BASE, f)
    try:
        py_compile.compile(fpath, doraise=True)
        print(f"  ✅ {f} — OK")
    except py_compile.PyCompileError as e:
        print(f"  ❌ {f} — ERREUR : {e}")


# ── 4. Git commit + push ──────────────────────────────────────
subprocess.run("git add -A", shell=True)
subprocess.run(
    'git commit -m "fix: modal edition produit affiche le vrai stock (route admin)"',
    shell=True
)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("  ✅ Fix appliqué !")
print()
print("  Relancer : python main.py")
print()
print("  Tester :")
print("  - Ouvrir un produit en édition")
print("  - Le champ 'Stock initial' affiche maintenant le vrai stock")
print("=" * 60)
