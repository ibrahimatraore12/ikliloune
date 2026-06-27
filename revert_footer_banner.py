#!/usr/bin/env python3
"""
revert_footer_banner.py
Supprime la bannière magasin + remet un footer simple
Exécuter depuis ~/IKLILOUNE : python revert_footer_banner.py
"""
import os, re, subprocess

BASE = os.getcwd()

def _read(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return f.read()

def _write(p, c):
    with open(os.path.join(BASE, p), "w", encoding="utf-8") as f:
        f.write(c)

# ══════════════════════════════════════════════════════════════
# 1. index.html — supprimer TOUTES les bannières magasin
# ══════════════════════════════════════════════════════════════
idx = _read("templates/boutique/index.html")

# Supprimer tout bloc banniere-magasin (avec ou sans doublons)
idx = re.sub(
    r'<!-- ══ BANNIÈRE MAGASIN .*?<!-- ══ BARRE FILTRES',
    '<!-- ══ BARRE FILTRES',
    idx,
    flags=re.DOTALL
)

_write("templates/boutique/index.html", idx)
print("  ✅ Bannière magasin supprimée de index.html")

# ══════════════════════════════════════════════════════════════
# 2. footer.html — footer simple avec adresse + map petite
# ══════════════════════════════════════════════════════════════
FOOTER_SIMPLE = """\
<!-- ══ FOOTER IKLILOUNE ════════════════════════════════════ -->
<footer class="footer-ik">
  <div class="footer-grid">

    <!-- Marque -->
    <div class="footer-col">
      <img src="{{ url_for('static', filename='images/logo-icone.png') }}"
           alt="IKLILOUNE" class="footer-logo">
      <p class="footer-slogan">La Maison du Chic</p>
      <p class="footer-desc">
        Parfums · Sacs · Vêtements · Chaussures<br>
        Collections Perles (Femme) &amp; Corail (Homme)
      </p>
    </div>

    <!-- Adresse boutique -->
    <div class="footer-col">
      <h4 class="footer-titre">🏪 Où nous trouver ?</h4>
      <p class="f-addr">📍 Songon 17</p>
      <p class="f-addr">Non loin de la Pharmacie de la Paix</p>
      <p class="f-addr" style="color:#c9a84c;font-weight:700">Abidjan, Côte d'Ivoire</p>
      <p style="margin-top:8px;font-size:12px">⏰ Lun–Sam : 9h–19h &nbsp;·&nbsp; Dim : 10h–17h</p>
      <p style="font-size:12px">📞 <a href="tel:+2250748956959">+225 07 48 95 69 59</a></p>
      <a class="footer-maps"
         href="https://www.google.com/maps/search/Songon+17+Abidjan+Pharmacie+de+la+Paix"
         target="_blank" rel="noopener">🗺️ Itinéraire</a>
    </div>

    <!-- Livraison -->
    <div class="footer-col">
      <h4 class="footer-titre">🚚 Livraison</h4>
      <ul class="footer-zones">
        <li>🟢 <strong>Zone 1</strong> — Songon / Yopougon &nbsp;<span>1 500 F</span></li>
        <li>🟡 <strong>Zone 2</strong> — Abidjan Centre &nbsp;<span>2 500 F</span></li>
        <li>🔴 <strong>Zone 3</strong> — Banlieue &nbsp;<span>3 500 F</span></li>
      </ul>
      <p style="font-size:11px;color:#aaa;margin-top:8px">🏪 Retrait magasin : GRATUIT</p>
    </div>

    <!-- Paiement -->
    <div class="footer-col">
      <h4 class="footer-titre">💳 Paiement</h4>
      <div class="footer-pay">
        <img src="{{ url_for('static', filename='images/logos/orange-money.svg') }}" alt="Orange Money">
        <img src="{{ url_for('static', filename='images/logos/mtn-momo.svg') }}" alt="MTN MoMo">
        <img src="{{ url_for('static', filename='images/logos/wave.svg') }}" alt="Wave">
      </div>
      <p style="font-size:11px;color:#aaa;margin-top:8px">À la livraison ou au retrait</p>
    </div>

  </div>

  <!-- Carte compacte -->
  <div class="footer-map-wrap">
    <iframe
      title="IKLILOUNE Localisation"
      src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15894.8!2d-4.0819!3d5.3485!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xfc1ebcc7e4189a7%3A0x7e5e8a6b0000001!2sSongon%2C%20Abidjan!5e0!3m2!1sfr!2sci!4v1700000000000"
      width="100%" height="110"
      style="border:0;border-radius:6px;display:block"
      allowfullscreen="" loading="lazy"
      referrerpolicy="no-referrer-when-downgrade">
    </iframe>
  </div>

  <div class="footer-bas">
    <p>© 2026 IKLILOUNE — La Maison du Chic &nbsp;·&nbsp; Abidjan, Côte d'Ivoire</p>
  </div>
</footer>
"""

_write("templates/partials/footer.html", FOOTER_SIMPLE)
print("  ✅ footer.html réécrit (simple et propre)")

# ══════════════════════════════════════════════════════════════
# 3. CSS — quelques règles propres pour le footer
# ══════════════════════════════════════════════════════════════
CSS = """
/* ── Footer IKLILOUNE ─────────────────────────────────────── */
.footer-ik{background:#111;color:#ccc;padding:40px 24px 0;margin-top:32px}
.footer-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:28px;max-width:1200px;margin:0 auto 28px}
.footer-col{display:flex;flex-direction:column;gap:5px}
.footer-logo{height:38px;width:auto;margin-bottom:4px;filter:brightness(1.5)}
.footer-slogan{font-family:'Playfair Display',serif;font-size:13px;color:#c9a84c;margin:0}
.footer-desc{font-size:11px;opacity:.6;line-height:1.6}
.footer-titre{font-size:13px;font-weight:700;color:#fff;margin:0 0 8px}
.footer-col p{font-size:12px;opacity:.75;margin:2px 0}
.footer-col a{color:#c9a84c;text-decoration:none}
.footer-col a:hover{text-decoration:underline}
.f-addr{font-size:13px !important;color:#fff !important;opacity:1 !important;font-weight:500}
.footer-maps{display:inline-block;background:#c9a84c18;color:#c9a84c !important;border:1px solid #c9a84c44;border-radius:16px;padding:4px 12px;font-size:11px;font-weight:600;margin-top:6px;text-decoration:none !important}
.footer-zones{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;font-size:12px}
.footer-zones span{color:#c9a84c;font-size:11px}
.footer-pay{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:4px}
.footer-pay img{height:26px;width:auto;filter:brightness(1.8)}
.footer-map-wrap{max-width:1200px;margin:0 auto 20px;border-radius:6px;overflow:hidden}
.footer-bas{text-align:center;padding:14px 0 18px;border-top:1px solid #222;font-size:11px;opacity:.4}
"""

css_path = os.path.join(BASE, "static/css/main.css")
content = _read("static/css/main.css")

# Retirer les anciens blocs footer/bannière si présents
content = re.sub(r'/\* ══+\s*(?:BANNIÈRE MAGASIN|FOOTER IKLILOUNE|CLICK&COLLECT).*?(?=/\* ══|$)', '', content, flags=re.DOTALL)
content = re.sub(r'/\* Footer map compact \*/.*?(?=\n/\*|$)', '', content, flags=re.DOTALL)
content = re.sub(r'/\* Footer — adresse.*?(?=\n/\*|$)', '', content, flags=re.DOTALL)

content = content.rstrip() + "\n" + CSS
_write("static/css/main.css", content)
print("  ✅ CSS footer propre (anciens blocs supprimés)")

# ══════════════════════════════════════════════════════════════
# 4. Git commit + push
# ══════════════════════════════════════════════════════════════
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: suppr banniere dupliquee + footer propre avec adresse + carte compacte"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n  ✅ Done. Redémarre : python main.py")
