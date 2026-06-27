#!/usr/bin/env python3
"""
fix_main_indent.py — IKLILOUNE
Corrige l'IndentationError dans main.py causé par fix_bugs_v1.py
"""
import os
import subprocess

BASE = os.getcwd()
PATH = os.path.join(BASE, "main.py")

with open(PATH, encoding="utf-8") as f:
    content = f.read()

# Remplacer le bloc mal indenté par la version correcte
BAD = (
    "    with app.app_context():\n"
    "    # Auto-créer les tables manquantes (dont historique_stock)\n"
    "    from backend.models.historique_stock import HistoriqueStock  # noqa\n"
    "    db.create_all()\n"
    "\n"
    "        _init_donnees_defaut(app)\n"
)

GOOD = (
    "    with app.app_context():\n"
    "        # Auto-créer les tables manquantes (dont historique_stock)\n"
    "        from backend.models.historique_stock import HistoriqueStock  # noqa\n"
    "        db.create_all()\n"
    "\n"
    "        _init_donnees_defaut(app)\n"
)

if BAD in content:
    content = content.replace(BAD, GOOD, 1)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print("  ✅ main.py — indentation corrigée")
elif GOOD in content:
    print("  ⏭  Déjà correct")
else:
    print("  ⚠️  Pattern non trouvé — vérification manuelle requise")
    # Afficher les lignes 60-75 pour diagnostic
    lines = content.splitlines()
    for i, line in enumerate(lines[58:78], start=59):
        print(f"  {i:3d} | {repr(line)}")

# Vérification syntaxique
import py_compile, sys
try:
    py_compile.compile(PATH, doraise=True)
    print("  ✅ main.py — syntaxe Python OK")
except py_compile.PyCompileError as e:
    print(f"  ❌ Erreur syntaxe : {e}")
    sys.exit(1)

# Git commit + push
subprocess.run("git add backend/routes/admin.py static/js/admin.js main.py", shell=True)
subprocess.run('git commit -m "fix: indentation main.py + with app_context block"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n  Relancer maintenant :")
print("  python main.py")
