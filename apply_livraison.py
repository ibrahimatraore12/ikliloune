#!/usr/bin/env python3
"""
apply_livraison.py — IKLILOUNE
Click&Collect + Livraison zones + Bannière magasin + Footer adresse
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exécuter depuis ~/IKLILOUNE avec l'env activé :
    python apply_livraison.py
"""
import os, subprocess

BASE = os.getcwd()

def _read(path):
    with open(os.path.join(BASE, path), "r", encoding="utf-8") as f:
        return f.read()

def _write(path, content):
    full = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full) if os.path.dirname(full) else ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

def patch(path, old, new, label=""):
    try:
        c = _read(path)
    except FileNotFoundError:
        print(f"  ❌ {path} introuvable"); return
    if old not in c:
        print(f"  ⚠️  Pattern non trouvé — {label or path}"); return
    _write(path, c.replace(old, new, 1))
    print(f"  ✅ {label or path}")

def write(path, content):
    _write(path, content)
    print(f"  📄 {path}")

def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    if r.returncode == 0:
        print(f"  ✅ {cmd}")
    else:
        print(f"  ⚠️  {cmd}\n     {out[:120]}")

print("\n" + "="*62)
print("  IKLILOUNE — Click&Collect + Livraison + Bannière + Footer")
print("="*62 + "\n")

# ═══════════════════════════════════════════════════════════════
# 1. MODÈLE Commande — ajout champs livraison
# ═══════════════════════════════════════════════════════════════
patch(
    "backend/models/commande.py",
    "    code_promo_utilise = db.Column(db.String(30), nullable=True)",
    """    code_promo_utilise = db.Column(db.String(30), nullable=True)
    # --- Mode de livraison ------------------------------------
    # "click_collect" | "livraison"
    mode_livraison    = db.Column(db.String(20), nullable=False, default="click_collect")
    # "zone_1" | "zone_2" | "zone_3"
    zone_livraison    = db.Column(db.String(20), nullable=True)
    # Frais en FCFA (0 si retrait magasin)
    frais_livraison   = db.Column(db.Integer, nullable=False, default=0)
    # Adresse de livraison précise
    adresse_livraison = db.Column(db.String(300), nullable=True)""",
    "Commande — 4 colonnes livraison"
)

patch(
    "backend/models/commande.py",
    '            "canal"              : self.canal,',
    '''            "canal"              : self.canal,
            "mode_livraison"     : self.mode_livraison or "click_collect",
            "zone_livraison"     : self.zone_livraison or "",
            "frais_livraison"    : self.frais_livraison or 0,
            "adresse_livraison"  : self.adresse_livraison or "",''',
    "Commande.vers_dict — champs livraison"
)

# ═══════════════════════════════════════════════════════════════
# 2. ROUTE /api/commande — logique livraison
# ═══════════════════════════════════════════════════════════════
patch(
    "backend/routes/commande.py",
    "    # ── 3. Conversion sécurisée des montants ──────────────────",
    """    # ── 2b. Mode de livraison ─────────────────────────────────
    ZONES = {
        "zone_1": {"label": "Songon / Yopougon",       "frais": 1500},
        "zone_2": {"label": "Abidjan Centre",           "frais": 2500},
        "zone_3": {"label": "Banlieue / Hors Abidjan", "frais": 3500},
    }
    mode_livraison = data.get("mode_livraison", "click_collect")
    if mode_livraison not in ("click_collect", "livraison"):
        mode_livraison = "click_collect"
    zone_livraison  = None
    frais_livraison = 0
    if mode_livraison == "livraison":
        zone_livraison = data.get("zone_livraison", "zone_1")
        if zone_livraison not in ZONES:
            zone_livraison = "zone_1"
        frais_livraison = ZONES[zone_livraison]["frais"]
    adresse_livraison = (data.get("adresse_livraison") or "").strip()

    # ── 3. Conversion sécurisée des montants ──────────────────""",
    "Route — zones livraison"
)

patch(
    "backend/routes/commande.py",
    "    # Cohérence : total doit être >= 0",
    """    # Ajouter frais de livraison au total
    total = total + frais_livraison

    # Cohérence : total doit être >= 0""",
    "Route — total + frais livraison"
)

patch(
    "backend/routes/commande.py",
    '            canal            = data.get("canal", "site_web"),',
    '''            canal            = data.get("canal", "site_web"),
            mode_livraison   = mode_livraison,
            zone_livraison   = zone_livraison,
            frais_livraison  = frais_livraison,
            adresse_livraison= adresse_livraison,''',
    "Route — Commande() champs livraison"
)

# ═══════════════════════════════════════════════════════════════
# 3. SERVICE WHATSAPP — message livraison
# ═══════════════════════════════════════════════════════════════
patch(
    "backend/services/commande_service.py",
    '    adresse = (getattr(commande, "client_adresse", "") or "À préciser").strip()',
    '''    # Livraison
    mode_liv    = getattr(commande, "mode_livraison",    "click_collect") or "click_collect"
    frais_liv   = getattr(commande, "frais_livraison",   0) or 0
    zone_liv    = getattr(commande, "zone_livraison",    "") or ""
    adresse_liv = (getattr(commande, "adresse_livraison", "") or "").strip()
    adresse_cli = (getattr(commande, "client_adresse",    "") or "").strip()
    adresse     = adresse_liv or adresse_cli or "À préciser"
    ZONES_LBL = {
        "zone_1": "Zone 1 — Songon / Yopougon",
        "zone_2": "Zone 2 — Abidjan Centre",
        "zone_3": "Zone 3 — Banlieue / Hors Abidjan",
    }
    if mode_liv == "click_collect":
        ligne_livraison = "🏪 *Retrait magasin* — Songon 17, près Pharmacie de la Paix\\n"
    else:
        zone_label = ZONES_LBL.get(zone_liv, zone_liv)
        ligne_livraison = (
            f"🚚 *Livraison* — {zone_label}\\n"
            f"📍 Adresse : {adresse}\\n"
            f"💸 Frais livraison : {_formater_montant(frais_liv)}\\n"
        )''',
    "Service WhatsApp — variables livraison"
)

patch(
    "backend/services/commande_service.py",
    '        f"📍 *Livraison :* {adresse}\\n"',
    '        f"{ligne_livraison}"',
    "Service WhatsApp — ligne livraison dans message"
)

# ═══════════════════════════════════════════════════════════════
# 4. INDEX.HTML — UI livraison dans le panier (checkout)
# ═══════════════════════════════════════════════════════════════
LIVRAISON_UI = '''    <!-- ── Mode de récupération ─────────────────────────────── -->
    <div class="checkout-label">🚗 Récupération de la commande</div>
    <div class="liv-opts" id="liv-opts">
      <label class="liv-opt selected" id="liv-collect"
             onclick="setModeLivraison(\'click_collect\')">
        <input type="radio" name="livraison" value="click_collect" checked>
        <span class="liv-icon">🏪</span>
        <div>
          <strong>Retrait magasin</strong>
          <small>Gratuit · Songon 17</small>
        </div>
      </label>
      <label class="liv-opt" id="liv-domicile"
             onclick="setModeLivraison(\'livraison\')">
        <input type="radio" name="livraison" value="livraison">
        <span class="liv-icon">🚚</span>
        <div>
          <strong>Livraison</strong>
          <small>1 500 – 3 500 FCFA</small>
        </div>
      </label>
    </div>
    <div id="zone-wrap" style="display:none;margin-top:8px">
      <select id="c-zone" class="checkout-input" onchange="majFraisLivraison()">
        <option value="zone_1">Zone 1 — Songon / Yopougon · 1 500 FCFA</option>
        <option value="zone_2">Zone 2 — Abidjan Centre · 2 500 FCFA</option>
        <option value="zone_3">Zone 3 — Banlieue / Hors Abidjan · 3 500 FCFA</option>
      </select>
      <input class="checkout-input" id="c-adresse-liv"
             placeholder="Adresse précise de livraison *"
             style="margin-top:8px">
      <div class="frais-liv-info" id="frais-info">
        🚚 Frais estimés : <strong id="frais-montant">1 500 FCFA</strong>
        <br><small>Confirmés dans la notification de validation</small>
      </div>
    </div>
    <!-- Ligne frais dans récap total -->
    <div class="panier-total" id="frais-ligne" style="display:none">
      <span>🚚 Livraison</span>
      <span id="frais-recap">0 FCFA</span>
    </div>
    '''

patch(
    "templates/boutique/index.html",
    '    <input class="checkout-input" id="c-adresse"',
    LIVRAISON_UI + '    <input class="checkout-input" id="c-adresse"',
    "index.html — UI livraison"
)

# ═══════════════════════════════════════════════════════════════
# 5. BANNIÈRE MAGASIN — avant la barre de filtres
# ═══════════════════════════════════════════════════════════════
BANNIERE = '''<!-- ══ BANNIÈRE MAGASIN ══════════════════════════════════════ -->
<div class="banniere-magasin">
  <div class="bm-photo">
    <img src="{{ url_for(\'static\', filename=\'images/boutique/magasin-banner.jpg\') }}"
         alt="Boutique IKLILOUNE" onerror="this.parentElement.style.display=\'none\'">
  </div>
  <div class="bm-contenu">
    <span class="bm-badge">🏪 Notre boutique</span>
    <h3>IKLILOUNE — La Maison du Chic</h3>
    <p>📍 Songon 17, non loin de la Pharmacie de la Paix &nbsp;·&nbsp; Abidjan, Côte d\'Ivoire</p>
    <p>⏰ Lun – Sam : 9h – 19h &nbsp;·&nbsp; Dim : 10h – 17h</p>
    <p>📞 <a href="tel:+2250748956959">+225 07 48 95 69 59</a>
       &nbsp;·&nbsp;
       <a href="https://wa.me/2250748956959" target="_blank">💬 WhatsApp</a></p>
    <a class="btn-itineraire"
       href="https://www.google.com/maps/search/Songon+17+Abidjan+Pharmacie+de+la+Paix"
       target="_blank" rel="noopener">🗺️ Itinéraire Google Maps</a>
  </div>
</div>
<!-- ══ BARRE FILTRES ═════════════════════════════════════════ -->
'''

patch(
    "templates/boutique/index.html",
    "<!-- ══ BARRE FILTRES ═════════════════════════════════════════ -->",
    BANNIERE,
    "index.html — bannière magasin"
)

# ═══════════════════════════════════════════════════════════════
# 6. FOOTER PARTIAL — adresse + zones + géolocalisation
# ═══════════════════════════════════════════════════════════════
FOOTER = '''<!-- ══ FOOTER IKLILOUNE ════════════════════════════════════════ -->
<footer class="footer-ik">
  <div class="footer-grid">

    <!-- Marque -->
    <div class="footer-col">
      <img src="{{ url_for(\'static\', filename=\'images/logo-icone.png\') }}"
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
        <a href="https://tiktok.com/@ikliloune" target="_blank" rel="noopener" aria-label="TikTok">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
          </svg>
        </a>
      </div>
    </div>

    <!-- Boutique -->
    <div class="footer-col">
      <h4 class="footer-titre">🏪 Notre boutique</h4>
      <p>Songon 17, non loin de<br>la Pharmacie de la Paix</p>
      <p>Abidjan, Côte d\'Ivoire</p>
      <p class="footer-horaires"><span>⏰</span>
         <span>Lun – Sam : 9h – 19h<br>Dimanche : 10h – 17h</span></p>
      <p>📞 <a href="tel:+2250748956959">+225 07 48 95 69 59</a></p>
      <a class="footer-maps"
         href="https://www.google.com/maps/search/Songon+17+Abidjan+Pharmacie+de+la+Paix"
         target="_blank" rel="noopener">🗺️ Voir sur Google Maps</a>
    </div>

    <!-- Livraison -->
    <div class="footer-col">
      <h4 class="footer-titre">🚚 Livraison à domicile</h4>
      <ul class="footer-zones">
        <li>🟢 <strong>Zone 1</strong> — Songon / Yopougon<br><span>1 500 FCFA</span></li>
        <li>🟡 <strong>Zone 2</strong> — Abidjan Centre<br><span>2 500 FCFA</span></li>
        <li>🔴 <strong>Zone 3</strong> — Banlieue / Hors Abidjan<br><span>3 500 FCFA</span></li>
      </ul>
      <p style="margin-top:10px;font-size:12px;opacity:.65">🏪 Retrait magasin : GRATUIT</p>
    </div>

    <!-- Paiement -->
    <div class="footer-col">
      <h4 class="footer-titre">💳 Paiement</h4>
      <div class="footer-pay">
        <img src="{{ url_for(\'static\', filename=\'images/logos/orange-money.svg\') }}" alt="Orange Money">
        <img src="{{ url_for(\'static\', filename=\'images/logos/mtn-momo.svg\') }}" alt="MTN MoMo">
        <img src="{{ url_for(\'static\', filename=\'images/logos/wave.svg\') }}" alt="Wave">
      </div>
      <p style="font-size:12px;opacity:.65;margin-top:8px">
        Paiement à la livraison<br>ou au retrait en magasin</p>
    </div>

  </div>

  <!-- Mini-carte Google Maps -->
  <div class="footer-map-wrap">
    <iframe
      title="IKLILOUNE — Localisation Songon Abidjan"
      src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d15894.8!2d-4.0819!3d5.3485!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0xfc1ebcc7e4189a7%3A0x7e5e8a6b0000001!2sSongon%2C%20Abidjan!5e0!3m2!1sfr!2sci!4v1700000000000"
      width="100%" height="200"
      style="border:0;border-radius:10px;opacity:.9"
      allowfullscreen="" loading="lazy"
      referrerpolicy="no-referrer-when-downgrade">
    </iframe>
  </div>

  <div class="footer-bas">
    <p>© 2026 IKLILOUNE — La Maison du Chic · Tous droits réservés</p>
    <p style="font-size:11px;opacity:.45;margin-top:4px">Abidjan · Côte d\'Ivoire</p>
  </div>
</footer>
'''

write("templates/partials/footer.html", FOOTER)

# ═══════════════════════════════════════════════════════════════
# 7. JS INLINE — fonctions livraison + injection payload
# ═══════════════════════════════════════════════════════════════
JS_BLOCK = '''<script>
/* ── Click&Collect / Livraison ─────────────────────────────── */
const FRAIS_ZONES = { zone_1: 1500, zone_2: 2500, zone_3: 3500 };
let _modeLiv  = 'click_collect';
let _zoneLiv  = 'zone_1';
let _fraisLiv = 0;

function setModeLivraison(mode) {
  _modeLiv = mode;
  document.querySelectorAll('.liv-opt').forEach(el => el.classList.remove('selected'));
  const showZone = mode === 'livraison';
  document.getElementById('liv-collect').classList.toggle('selected',  !showZone);
  document.getElementById('liv-domicile').classList.toggle('selected',  showZone);
  document.getElementById('zone-wrap').style.display   = showZone ? 'block' : 'none';
  document.getElementById('frais-ligne').style.display = showZone ? 'flex'  : 'none';
  majFraisLivraison();
}

function majFraisLivraison() {
  const zone = document.getElementById('c-zone');
  if (zone) _zoneLiv = zone.value;
  _fraisLiv = _modeLiv === 'livraison' ? (FRAIS_ZONES[_zoneLiv] || 0) : 0;
  const fmt = n => n.toLocaleString('fr-FR') + ' FCFA';
  const elMontant = document.getElementById('frais-montant');
  const elRecap   = document.getElementById('frais-recap');
  if (elMontant) elMontant.textContent = fmt(_fraisLiv);
  if (elRecap)   elRecap.textContent   = fmt(_fraisLiv);
  /* Tenter de déclencher le recalcul du total si la fonction existe */
  ['mettreAJourTotaux','majTotaux','recalculerTotaux','updateTotal'].forEach(fn => {
    if (typeof window[fn] === 'function') window[fn]();
  });
}

/* Intercepte le bouton Valider pour injecter livraison */
document.addEventListener('DOMContentLoaded', function () {
  const btn = document.querySelector('.btn-commander');
  if (!btn) return;
  btn.removeAttribute('onclick');
  btn.addEventListener('click', async function (e) {
    e.preventDefault();
    /* Validation adresse livraison obligatoire */
    if (_modeLiv === 'livraison') {
      const adLiv = (document.getElementById('c-adresse-liv')?.value || '').trim();
      if (!adLiv) {
        if (typeof afficherToast === 'function')
          afficherToast('⚠️ Veuillez saisir votre adresse de livraison.', 'erreur');
        else alert('Veuillez saisir votre adresse de livraison.');
        return;
      }
    }
    /* Données livraison accessibles globalement pour boutique.js */
    window.__livraison = {
      mode_livraison   : _modeLiv,
      zone_livraison   : _modeLiv === 'livraison' ? _zoneLiv : null,
      frais_livraison  : _fraisLiv,
      adresse_livraison: (document.getElementById('c-adresse-liv')?.value || '').trim(),
    };
    if (typeof validerCommande === 'function') await validerCommande();
  });
});
</script>
'''

patch(
    "templates/boutique/index.html",
    "<script src=\"{{ url_for('static', filename='js/boutique.js') }}\"></script>",
    "<script src=\"{{ url_for('static', filename='js/boutique.js') }}\"></script>\n" + JS_BLOCK,
    "index.html — JS livraison inline"
)

# ═══════════════════════════════════════════════════════════════
# 8. boutique.js — injecter __livraison dans le payload fetch
# ═══════════════════════════════════════════════════════════════
BJS = "static/js/boutique.js"
try:
    bjs = _read(BJS)
    if "frais_livraison" in bjs or "__livraison" in bjs:
        print(f"  ⏭️  boutique.js — livraison déjà présent")
    else:
        injected = False
        # Chercher le premier marqueur de fin de payload fetch
        for marker in ['"canal"', 'canal:', '"paiement"', 'paiement:']:
            idx = bjs.find(marker)
            if idx != -1:
                end_of_line = bjs.find('\n', idx)
                if end_of_line != -1:
                    injection = '\n        ...(window.__livraison || {}),'
                    bjs = bjs[:end_of_line] + injection + bjs[end_of_line:]
                    _write(BJS, bjs)
                    print(f"  ✅ boutique.js — payload livraison injecté (après '{marker}')")
                    injected = True
                    break
        if not injected:
            print(f"  ⚠️  boutique.js — marker non trouvé, ajout manuel nécessaire")
            print(f"       → Ajouter '...(window.__livraison || {{}}),' dans le payload fetch /api/commande")
except FileNotFoundError:
    print(f"  ❌ boutique.js introuvable")

# ═══════════════════════════════════════════════════════════════
# 9. CSS — livraison + bannière + footer
# ═══════════════════════════════════════════════════════════════
CSS = """

/* ══════════════════════════════════════════════════════════════
   CLICK&COLLECT / LIVRAISON
══════════════════════════════════════════════════════════════ */
.liv-opts {
  display: flex; gap: 8px; margin: 8px 0 4px;
}
.liv-opt {
  flex: 1; display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border: 2px solid #e0d8cc;
  border-radius: 12px; cursor: pointer; background: #faf7f2;
  transition: border-color .2s, background .2s;
}
.liv-opt input[type="radio"] { display: none; }
.liv-opt.selected { border-color: #c9a84c; background: #fdf8ee; }
.liv-opt:hover    { border-color: #c9a84c88; }
.liv-icon { font-size: 22px; }
.liv-opt strong { font-size: 12px; display: block; color: #1a1a1a; }
.liv-opt small  { font-size: 11px; color: #888; }
.frais-liv-info {
  background: #fff8e1; border: 1px solid #ffe082; border-radius: 8px;
  padding: 8px 12px; margin-top: 8px; font-size: 12px;
  color: #7a5c00; line-height: 1.6;
}

/* ══════════════════════════════════════════════════════════════
   BANNIÈRE MAGASIN
══════════════════════════════════════════════════════════════ */
.banniere-magasin {
  display: flex; align-items: stretch; background: #1a1a1a;
  min-height: 160px; overflow: hidden;
}
.bm-photo { width: 220px; flex-shrink: 0; overflow: hidden; }
.bm-photo img { width: 100%; height: 100%; object-fit: cover; opacity: .75; }
.bm-contenu { flex: 1; padding: 20px 28px; color: #fff; display: flex;
  flex-direction: column; justify-content: center; }
.bm-badge {
  display: inline-block; background: #c9a84c; color: #fff;
  font-size: 10px; font-weight: 700; letter-spacing: 1.5px;
  text-transform: uppercase; padding: 3px 12px; border-radius: 20px; margin-bottom: 8px;
}
.bm-contenu h3 {
  font-family: 'Playfair Display', serif; font-size: 20px;
  margin: 0 0 6px; color: #fff;
}
.bm-contenu p   { font-size: 13px; opacity: .85; margin: 3px 0; color: #eee; }
.bm-contenu a   { color: #c9a84c; text-decoration: none; }
.btn-itineraire {
  display: inline-block; background: #c9a84c; color: #fff !important;
  border-radius: 24px; padding: 7px 16px; font-size: 12px; font-weight: 700;
  margin-top: 10px; text-decoration: none !important; transition: background .2s;
  width: fit-content;
}
.btn-itineraire:hover { background: #b8973b; }
@media (max-width: 600px) {
  .banniere-magasin { flex-direction: column; }
  .bm-photo { width: 100%; min-height: 120px; }
}

/* ══════════════════════════════════════════════════════════════
   FOOTER IKLILOUNE
══════════════════════════════════════════════════════════════ */
.footer-ik { background: #111; color: #ccc; padding: 48px 24px 0; margin-top: 40px; }
.footer-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 32px; max-width: 1200px; margin: 0 auto 32px;
}
.footer-col    { display: flex; flex-direction: column; gap: 5px; }
.footer-logo   { height: 40px; width: auto; margin-bottom: 4px; filter: brightness(1.6); }
.footer-slogan { font-family: 'Playfair Display', serif; font-size: 14px; color: #c9a84c; margin: 0; }
.footer-desc   { font-size: 12px; opacity: .65; line-height: 1.6; }
.footer-titre  { font-size: 14px; font-weight: 700; color: #fff; margin: 0 0 8px; }
.footer-col p  { font-size: 12px; opacity: .7; margin: 2px 0; }
.footer-col a  { color: #c9a84c; text-decoration: none; }
.footer-col a:hover { text-decoration: underline; }
.footer-horaires { display: flex; gap: 8px; align-items: flex-start; }
.footer-maps {
  display: inline-block; background: #c9a84c18; color: #c9a84c !important;
  border: 1px solid #c9a84c44; border-radius: 20px;
  padding: 5px 14px; font-size: 11px; font-weight: 600;
  margin-top: 6px; text-decoration: none !important; width: fit-content;
}
.footer-zones { list-style: none; padding: 0; margin: 0; display: flex;
  flex-direction: column; gap: 10px; }
.footer-zones li { font-size: 12px; line-height: 1.5; }
.footer-zones span { color: #c9a84c; font-size: 11px; }
.footer-pay { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 4px; }
.footer-pay img { height: 28px; width: auto; filter: brightness(1.8) grayscale(.3); }
.footer-socials { display: flex; gap: 12px; margin-top: 8px; }
.footer-socials a { color: #888; transition: color .2s; }
.footer-socials a:hover { color: #c9a84c; }
.footer-map-wrap {
  max-width: 1200px; margin: 0 auto 24px;
  border-radius: 12px; overflow: hidden;
}
.footer-bas {
  text-align: center; padding: 16px 0 20px;
  border-top: 1px solid #2a2a2a; font-size: 12px; opacity: .45;
}
"""

css_path = os.path.join(BASE, "static/css/main.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()
    if "CLICK&COLLECT / LIVRAISON" not in css_content:
        with open(css_path, "a", encoding="utf-8") as f:
            f.write(CSS)
        print("  ✅ CSS — livraison + bannière + footer")
    else:
        print("  ⏭️  CSS — déjà présent")
else:
    print("  ❌ static/css/main.css introuvable")

# ═══════════════════════════════════════════════════════════════
# 10. MIGRATION DB (ajout colonnes livraison)
# ═══════════════════════════════════════════════════════════════
print("\n  📦 Migration base de données...")
migration_script = """
from main import creer_app
from backend.database import db
app = creer_app()
with app.app_context():
    # Ajouter les colonnes si elles n'existent pas (SQLite + PostgreSQL)
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('commandes')]
    with db.engine.connect() as conn:
        if 'mode_livraison' not in cols:
            conn.execute(text("ALTER TABLE commandes ADD COLUMN mode_livraison VARCHAR(20) NOT NULL DEFAULT 'click_collect'"))
            print('  + mode_livraison')
        if 'zone_livraison' not in cols:
            conn.execute(text("ALTER TABLE commandes ADD COLUMN zone_livraison VARCHAR(20)"))
            print('  + zone_livraison')
        if 'frais_livraison' not in cols:
            conn.execute(text("ALTER TABLE commandes ADD COLUMN frais_livraison INTEGER NOT NULL DEFAULT 0"))
            print('  + frais_livraison')
        if 'adresse_livraison' not in cols:
            conn.execute(text("ALTER TABLE commandes ADD COLUMN adresse_livraison VARCHAR(300)"))
            print('  + adresse_livraison')
        conn.commit()
    print('  DB mise à jour ✅')
"""
with open("/tmp/_migrate_liv.py", "w") as f:
    f.write(migration_script)
run("python /tmp/_migrate_liv.py")

# ═══════════════════════════════════════════════════════════════
# 11. DOSSIER BOUTIQUE IMAGE (placeholder)
# ═══════════════════════════════════════════════════════════════
boutique_dir = os.path.join(BASE, "static/images/boutique")
os.makedirs(boutique_dir, exist_ok=True)
readme = os.path.join(boutique_dir, "README.txt")
if not os.path.exists(readme):
    with open(readme, "w") as f:
        f.write("Placer ici une photo du magasin nommée: magasin-banner.jpg\n"
                "Taille recommandée: 440×320 px minimum\n")
    print("  📁 static/images/boutique/ créé — ajouter magasin-banner.jpg")

# ═══════════════════════════════════════════════════════════════
# 12. GIT COMMIT + PUSH
# ═══════════════════════════════════════════════════════════════
print("\n  📤 Git commit + push...")
run("git add -A")
run('git commit -m "feat: click&collect + livraison zones + banniere magasin + footer adresse + geoloc"')
run("git push origin main")

print("\n" + "="*62)
print("  ✅ Patch appliqué avec succès !")
print()
print("  🔧 Prochaine étape :")
print("     1. Redémarrer le serveur : python main.py")
print("     2. Ajouter une photo du magasin dans :")
print("        static/images/boutique/magasin-banner.jpg")
print("="*62 + "\n")
