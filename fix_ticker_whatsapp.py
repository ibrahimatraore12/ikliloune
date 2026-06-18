#!/usr/bin/env python3
"""
fix_ticker_whatsapp.py — Corrige 3 problèmes :
1. Le bouton "Commander par WhatsApp" du panier envoyait vers un numéro
   personnel au lieu du numéro boutique (+225 01 04 14 41 41).
2. Une ligne du bandeau défilant contenait des caractères corrompus
   (encodage cassé) à la place de l'émoji Wave.
3. Les espacements du bandeau défilant sont élargis pour plus de lisibilité.

À lancer UNE SEULE FOIS depuis la racine du projet (~/IKLILOUNE) :
    python3 fix_ticker_whatsapp.py
"""
import sys

remplacements = []

# 1. Numero WhatsApp boutique (JS) -----------------------------------
remplacements.append((
    "static/js/boutique.js",
    'const WA_BOUTIQUE = "2250748956959";',
    'const WA_BOUTIQUE = "2250104144141";',
))

# 2. Numero WhatsApp boutique (config backend) ------------------------
remplacements.append((
    "backend/config.py",
    'NUMERO_WHATSAPP  = os.environ.get("NUMERO_WHATSAPP", "2250748956959")   # numéro principal',
    'NUMERO_WHATSAPP  = os.environ.get("NUMERO_WHATSAPP", "2250104144141")   # numéro principal',
))

# 3. Ligne ticker corrompue -> remplacee par les vrais logos -----------
remplacements.append((
    "templates/boutique/index.html",
    '    <span class="ticker-item">🟠 Orange Money · 🟡 MTN MoMo · �� Wave acceptés</span>',
    """    <span class="ticker-item ticker-logos">
      <img src="{{ url_for('static', filename='images/logos/orange-money.svg') }}" alt="Orange Money" class="ticker-logo">
      <img src="{{ url_for('static', filename='images/logos/mtn-momo.svg') }}" alt="MTN MoMo" class="ticker-logo">
      <img src="{{ url_for('static', filename='images/logos/wave.svg') }}" alt="Wave" class="ticker-logo">
      acceptés
    </span>""",
))

# 4. Espacements ticker ------------------------------------------------
remplacements.append((
    "static/css/main.css",
    """.ticker-item {
  display:inline-flex; align-items:center; gap:8px;
  padding:0 28px; font-size:12px; color:rgba(255,255,255,0.8);
  font-weight:600; letter-spacing:0.3px;
}""",
    """.ticker-item {
  display:inline-flex; align-items:center; gap:8px; flex-shrink:0;
  padding:0 36px; font-size:12px; color:rgba(255,255,255,0.8);
  font-weight:600; letter-spacing:0.3px;
}""",
))
remplacements.append((
    "static/css/main.css",
    """.ticker-logos { display:inline-flex; align-items:center; gap:6px; vertical-align:middle; }
.ticker-logo  { width:56px; height:22px; object-fit:contain; border-radius:4px; background:white; padding:2px 3px; vertical-align:middle; }""",
    """.ticker-logos { display:inline-flex; align-items:center; gap:8px; vertical-align:middle; flex-shrink:0; }
.ticker-logo  { width:56px; height:22px; object-fit:contain; border-radius:4px; background:white; padding:2px 3px; vertical-align:middle; flex-shrink:0; }""",
))


def main():
    erreurs = 0
    for chemin, ancien, nouveau in remplacements:
        try:
            with open(chemin, "r", encoding="utf-8") as f:
                contenu = f.read()
        except FileNotFoundError:
            print(f"❌ Fichier introuvable : {chemin}")
            erreurs += 1
            continue

        if ancien not in contenu:
            print(f"⚠️   Bloc déjà modifié ou introuvable dans {chemin} (ignoré)")
            continue

        contenu = contenu.replace(ancien, nouveau, 1)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(contenu)
        print(f"✅ {chemin} mis à jour")

    if erreurs:
        print(f"\n{erreurs} fichier(s) introuvable(s) — vérifie que tu es bien à la racine du projet.")
        sys.exit(1)
    print("\n🌸 Terminé. Vérifie avec : git --no-pager diff")


if __name__ == "__main__":
    main()
