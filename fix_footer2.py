#!/usr/bin/env python3
"""
fix_footer2.py — Réécriture complète du footer + corrections
Exécuter depuis ~/IKLILOUNE : python fix_footer2.py
"""
import os, subprocess

BASE = os.getcwd()

# ══════════════════════════════════════════════════════════════
# 1. FOOTER complet réécrit (remplacement total du fichier)
# ══════════════════════════════════════════════════════════════
FOOTER = """\
<!-- ══ FOOTER IKLILOUNE ════════════════════════════════════ -->
<footer class="footer-ik">
  <div class="footer-grid">

    <!-- Colonne 1 : Marque + réseaux -->
    <div class="footer-col">
      <img src="{{ url_for('static', filename='images/logo-icone.png') }}"
           alt="IKLILOUNE" class="footer-logo">
      <p class="footer-slogan">La Maison du Chic</p>
      <p class="footer-desc">Parfums · Sacs · Vêtements · Chaussures<br>
         Collections Perles (Femme) &amp; Corail (Homme)</p>
      <div class="footer-socials">
        <a href="https://instagram.com/ikliloune" target="_blank" rel="noopener" aria-label="Instagram">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
          </svg>
        </a>
        <a href="https://wa.me/2250748956959" target="_blank" rel="noopener" aria-label="WhatsApp">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
          </svg>
        </a>
      </div>
    </div>

    <!-- Colonne 2 : Adresse boutique -->
    <div class="footer-col">
      <h4 class="footer-titre">🏪 Notre boutique</h4>
      <p class="footer-adresse">Songon 17</p>
      <p class="footer-adresse">Non loin de la Pharmacie de la Paix</p>
      <p class="footer-adresse" style="color:#c9a84c">Abidjan, Côte d'Ivoire</p>
      <p style="margin-top:6px">⏰ Lun–Sam : 9h–19h &nbsp;·&nbsp; Dim : 10h–17h</p>
      <p>📞 <a href="tel:+2250748956959">+225 07 48 95 69 59</a></p>
      <a class="footer-maps"
         href="https://www.google.com/maps/search/Songon+17+Abidjan+Pharmacie+de+la+Paix"
         target="_blank" rel="noopener">🗺️ Itinéraire Google Maps</a>
    </div>

    <!-- Colonne 3 : Zones de livraison -->
    <div class="footer-col">
      <h4 class="footer-titre">🚚 Livraison à domicile</h4>
      <ul class="footer-zones">
        <li>🟢 <strong>Zone 1</strong> — Songon / Yopougon<br>
            <span class="footer-zone-prix">1 500 FCFA</span></li>
        <li>🟡 <strong>Zone 2</strong> — Abidjan Centre<br>
            <span class="footer-zone-prix">2 500 FCFA</span></li>
        <li>🔴 <strong>Zone 3</strong> — Banlieue / Hors Abidjan<br>
            <span class="footer-zone-prix">3 500 FCFA</span></li>
      </ul>
      <p class="footer-collect">🏪 Retrait en magasin : GRATUIT</p>
    </div>

    <!-- Colonne 4 : Paiement -->
    <div class="footer-col">
      <h4 class="footer-titre">💳 Paiement accepté</h4>
      <div class="footer-pay">
        <img src="{{ url_for('static', filename='images/logos/orange-money.svg') }}" alt="Orange Money">
        <img src="{{ url_for('static', filename='images/logos/mtn-momo.svg') }}" alt="MTN MoMo">
        <img src="{{ url_for('static', filename='images/logos/wave.svg') }}" alt="Wave">
      </div>
      <p style="font-size:12px;margin-top:8px">Paiement à la livraison<br>ou au retrait en magasin</p>
    </div>

  </div>

  <!-- Carte Google Maps compacte -->
  <div class="footer-map-wrap">
    <iframe
      title="IKLILOUNE — Localisation Songon Abidjan"
      src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15894.8!2d-4.0819!3d5.3485!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xfc1ebcc7e4189a7%3A0x7e5e8a6b0000001!2sSongon%2C%20Abidjan!5e0!3m2!1sfr!2sci!4v1700000000000"
      width="100%" height="120"
      style="border:0;border-radius:8px;opacity:.85;display:block"
      allowfullscreen="" loading="lazy"
      referrerpolicy="no-referrer-when-downgrade">
    </iframe>
  </div>

  <div class="footer-bas">
    <p>© 2026 IKLILOUNE — La Maison du Chic · Tous droits réservés · Abidjan, Côte d'Ivoire</p>
  </div>
</footer>
"""

footer_path = os.path.join(BASE, "templates/partials/footer.html")
with open(footer_path, "w", encoding="utf-8") as f:
    f.write(FOOTER)
print("  ✅ footer.html réécrit complètement")

# ══════════════════════════════════════════════════════════════
# 2. CSS — footer_adresse bien visible
# ══════════════════════════════════════════════════════════════
CSS_EXTRA = """
/* Footer — adresse bien visible */
.footer-adresse { color: #fff !important; font-size: 13px !important;
  font-weight: 500; opacity: 1 !important; }
.footer-collect { font-size: 12px; color: #aaa; margin-top: 10px; }
.footer-zone-prix { color: #c9a84c; font-size: 11px; }
.footer-map-wrap  { max-width: 1200px; margin: 0 auto 20px;
  border-radius: 8px; overflow: hidden; }
"""
css_path = os.path.join(BASE, "static/css/main.css")
with open(css_path, "a", encoding="utf-8") as f:
    f.write(CSS_EXTRA)
print("  ✅ CSS adresse visible")

# ══════════════════════════════════════════════════════════════
# 3. Git commit + push
# ══════════════════════════════════════════════════════════════
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: footer adresse bien visible + carte compacte 120px"', shell=True)
subprocess.run("git push origin main", shell=True)
print("\n  ✅ Done — redémarre : python main.py")
