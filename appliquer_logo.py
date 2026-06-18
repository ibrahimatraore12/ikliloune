#!/usr/bin/env python3
"""
appliquer_logo.py — Remplace le logo SVG approximatif par le vrai logo
officiel IKLILOUNE partout où il apparaît (navbar, footer, login admin,
sidebar admin, page suivi) + favicon + image de partage réseaux sociaux.

À lancer UNE SEULE FOIS depuis la racine du projet (~/IKLILOUNE) :
    python3 appliquer_logo.py

Pré-requis : avoir déjà déposé ces 5 fichiers dans static/images/ :
    logo-icone.png, logo-complet.png, favicon-32.png,
    apple-touch-icon.png, og-image.jpg
"""
import sys

remplacements = []

# 1. Navbar boutique --------------------------------------------------
remplacements.append((
    "templates/boutique/index.html",
    """  <a class="nav-logo" href="/">
    <div class="logo-sphere">
      <!-- Logo cubique SVG identique à la maquette -->
      <svg width="38" height="38" viewBox="0 0 38 38" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <radialGradient id="bgN" cx="38%" cy="32%" r="65%">
            <stop offset="0%" stop-color="#FAD4DC"/>
            <stop offset="45%" stop-color="#F2AEBB"/>
            <stop offset="100%" stop-color="#A85870"/>
          </radialGradient>
          <filter id="glowN">
            <feGaussianBlur stdDeviation="0.7" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <linearGradient id="orN" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#F0C96B"/>
            <stop offset="50%" stop-color="#C9922A"/>
            <stop offset="100%" stop-color="#F0C96B"/>
          </linearGradient>
        </defs>
        <circle cx="19" cy="19" r="18" fill="url(#bgN)"/>
        <circle cx="19" cy="19" r="17" fill="none" stroke="url(#orN)" stroke-width="1.2" opacity="0.7"/>
        <g filter="url(#glowN)">
          <polygon points="19,8 29,14 19,20 9,14" fill="rgba(201,146,42,0.08)" stroke="url(#orN)" stroke-width="1.5" stroke-linejoin="round"/>
          <polygon points="9,14 19,20 19,32 9,26"  fill="rgba(201,146,42,0.04)" stroke="url(#orN)" stroke-width="1.5" stroke-linejoin="round"/>
          <polygon points="29,14 19,20 19,32 29,26" fill="rgba(240,201,107,0.06)" stroke="url(#orN)" stroke-width="1.5" stroke-linejoin="round"/>
          <circle cx="19" cy="8"  r="1.4" fill="#F0C96B"/>
          <circle cx="9"  cy="14" r="1.2" fill="#C9922A"/>
          <circle cx="29" cy="14" r="1.2" fill="#C9922A"/>
          <circle cx="19" cy="20" r="1.4" fill="#F0C96B"/>
          <circle cx="9"  cy="26" r="1.2" fill="#C9922A"/>
          <circle cx="29" cy="26" r="1.2" fill="#C9922A"/>
          <circle cx="19" cy="32" r="1.2" fill="#F0C96B"/>
        </g>
      </svg>
    </div>
    <div class="logo-textes">
      <span class="logo-nom">IKLILOUNE</span>
      <span class="logo-slogan">La Maison du Chic</span>
    </div>
  </a>""",
    """  <a class="nav-logo" href="/">
    <img src="{{ url_for('static', filename='images/logo-icone.png') }}" alt="IKLILOUNE" class="logo-img logo-img-nav">
    <div class="logo-textes">
      <span class="logo-nom">IKLILOUNE</span>
      <span class="logo-slogan">La Maison du Chic</span>
    </div>
  </a>""",
))

# 2. Footer -------------------------------------------------------------
remplacements.append((
    "templates/partials/footer.html",
    """        <div class="footer-logo">
          <svg width="40" height="40" viewBox="0 0 44 44" fill="none">
            <defs>
              <radialGradient id="bgF" cx="38%" cy="32%" r="65%">
                <stop offset="0%" stop-color="#FAD4DC"/>
                <stop offset="45%" stop-color="#F2AEBB"/>
                <stop offset="100%" stop-color="#A85870"/>
              </radialGradient>
              <linearGradient id="orF" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#F0C96B"/>
                <stop offset="50%" stop-color="#C9922A"/>
                <stop offset="100%" stop-color="#F0C96B"/>
              </linearGradient>
            </defs>
            <circle cx="22" cy="22" r="21" fill="url(#bgF)"/>
            <circle cx="22" cy="22" r="20" fill="none" stroke="url(#orF)" stroke-width="1.4" opacity="0.7"/>
            <polygon points="22,9 33,16 22,23 11,16"  fill="none" stroke="url(#orF)" stroke-width="1.6" stroke-linejoin="round"/>
            <polygon points="11,16 22,23 22,37 11,30" fill="none" stroke="url(#orF)" stroke-width="1.6" stroke-linejoin="round"/>
            <polygon points="33,16 22,23 22,37 33,30" fill="none" stroke="url(#orF)" stroke-width="1.6" stroke-linejoin="round"/>
            <circle cx="22" cy="9"  r="1.6" fill="#F0C96B"/>
            <circle cx="11" cy="16" r="1.4" fill="#C9922A"/>
            <circle cx="33" cy="16" r="1.4" fill="#C9922A"/>
            <circle cx="22" cy="23" r="1.6" fill="#F0C96B"/>
            <circle cx="11" cy="30" r="1.4" fill="#C9922A"/>
            <circle cx="33" cy="30" r="1.4" fill="#C9922A"/>
            <circle cx="22" cy="37" r="1.4" fill="#F0C96B"/>
          </svg>
          <div>
            <div class="footer-logo-nom">IKLILOUNE</div>
            <div class="footer-logo-slogan">La Maison du Chic</div>
          </div>
        </div>""",
    """        <div class="footer-logo">
          <img src="{{ url_for('static', filename='images/logo-icone.png') }}" alt="IKLILOUNE" class="logo-img logo-img-footer">
          <div>
            <div class="footer-logo-nom">IKLILOUNE</div>
            <div class="footer-logo-slogan">La Maison du Chic</div>
          </div>
        </div>""",
))

# 3. Login admin (logo complet, bien mis en evidence) -------------------
remplacements.append((
    "templates/admin/login.html",
    """    <div class="login-logo">
      <svg width="52" height="52" viewBox="0 0 52 52" fill="none">
        <defs>
          <radialGradient id="bgL" cx="38%" cy="32%" r="65%">
            <stop offset="0%" stop-color="#FAD4DC"/>
            <stop offset="45%" stop-color="#F2AEBB"/>
            <stop offset="100%" stop-color="#A85870"/>
          </radialGradient>
          <linearGradient id="orL" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#F0C96B"/>
            <stop offset="100%" stop-color="#C9922A"/>
          </linearGradient>
        </defs>
        <circle cx="26" cy="26" r="25" fill="url(#bgL)"/>
        <circle cx="26" cy="26" r="24" fill="none" stroke="url(#orL)" stroke-width="1.5" opacity="0.7"/>
        <polygon points="26,10 38,18 26,26 14,18" fill="rgba(201,146,42,0.1)" stroke="url(#orL)" stroke-width="1.8" stroke-linejoin="round"/>
        <polygon points="14,18 26,26 26,42 14,34" fill="rgba(201,146,42,0.05)" stroke="url(#orL)" stroke-width="1.8" stroke-linejoin="round"/>
        <polygon points="38,18 26,26 26,42 38,34" fill="rgba(240,201,107,0.07)" stroke="url(#orL)" stroke-width="1.8" stroke-linejoin="round"/>
        <circle cx="26" cy="10" r="2" fill="#F0C96B"/>
        <circle cx="14" cy="18" r="1.6" fill="#C9922A"/>
        <circle cx="38" cy="18" r="1.6" fill="#C9922A"/>
        <circle cx="26" cy="26" r="2" fill="#F0C96B"/>
        <circle cx="26" cy="42" r="1.6" fill="#F0C96B"/>
      </svg>
    </div>

    <h1 class="login-titre">IKLILOUNE</h1>
    <p class="login-sous">Accès administration · Privé et exclusif</p>""",
    """    <div class="login-logo">
      <img src="{{ url_for('static', filename='images/logo-complet.png') }}" alt="IKLILOUNE — Maison du Chic" class="logo-img logo-img-login">
    </div>

    <p class="login-sous">Accès administration · Privé et exclusif</p>""",
))

# 4. Sidebar admin --------------------------------------------------------
remplacements.append((
    "templates/admin/dashboard.html",
    """    <div class="sidebar-logo">
      <!-- Mini logo SVG IKLILOUNE -->
      <svg width="28" height="28" viewBox="0 0 44 44" fill="none" style="flex-shrink:0">
        <circle cx="22" cy="22" r="21" fill="#1A1A2E"/>
        <polygon points="22,9 33,16 22,23 11,16"  fill="none" stroke="#F0C96B" stroke-width="1.6" stroke-linejoin="round"/>
        <polygon points="11,16 22,23 22,37 11,30" fill="none" stroke="#F0C96B" stroke-width="1.6" stroke-linejoin="round"/>
        <polygon points="33,16 22,23 22,37 33,30" fill="none" stroke="#F0C96B" stroke-width="1.6" stroke-linejoin="round"/>
      </svg>
      <div>
        <span class="sidebar-logo-nom">IKLILOUNE</span>
        <span class="sidebar-logo-role">Administration</span>
      </div>
    </div>""",
    """    <div class="sidebar-logo">
      <img src="{{ url_for('static', filename='images/logo-icone.png') }}" alt="IKLILOUNE" class="logo-img logo-img-sidebar">
      <div>
        <span class="sidebar-logo-nom">IKLILOUNE</span>
        <span class="sidebar-logo-role">Administration</span>
      </div>
    </div>""",
))

# 5. Page suivi de commande -----------------------------------------------
remplacements.append((
    "templates/boutique/suivi.html",
    """  <a class="nav-logo" href="/">
    <svg width="36" height="36" viewBox="0 0 38 38" fill="none">
      <defs>
        <radialGradient id="bgS" cx="38%" cy="32%" r="65%"><stop offset="0%" stop-color="#FAD4DC"/><stop offset="45%" stop-color="#F2AEBB"/><stop offset="100%" stop-color="#A85870"/></radialGradient>
        <linearGradient id="orS" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#F0C96B"/><stop offset="50%" stop-color="#C9922A"/><stop offset="100%" stop-color="#F0C96B"/></linearGradient>
      </defs>
      <circle cx="19" cy="19" r="18" fill="url(#bgS)"/>
      <polygon points="19,8 29,14 19,20 9,14" fill="none" stroke="url(#orS)" stroke-width="1.5"/>
      <polygon points="9,14 19,20 19,32 9,26"  fill="none" stroke="url(#orS)" stroke-width="1.5"/>
      <polygon points="29,14 19,20 19,32 29,26" fill="none" stroke="url(#orS)" stroke-width="1.5"/>
    </svg>
    <div class="logo-textes">
      <span class="logo-nom">IKLILOUNE</span>
      <span class="logo-slogan">La Maison du Chic</span>
    </div>
  </a>""",
    """  <a class="nav-logo" href="/">
    <img src="{{ url_for('static', filename='images/logo-icone.png') }}" alt="IKLILOUNE" class="logo-img logo-img-nav">
    <div class="logo-textes">
      <span class="logo-nom">IKLILOUNE</span>
      <span class="logo-slogan">La Maison du Chic</span>
    </div>
  </a>""",
))

# 6. Pop-up capture email -5% (oubliée la 1ère fois) ----------------------
remplacements.append((
    "templates/boutique/index.html",
    """      <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
        <defs>
          <radialGradient id="bgPop" cx="38%" cy="32%" r="65%">
            <stop offset="0%" stop-color="#FAD4DC"/>
            <stop offset="45%" stop-color="#F2AEBB"/>
            <stop offset="100%" stop-color="#A85870"/>
          </radialGradient>
          <linearGradient id="orPop" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#F0C96B"/>
            <stop offset="100%" stop-color="#C9922A"/>
          </linearGradient>
        </defs>
        <circle cx="28" cy="28" r="27" fill="url(#bgPop)"/>
        <circle cx="28" cy="28" r="26" fill="none" stroke="url(#orPop)" stroke-width="1.3" opacity="0.7"/>
        <polygon points="28,11 38,17 28,23 18,17" fill="rgba(201,146,42,0.1)" stroke="url(#orPop)" stroke-width="1.5" stroke-linejoin="round"/>
        <polygon points="18,17 28,23 28,35 18,29" fill="rgba(201,146,42,0.05)" stroke="url(#orPop)" stroke-width="1.5" stroke-linejoin="round"/>
        <polygon points="38,17 28,23 28,35 38,29" fill="rgba(240,201,107,0.07)" stroke="url(#orPop)" stroke-width="1.5" stroke-linejoin="round"/>
        <circle cx="28" cy="11" r="1.8" fill="#F0C96B"/>
        <circle cx="18" cy="17" r="1.5" fill="#C9922A"/>
        <circle cx="38" cy="17" r="1.5" fill="#C9922A"/>
        <circle cx="28" cy="23" r="1.8" fill="#F0C96B"/>
        <circle cx="28" cy="35" r="1.5" fill="#F0C96B"/>
      </svg>
      <p class="popup-tag">Offre exclusive · 1ère commande</p>""",
    """      <img src="{{ url_for('static', filename='images/logo-icone.png') }}" alt="IKLILOUNE" class="logo-img logo-img-popup">
      <p class="popup-tag">Offre exclusive · 1ère commande</p>""",
))

# 7. Favicon dans base.html --------------------------------------------
remplacements.append((
    "templates/base.html",
    """  <!-- ── Favicon ─────────────────────────────────────────── -->
  <link rel="icon" type="image/svg+xml" href="{{ url_for('static', filename='images/favicon.svg') }}" onerror="this.remove()">""",
    """  <!-- ── Favicon ─────────────────────────────────────────── -->
  <link rel="icon" type="image/png" href="{{ url_for('static', filename='images/favicon-32.png') }}">
  <link rel="apple-touch-icon" href="{{ url_for('static', filename='images/apple-touch-icon.png') }}">""",
))

# 8. CSS — tailles du logo --------------------------------------------------
remplacements.append((
    "static/css/main.css",
    """.nav-logo { display:flex; align-items:center; gap:10px; }
.logo-sphere { flex-shrink:0; filter:drop-shadow(0 2px 6px rgba(242,174,187,0.4)); }""",
    """.nav-logo { display:flex; align-items:center; gap:10px; }
.logo-sphere { flex-shrink:0; filter:drop-shadow(0 2px 6px rgba(242,174,187,0.4)); }
.logo-img { display:block; object-fit:contain; }
.logo-img-nav { width:42px; height:42px; flex-shrink:0; filter:drop-shadow(0 2px 6px rgba(242,174,187,0.4)); }""",
))
remplacements.append((
    "static/css/main.css",
    """.footer-logo { display:flex; align-items:center; gap:12px; margin-bottom:16px; }""",
    """.footer-logo { display:flex; align-items:center; gap:12px; margin-bottom:16px; }
.logo-img-footer { width:44px; height:44px; flex-shrink:0; }""",
))
remplacements.append((
    "static/css/main.css",
    """.login-logo { margin-bottom:16px; filter:drop-shadow(0 4px 12px rgba(242,174,187,0.4)); }""",
    """.login-logo { margin-bottom:16px; filter:drop-shadow(0 4px 12px rgba(242,174,187,0.4)); }
.logo-img-login { width:150px; height:auto; margin:0 auto; }""",
))
remplacements.append((
    "static/css/main.css",
    """.sidebar-logo { padding:20px 16px 14px; border-bottom:1px solid rgba(201,146,42,0.15); }""",
    """.sidebar-logo { padding:20px 16px 14px; border-bottom:1px solid rgba(201,146,42,0.15); display:flex; align-items:center; gap:10px; }
.logo-img-sidebar { width:32px; height:32px; flex-shrink:0; }""",
))
remplacements.append((
    "static/css/main.css",
    """.popup-top {
  background:linear-gradient(135deg,var(--noir-chaud),#2D1F0A);
  padding:24px 28px; text-align:center; position:relative;
}""",
    """.popup-top {
  background:linear-gradient(135deg,var(--noir-chaud),#2D1F0A);
  padding:24px 28px; text-align:center; position:relative;
}
.logo-img-popup { width:56px; height:56px; margin:0 auto 4px; }""",
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
    print("\n🌸 Terminé. Vérifie avec : git --no-pager diff --stat")


if __name__ == "__main__":
    main()
