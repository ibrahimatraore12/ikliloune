#!/usr/bin/env python3
"""fix_footer.py — Adresse plus visible + carte plus petite"""
import os, re

BASE = os.getcwd()

def patch(path, old, new, label=""):
    full = os.path.join(BASE, path)
    with open(full, 'r', encoding='utf-8') as f:
        c = f.read()
    if old in c:
        with open(full, 'w', encoding='utf-8') as f:
            f.write(c.replace(old, new, 1))
        print(f"  ✅ {label}")
    else:
        print(f"  ⚠️  Pattern non trouvé — {label}")

# ── 1. Adresse plus visible (blanc + or) ─────────────────────
patch(
    "templates/partials/footer.html",
    "<p>Songon 17, non loin de<br>la Pharmacie de la Paix</p>\n      <p>Abidjan, Côte d'Ivoire</p>",
    """<p style="color:#fff;font-weight:700;font-size:14px;line-height:1.6">
        📍 Songon 17, non loin de la Pharmacie de la Paix
      </p>
      <p style="color:#c9a84c;font-size:13px;font-weight:600">Abidjan, Côte d'Ivoire</p>""",
    "Adresse visible (blanc + or)"
)

# ── 2. Carte moins haute (130px au lieu de 200px) ────────────
patch(
    "templates/partials/footer.html",
    'width="100%" height="200"',
    'width="100%" height="130"',
    "Carte réduite à 130px"
)

patch(
    "templates/partials/footer.html",
    "style=\"border:0;border-radius:10px;opacity:.9\"",
    "style=\"border:0;border-radius:8px;opacity:.8\"",
    "Style carte"
)

# ── 3. CSS footer-map-wrap plus compact ──────────────────────
CSS_FIX = """
/* Footer map compact */
.footer-map-wrap { max-width: 1200px; margin: 0 auto 16px; border-radius: 8px; overflow: hidden; }
"""
css_path = os.path.join(BASE, "static/css/main.css")
with open(css_path, 'a', encoding='utf-8') as f:
    f.write(CSS_FIX)
print("  ✅ CSS map compact")

# ── 4. Git commit ─────────────────────────────────────────────
import subprocess
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: footer adresse visible + carte reduite"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n  ✅ Fait ! Redémarre le serveur : python main.py")
