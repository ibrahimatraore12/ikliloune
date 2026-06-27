#!/usr/bin/env python3
"""
add_magasin_features.py — IKLILOUNE
=====================================
AJOUTE :
  1. Corrige les colonnes dupliquées dans commande.py
  2. Ajoute generer_ticket_acheteur() dans commande_service.py
  3. Ajoute dans admin.py :
       - POST /admin/api/commande-magasin  (vente en boutique physique)
       - GET  /admin/api/ticket-wa/<cid>   (ticket WhatsApp acheteur)
  4. Patche dashboard.html :
       - Sidebar : "🛍️ Caisse Magasin" + "📋 Audit Stock"
       - Section commandes : bouton "Nouvelle vente"
       - Modal commande : bouton "Ticket acheteur WA"
       - Section sec-magasin (caisse boutique)
       - Section sec-stock-audit (historique mouvements)
       - Modal modal-magasin (saisie vente en magasin)
  5. Patche admin.js : fonctions JS pour les nouvelles sections + modals
  6. Git commit + push

Exécuter depuis ~/IKLILOUNE : python add_magasin_features.py
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
    elif new.strip()[:50] in c:
        print(f"  ⏭  Déjà appliqué — {label}")
        return True
    else:
        print(f"  ⚠️  Pattern non trouvé — {label}")
        return False


print("=" * 60)
print("  IKLILOUNE — Caisse Magasin + Ticket WhatsApp acheteur")
print("=" * 60)


# ══════════════════════════════════════════════════════════════
# 1. Corriger les colonnes dupliquées dans commande.py
# ══════════════════════════════════════════════════════════════
# Supprimer le second bloc de déclaration (doublon laissé par un patch précédent)
DOUBLE_COL_OLD = (
    "    adresse_livraison = db.Column(db.String(300), nullable=True)\n"
    "    # --- Mode de livraison ------------------------------------\n"
    "    # \"click_collect\" | \"livraison\"\n"
    "    mode_livraison    = db.Column(db.String(20), nullable=False, default=\"click_collect\")\n"
    "    # \"zone_1\" | \"zone_2\" | \"zone_3\"\n"
    "    zone_livraison    = db.Column(db.String(20), nullable=True)\n"
    "    # Frais en FCFA (0 si retrait magasin)\n"
    "    frais_livraison   = db.Column(db.Integer, nullable=False, default=0)\n"
    "    # Adresse de livraison précise\n"
    "    adresse_livraison = db.Column(db.String(300), nullable=True)\n"
    "\n"
    "    # --- Canal et paiement -------------------------------------"
)
DOUBLE_COL_NEW = (
    "    adresse_livraison = db.Column(db.String(300), nullable=True)\n"
    "\n"
    "    # --- Canal et paiement -------------------------------------"
)
_patch("backend/models/commande.py", DOUBLE_COL_OLD, DOUBLE_COL_NEW,
       "Suppression colonnes dupliquées dans commande.py")

# Corriger aussi les clés dupliquées dans vers_dict()
DOUBLE_DICT_OLD = (
    '            "mode_livraison"     : self.mode_livraison or "click_collect",\n'
    '            "zone_livraison"     : self.zone_livraison or "",\n'
    '            "frais_livraison"    : self.frais_livraison or 0,\n'
    '            "adresse_livraison"  : self.adresse_livraison or "",\n'
    '            "mode_livraison"     : self.mode_livraison or "click_collect",\n'
    '            "zone_livraison"     : self.zone_livraison or "",\n'
    '            "frais_livraison"    : self.frais_livraison or 0,\n'
    '            "adresse_livraison"  : self.adresse_livraison or "",\n'
    '            "mode_paiement"      : self.mode_paiement or "",'
)
DOUBLE_DICT_NEW = (
    '            "mode_livraison"     : self.mode_livraison or "click_collect",\n'
    '            "zone_livraison"     : self.zone_livraison or "",\n'
    '            "frais_livraison"    : self.frais_livraison or 0,\n'
    '            "adresse_livraison"  : self.adresse_livraison or "",\n'
    '            "mode_paiement"      : self.mode_paiement or "",'
)
_patch("backend/models/commande.py", DOUBLE_DICT_OLD, DOUBLE_DICT_NEW,
       "Suppression clés dupliquées dans vers_dict()")

# Ajouter "magasin" dans les canaux valides (commentaire)
_patch(
    "backend/models/commande.py",
    '    # "site_web" | "whatsapp"\n'
    '    canal           = db.Column(db.String(20), nullable=False, default="site_web")',
    '    # "site_web" | "whatsapp" | "magasin"\n'
    '    canal           = db.Column(db.String(20), nullable=False, default="site_web")',
    'Canal "magasin" ajouté dans commande.py'
)


# ══════════════════════════════════════════════════════════════
# 2. Ajouter generer_ticket_acheteur() dans commande_service.py
# ══════════════════════════════════════════════════════════════
TICKET_FN = '''

def generer_ticket_acheteur(commande) -> dict:
    """
    Génère un ticket/reçu formaté pour l'ACHETEUR via WhatsApp.
    Distinct de message_notification_statut() qui s'adresse au client
    pour un changement de statut.

    Ce ticket est envoyé :
    - À la confirmation d'une commande en ligne
    - Immédiatement après une vente en magasin (canal="magasin")

    Returns:
        dict: { "url": "https://wa.me/...", "texte": "..." }
    """
    # ── Articles ──────────────────────────────────────────────
    lignes = ""
    for a in commande.articles():
        nom    = a.get("nom", "Article")
        qty    = int(a.get("qty", a.get("quantite", a.get("qte", 1))))
        prix_u = a.get("prix_actuel", a.get("prix_unitaire", a.get("prix", 0)))
        coloris = a.get("coloris", a.get("couleur", ""))
        taille  = a.get("taille", a.get("pointure", ""))
        detail  = ""
        if coloris: detail += f" · {coloris}"
        if taille:  detail += f" · {taille}"
        lignes += f"  • {nom}{detail} ×{qty} = {_formater_montant(qty * prix_u)}\\n"

    if not lignes:
        lignes = "  • Articles commandés\\n"

    # ── Remise ────────────────────────────────────────────────
    ligne_remise = ""
    remise = getattr(commande, "remise_montant", 0) or 0
    if remise > 0:
        code = getattr(commande, "code_promo_utilise", "") or ""
        suffix = f" ({code})" if code else ""
        ligne_remise = f"🎁 Remise{suffix} : -{_formater_montant(remise)}\\n"

    # ── Livraison ─────────────────────────────────────────────
    mode_liv  = getattr(commande, "mode_livraison", "click_collect") or "click_collect"
    frais_liv = getattr(commande, "frais_livraison", 0) or 0
    canal     = getattr(commande, "canal", "site_web") or "site_web"

    if canal == "magasin":
        ligne_liv = "🏪 Achat en boutique — IKLILOUNE Songon 17\\n"
    elif mode_liv == "click_collect":
        ligne_liv = "🏪 Retrait magasin — Songon 17, près Pharmacie de la Paix\\n"
    else:
        ZONES_LBL = {
            "zone_1": "Zone 1 — Songon / Yopougon",
            "zone_2": "Zone 2 — Abidjan Centre",
            "zone_3": "Zone 3 — Banlieue / Hors Abidjan",
        }
        zone_label = ZONES_LBL.get(getattr(commande, "zone_livraison", ""), "")
        ligne_liv  = (
            f"🚚 Livraison {zone_label}\\n"
            f"   Frais : {_formater_montant(frais_liv)}\\n"
        )

    # ── Message complet ───────────────────────────────────────
    date_str = commande.cree_le.strftime("%d/%m/%Y à %H:%M") if commande.cree_le else "—"
    mode_pmt = getattr(commande, "mode_paiement", "") or ""
    paiement = LABELS_PAIEMENT.get(mode_pmt.lower(), mode_pmt or "—")

    texte = (
        f"🧾 *IKLILOUNE — TICKET D\'ACHAT*\\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        f"📋 Commande : *{commande.numero}*\\n"
        f"📅 Date : {date_str}\\n"
        f"👤 Client : {commande.client_nom}\\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        f"🛍️ *Articles :*\\n"
        f"{lignes}\\n"
        f"💰 Sous-total : {_formater_montant(commande.sous_total or commande.total)}\\n"
        f"{ligne_remise}"
    )
    if frais_liv > 0:
        texte += f"🚚 Livraison : {_formater_montant(frais_liv)}\\n"

    texte += (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\\n"
        f"💳 *TOTAL PAYÉ : {_formater_montant(commande.total)} FCFA*\\n"
        f"   Paiement : {paiement}\\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        f"{ligne_liv}\\n"
        f"🌸 *IKLILOUNE — La Maison du Chic*\\n"
        f"📍 Songon 17, près Pharmacie de la Paix\\n"
        f"📞 +225 07 48 95 69 59\\n\\n"
        f"Merci de votre confiance ! 🙏"
    )

    tel = _normaliser_telephone(commande.client_telephone)
    url = f"https://wa.me/{tel}?text={quote(texte)}"
    return {"url": url, "texte": texte}
'''

svc = _read("backend/services/commande_service.py")
if "generer_ticket_acheteur" not in svc:
    _write("backend/services/commande_service.py", svc.rstrip() + "\n" + TICKET_FN)
    print("  ✅ generer_ticket_acheteur() ajouté dans commande_service.py")
else:
    print("  ⏭  generer_ticket_acheteur déjà présente")


# ══════════════════════════════════════════════════════════════
# 3. Nouvelles routes admin : commande-magasin + ticket-wa
# ══════════════════════════════════════════════════════════════
ROUTES_MAGASIN = """

# ══════════════════════════════════════════════════════════════
# CAISSE MAGASIN — Ventes en boutique physique
# ══════════════════════════════════════════════════════════════

@admin_bp.route("/admin/api/commande-magasin", methods=["POST"])
@login_required
def creer_commande_magasin():
    \"\"\"
    Crée une vente en boutique physique (canal = "magasin").
    La commande est directement confirmée et le stock est décrémenté.

    Corps JSON :
    {
      "client_nom":    "Fatou Koné",
      "client_tel":    "+2250700000000",
      "articles":      [{"produit_id": 5, "quantite": 2}, ...],
      "mode_paiement": "orange_money"   ← optionnel
    }
    \"\"\"
    from backend.models.historique_stock import HistoriqueStock

    data = request.get_json() or {}

    client_nom = data.get("client_nom", "").strip()
    client_tel = data.get("client_tel", "").strip()
    articles_in = data.get("articles", [])

    if not client_nom or not client_tel:
        return jsonify({"erreur": "Nom et téléphone client obligatoires"}), 400
    if not articles_in:
        return jsonify({"erreur": "Aucun article sélectionné"}), 400

    try:
        import json as _json

        # ── Constituer le panier ─────────────────────────────
        articles_json_list = []
        sous_total = 0

        for item in articles_in:
            pid_  = item.get("produit_id")
            qty_  = int(item.get("quantite", item.get("qty", 1)))
            if not pid_ or qty_ <= 0:
                continue
            prod_ = db.session.get(Produit, pid_)
            if not prod_ or not prod_.actif:
                return jsonify({"erreur": f"Produit ID {pid_} introuvable ou inactif"}), 400
            if prod_.stock < qty_:
                return jsonify({
                    "erreur": f"Stock insuffisant pour '{prod_.nom}' "
                              f"(disponible : {prod_.stock}, demandé : {qty_})"
                }), 400

            prix_u = prod_.prix_actuel()
            articles_json_list.append({
                "id"          : prod_.id,
                "reference"   : prod_.reference,
                "nom"         : prod_.nom,
                "prix_actuel" : prix_u,
                "prix_unitaire": prix_u,
                "quantite"    : qty_,
                "qty"         : qty_,
                "photo"       : prod_.photo or "",
                "categorie"   : prod_.categorie,
            })
            sous_total += prix_u * qty_

        if not articles_json_list:
            return jsonify({"erreur": "Aucun article valide"}), 400

        # ── Créer la commande magasin ─────────────────────────
        commande = Commande(
            client_nom       = client_nom,
            client_telephone = client_tel,
            articles_json    = _json.dumps(articles_json_list, ensure_ascii=False),
            sous_total       = sous_total,
            remise_montant   = 0,
            total            = sous_total,
            canal            = "magasin",
            mode_livraison   = "click_collect",
            frais_livraison  = 0,
            statut           = "confirmee",
            mode_paiement    = data.get("mode_paiement", "a_definir"),
            notes_admin      = f"Vente en boutique — saisie par {current_user.email}",
        )
        db.session.add(commande)
        db.session.flush()  # obtenir l'ID avant le log

        # ── Décrémenter le stock ──────────────────────────────
        for item in articles_json_list:
            prod_ = db.session.get(Produit, item["id"])
            if prod_:
                avant_ = prod_.stock
                prod_.stock = max(0, prod_.stock - item["qty"])
                db.session.add(HistoriqueStock(
                    produit_id=prod_.id,
                    type_mouvement="vente_magasin",
                    quantite_avant=avant_,
                    quantite_apres=prod_.stock,
                    delta=prod_.stock - avant_,
                    commande_id=commande.id,
                    note=f"Vente boutique — {commande.numero}"
                ))

        # ── Historique statut ─────────────────────────────────
        db.session.add(HistoriqueStatut(
            commande_id  = commande.id,
            statut_avant = None,
            statut_apres = "confirmee",
            note         = "Vente créée et confirmée en boutique",
            modifie_par  = current_user.email,
        ))

        db.session.commit()

        # ── Générer le ticket WhatsApp acheteur ───────────────
        from backend.services.commande_service import generer_ticket_acheteur
        ticket = generer_ticket_acheteur(commande)

        print(f"🛍️ Vente magasin : {commande.numero} — {client_nom} — {sous_total} FCFA")
        return jsonify({
            "succes"    : True,
            "commande"  : commande.vers_dict(),
            "ticket_wa" : ticket,
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur creer_commande_magasin : {e}")
        return jsonify({"erreur": str(e)}), 500


@admin_bp.route("/admin/api/ticket-wa/<int:cid>")
@login_required
def api_ticket_whatsapp_acheteur(cid):
    \"\"\"
    Génère le ticket WhatsApp acheteur pour n'importe quelle commande.
    Utilisé par le bouton 'Envoyer ticket acheteur' dans le modal commande.
    \"\"\"
    from backend.services.commande_service import generer_ticket_acheteur
    commande = db.get_or_404(Commande, cid)
    ticket   = generer_ticket_acheteur(commande)
    return jsonify({"succes": True, **ticket})
"""

admin_content = _read("backend/routes/admin.py")
if "creer_commande_magasin" not in admin_content:
    _write("backend/routes/admin.py", admin_content.rstrip() + "\n" + ROUTES_MAGASIN)
    print("  ✅ Routes commande-magasin + ticket-wa ajoutées dans admin.py")
else:
    print("  ⏭  Routes magasin déjà présentes")


# ══════════════════════════════════════════════════════════════
# 4. Patch dashboard.html — sidebar + sections + modals
# ══════════════════════════════════════════════════════════════

# 4a. Ajouter items sidebar
_patch(
    "templates/admin/dashboard.html",
    '      <button class="sbar-item" onclick="adminSection(\'stats\', this)">📈 Statistiques</button>\n'
    '      <div class="sidebar-sep">',

    '      <button class="sbar-item" onclick="adminSection(\'stats\', this)">📈 Statistiques</button>\n'
    '      <button class="sbar-item" onclick="adminSection(\'magasin\', this)">🛍️ Caisse Magasin</button>\n'
    '      <button class="sbar-item" onclick="adminSection(\'stock-audit\', this)">📋 Audit Stock</button>\n'
    '      <div class="sidebar-sep">',

    "Sidebar : items Caisse Magasin + Audit Stock"
)

# 4b. Bouton "Nouvelle vente" dans sec-commandes
_patch(
    "templates/admin/dashboard.html",
    '        <div style="display:flex;gap:8px">\n'
    '          <a class="btn-primaire" href="/admin/api/export/commandes-excel"\n'
    '             style="background:var(--vert-dark,#1a7a4a)">📥 Export Excel</a>\n'
    '        </div>',

    '        <div style="display:flex;gap:8px">\n'
    '          <button class="btn-primaire" onclick="ouvrirModalMagasin()"\n'
    '                  style="background:#7b2d8b">🛍️ Nouvelle vente</button>\n'
    '          <a class="btn-primaire" href="/admin/api/export/commandes-excel"\n'
    '             style="background:var(--vert-dark,#1a7a4a)">📥 Export Excel</a>\n'
    '        </div>',

    "Bouton 'Nouvelle vente' dans sec-commandes"
)

# 4c. Bouton ticket acheteur dans le modal commande (zone wa-notif-zone)
_patch(
    "templates/admin/dashboard.html",
    '    <div class="modal-footer">\n'
    '      <button class="btn-annuler" onclick="fermerModalCommande()">Fermer</button>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>',   # fin modal-commande-bg

    '    <!-- Ticket WhatsApp acheteur -->\n'
    '    <div style="padding:10px 20px 16px">\n'
    '      <button class="btn-primaire" onclick="envoyerTicketWA(ADMIN.commandeId)"\n'
    '              style="background:#25D366;width:100%">\n'
    '        🧾 Envoyer le ticket d\'achat WhatsApp à l\'acheteur\n'
    '      </button>\n'
    '    </div>\n'
    '    <div class="modal-footer">\n'
    '      <button class="btn-annuler" onclick="fermerModalCommande()">Fermer</button>\n'
    '    </div>\n'
    '  </div>\n'
    '</div>',

    "Bouton ticket acheteur WA dans modal commande"
)

# 4d. Ajouter sections sec-magasin et sec-stock-audit avant </main>
SECTIONS_NOUVELLES = """
    <!-- ─────────────────────────────────────────────────────
         SECTION CAISSE MAGASIN — Ventes en boutique
    ───────────────────────────────────────────────────────── -->
    <section id="sec-magasin" class="admin-section">
      <div class="admin-top">
        <div>
          <h1 class="admin-page-titre">🛍️ Caisse Magasin</h1>
          <p class="admin-page-sous">Enregistrer une vente en boutique · Stock mis à jour automatiquement</p>
        </div>
        <button class="btn-primaire" onclick="ouvrirModalMagasin()">+ Nouvelle vente</button>
      </div>

      <!-- Dernières ventes magasin -->
      <div class="admin-table-wrap">
        <div class="admin-table-header"><h3>🏪 Dernières ventes en boutique</h3></div>
        <div class="table-scroll">
          <table class="admin-table">
            <thead><tr>
              <th>Numéro</th><th>Date</th><th>Client</th><th>Téléphone</th>
              <th>Articles</th><th>Total</th><th>Ticket</th>
            </tr></thead>
            <tbody id="tbody-magasin">
              <tr><td colspan="7" class="chargement-cell">Chargement...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>


    <!-- ─────────────────────────────────────────────────────
         SECTION AUDIT STOCK — Historique des mouvements
    ───────────────────────────────────────────────────────── -->
    <section id="sec-stock-audit" class="admin-section">
      <div class="admin-top">
        <div>
          <h1 class="admin-page-titre">📋 Audit Stock</h1>
          <p class="admin-page-sous">Traçabilité complète · Chaque mouvement est enregistré</p>
        </div>
      </div>

      <!-- Filtres -->
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
        <button class="filtre-btn active" onclick="filtrerAuditStock('',this)">Tous</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('vente',this)">🛒 Ventes</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('vente_magasin',this)">🏪 Magasin</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('ajustement_manuel',this)">✏️ Ajustements</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('annulation_commande',this)">↩️ Annulations</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('ajout_initial',this)">➕ Ajouts</button>
        <button class="filtre-btn" onclick="filtrerAuditStock('desactivation',this)">🗑️ Désactivations</button>
      </div>

      <div class="admin-table-wrap">
        <div class="table-scroll">
          <table class="admin-table" id="table-audit">
            <thead><tr>
              <th>Date</th><th>Type</th><th>Produit</th><th>Réf.</th>
              <th>Avant</th><th>Après</th><th>Delta</th>
              <th>Commande</th><th>Note</th>
            </tr></thead>
            <tbody id="tbody-audit">
              <tr><td colspan="9" class="chargement-cell">Chargement de l'audit...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

"""

html = _read("templates/admin/dashboard.html")
if "sec-magasin" not in html:
    html = html.replace("  </main>\n</div>", SECTIONS_NOUVELLES + "  </main>\n</div>", 1)
    _write("templates/admin/dashboard.html", html)
    print("  ✅ Sections sec-magasin + sec-stock-audit ajoutées")
else:
    print("  ⏭  Sections magasin/audit déjà présentes")


# 4e. Ajouter modal-magasin avant le TOAST
MODAL_MAGASIN = """
<!-- ══════════════════════════════════════════════════════════
     MODAL — Vente en magasin (Caisse boutique)
══════════════════════════════════════════════════════════════ -->
<div class="modal-bg" id="modal-magasin-bg">
  <div class="modal-box" style="max-width:600px">
    <div class="modal-header">
      <h2>🛍️ Nouvelle vente en boutique</h2>
      <button onclick="fermerModalMagasin()" aria-label="Fermer">✕</button>
    </div>
    <div class="modal-body">

      <!-- Client -->
      <div class="field-row">
        <div class="field-group">
          <label class="field-lbl">Nom du client *</label>
          <input class="field-input" id="mag-client-nom" placeholder="Fatou Koné">
        </div>
        <div class="field-group">
          <label class="field-lbl">Téléphone * (pour le ticket)</label>
          <div class="tel-wrap-admin">
            <span class="tel-prefix-admin">🇨🇮 +225</span>
            <input class="field-input tel-input-admin" id="mag-client-tel"
                   placeholder="07 00 00 00 00" type="tel" maxlength="10" inputmode="numeric"
                   oninput="this.value=this.value.replace(/\\D/g,'').slice(0,10)">
          </div>
        </div>
      </div>

      <!-- Paiement -->
      <div class="field-group">
        <label class="field-lbl">Mode de paiement</label>
        <select class="field-input" id="mag-paiement">
          <option value="especes">💵 Espèces</option>
          <option value="orange_money">🟠 Orange Money</option>
          <option value="mtn_momo">🟡 MTN MoMo</option>
          <option value="wave">🔵 Wave</option>
        </select>
      </div>

      <!-- Articles -->
      <div class="field-group">
        <label class="field-lbl">Articles vendus *</label>
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <select class="field-input" id="mag-produit-select" style="flex:3">
            <option value="">-- Sélectionner un article --</option>
          </select>
          <input class="field-input" type="number" id="mag-qty" value="1" min="1"
                 style="flex:1;max-width:80px" placeholder="Qté">
          <button class="btn-primaire" onclick="ajouterLigneMagasin()"
                  style="white-space:nowrap">+ Ajouter</button>
        </div>
        <div id="mag-lignes" style="border:1px solid #eee;border-radius:8px;min-height:60px;padding:8px">
          <p style="color:#aaa;font-size:12px;text-align:center;margin:12px 0">
            Aucun article ajouté
          </p>
        </div>
      </div>

      <!-- Total -->
      <div style="text-align:right;margin-top:12px;padding:12px;background:var(--ivoire);border-radius:8px">
        <strong style="font-size:18px">Total : <span id="mag-total-aff">0 FCFA</span></strong>
      </div>

    </div>
    <div class="modal-footer">
      <button class="btn-annuler" onclick="fermerModalMagasin()">Annuler</button>
      <button class="btn-primaire" onclick="validerVenteMagasin()" id="btn-vente-magasin">
        ✅ Enregistrer la vente
      </button>
    </div>
  </div>
</div>

"""

html2 = _read("templates/admin/dashboard.html")
if "modal-magasin-bg" not in html2:
    html2 = html2.replace(
        "<!-- ══════════════════════════════════════════════════════════\n"
        "     TOAST — Notifications flottantes",
        MODAL_MAGASIN +
        "<!-- ══════════════════════════════════════════════════════════\n"
        "     TOAST — Notifications flottantes",
        1
    )
    _write("templates/admin/dashboard.html", html2)
    print("  ✅ Modal vente magasin ajouté")
else:
    print("  ⏭  Modal magasin déjà présent")


# ══════════════════════════════════════════════════════════════
# 5. Patch admin.js — nouvelles fonctions JS
# ══════════════════════════════════════════════════════════════

# 5a. Mettre à jour adminSection() pour gérer les nouvelles sections
_patch(
    "static/js/admin.js",
    "    switch (section) {\n"
    "    case \"produits\":  chargerTableProduits();  break;\n"
    "    case \"commandes\": chargerTableCommandes(); break;\n"
    "    case \"clients\":   chargerTableClients();   break;\n"
    "    case \"bannieres\": chargerBannieres();       break;\n"
    "    case \"promos\":    chargerCodesPromo();      break;\n"
    "    case \"stats\":     /* graphiques déjà rendus côté serveur */ break;\n"
    "  }",

    "    switch (section) {\n"
    "    case \"produits\":     chargerTableProduits();   break;\n"
    "    case \"commandes\":    chargerTableCommandes();  break;\n"
    "    case \"clients\":      chargerTableClients();    break;\n"
    "    case \"bannieres\":    chargerBannieres();        break;\n"
    "    case \"promos\":       chargerCodesPromo();       break;\n"
    "    case \"stats\":        /* graphiques côté serveur */ break;\n"
    "    case \"magasin\":      chargerVentesMagasin();   break;\n"
    "    case \"stock-audit\":  chargerAuditStock();      break;\n"
    "  }",

    "adminSection() — cas magasin + stock-audit"
)

# 5b. Ajouter les nouvelles fonctions JS à la fin de admin.js
JS_ADDITIONS = """

// ══════════════════════════════════════════════════════════════
// CAISSE MAGASIN — Ventes en boutique
// ══════════════════════════════════════════════════════════════

const MAGASIN = { lignes: [], produits: [] };

/** Formate un montant entier en "28 500 FCFA". */
function fmtFCFA(n) {
  return new Intl.NumberFormat("fr-CI").format(n || 0) + " FCFA";
}

/** Charge la liste des produits actifs pour le select du modal magasin. */
async function _chargerProduitsMagasin() {
  if (MAGASIN.produits.length) return;
  try {
    const rep  = await fetch("/admin/api/produits");
    MAGASIN.produits = (await rep.json()).filter(p => p.actif && p.stock > 0);
    const sel = document.getElementById("mag-produit-select");
    if (!sel) return;
    sel.innerHTML = '<option value="">-- Sélectionner un article --</option>';
    MAGASIN.produits.forEach(p => {
      sel.innerHTML += `<option value="${p.id}" data-prix="${p.prix_actuel}" data-stock="${p.stock}">
        ${p.nom} — ${fmtFCFA(p.prix_actuel)} (stock: ${p.stock})
      </option>`;
    });
  } catch (e) { console.error("_chargerProduitsMagasin:", e); }
}

/** Ajoute une ligne article dans le panier magasin. */
function ajouterLigneMagasin() {
  const sel  = document.getElementById("mag-produit-select");
  const pid  = parseInt(sel?.value);
  const qty  = parseInt(document.getElementById("mag-qty")?.value || "1");
  if (!pid || qty < 1) { afficherToast("⚠️ Sélectionnez un article et une quantité valide", "⚠️"); return; }

  const opt   = sel.options[sel.selectedIndex];
  const prix  = parseFloat(opt.dataset.prix || "0");
  const stock = parseInt(opt.dataset.stock || "0");
  const nom   = opt.text.split(" — ")[0].trim();

  const existant = MAGASIN.lignes.find(l => l.id === pid);
  if (existant) {
    if (existant.qty + qty > stock) {
      afficherToast(`⚠️ Stock insuffisant (${stock} disponible)`, "⚠️"); return;
    }
    existant.qty += qty;
  } else {
    if (qty > stock) { afficherToast(`⚠️ Stock insuffisant (${stock} disponible)`, "⚠️"); return; }
    MAGASIN.lignes.push({ id: pid, nom, prix, qty, stock });
  }

  // Réinitialiser la sélection
  sel.value = "";
  document.getElementById("mag-qty").value = "1";
  _rendreLignesMagasin();
}

/** Retire une ligne du panier magasin. */
function retirerLigneMagasin(index) {
  MAGASIN.lignes.splice(index, 1);
  _rendreLignesMagasin();
}

/** Met à jour l'affichage des lignes et du total. */
function _rendreLignesMagasin() {
  const conteneur = document.getElementById("mag-lignes");
  if (!conteneur) return;
  if (!MAGASIN.lignes.length) {
    conteneur.innerHTML = '<p style="color:#aaa;font-size:12px;text-align:center;margin:12px 0">Aucun article ajouté</p>';
    document.getElementById("mag-total-aff").textContent = "0 FCFA";
    return;
  }
  let total = 0;
  conteneur.innerHTML = MAGASIN.lignes.map((l, i) => {
    const st = l.qty * l.prix;
    total += st;
    return `
      <div style="display:flex;align-items:center;gap:10px;padding:8px;border-bottom:1px solid #f0f0f0">
        <div style="flex:1;font-weight:600;font-size:13px">${l.nom}</div>
        <div style="font-size:12px;color:var(--brun-clair)">${fmtFCFA(l.prix)} × ${l.qty}</div>
        <div style="font-weight:700;color:var(--or-sombre)">${fmtFCFA(st)}</div>
        <button class="btn-mini btn-danger" onclick="retirerLigneMagasin(${i})">✕</button>
      </div>`;
  }).join("");
  document.getElementById("mag-total-aff").textContent = fmtFCFA(total);
}

/** Ouvre le modal de vente en magasin. */
async function ouvrirModalMagasin() {
  MAGASIN.lignes = [];
  _rendreLignesMagasin();
  ["mag-client-nom", "mag-client-tel"].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = "";
  });
  await _chargerProduitsMagasin();
  document.getElementById("modal-magasin-bg").classList.add("show");
}

function fermerModalMagasin() {
  document.getElementById("modal-magasin-bg").classList.remove("show");
  MAGASIN.lignes = [];
}

/** Valide la vente en magasin et crée la commande. */
async function validerVenteMagasin() {
  const nom = document.getElementById("mag-client-nom")?.value.trim();
  const telRaw = document.getElementById("mag-client-tel")?.value.trim() || "";
  const chiffres = telRaw.replace(/\\D/g, "");
  const tel = chiffres ? "+225" + chiffres : "";

  if (!nom || !tel) { afficherToast("⚠️ Nom et téléphone obligatoires", "⚠️"); return; }
  if (!MAGASIN.lignes.length) { afficherToast("⚠️ Aucun article dans le panier", "⚠️"); return; }

  const btn = document.getElementById("btn-vente-magasin");
  if (btn) { btn.disabled = true; btn.textContent = "Enregistrement..."; }

  try {
    const rep = await fetch("/admin/api/commande-magasin", {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({
        client_nom   : nom,
        client_tel   : tel,
        mode_paiement: document.getElementById("mag-paiement")?.value || "especes",
        articles     : MAGASIN.lignes.map(l => ({
          produit_id: l.id,
          quantite  : l.qty,
        })),
      })
    });
    const data = await rep.json();

    if (data.succes) {
      fermerModalMagasin();
      chargerVentesMagasin();
      chargerTableProduits();  // rafraîchir les stocks

      afficherToast(`✅ Vente ${data.commande.numero} enregistrée !`);

      // Ouvrir directement le ticket WA pour l'envoyer
      if (data.ticket_wa?.url) {
        if (confirm(`Vente enregistrée !\\n\\nEnvoyer le ticket WhatsApp à ${nom} ?`)) {
          window.open(data.ticket_wa.url, "_blank");
        }
      }
    } else {
      afficherToast("❌ " + (data.erreur || "Erreur"), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
    console.error("validerVenteMagasin:", e);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "✅ Enregistrer la vente"; }
  }
}

/** Charge les ventes magasin dans la section sec-magasin. */
async function chargerVentesMagasin() {
  const tbody = document.getElementById("tbody-magasin");
  if (!tbody) return;
  try {
    const rep  = await fetch("/admin/api/commandes");
    const data = (await rep.json()).filter(c => c.canal === "magasin");

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:32px;color:var(--brun-clair)">
        Aucune vente en boutique enregistrée.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(c => {
      const arts = (c.articles || []);
      const resumeArt = arts.slice(0,2).map(a => `${a.nom} ×${a.quantite||a.qty||1}`).join(", ")
                        + (arts.length > 2 ? ` +${arts.length-2}` : "");
      return `
        <tr>
          <td style="font-weight:700;font-family:monospace;color:var(--or-sombre)">${c.numero}</td>
          <td style="font-size:11px">${c.cree_le || "—"}</td>
          <td style="font-weight:600">${c.client_nom}</td>
          <td><a href="https://wa.me/${(c.client_telephone||"").replace(/[^0-9]/g,"")}"
                 target="_blank" class="lien-tel">${c.client_telephone}</a></td>
          <td style="font-size:11px;color:var(--brun-clair)">${resumeArt}</td>
          <td style="font-weight:700">${fmtFCFA(c.total)}</td>
          <td>
            <button class="btn-mini" style="background:#25D366;color:#fff"
                    onclick="envoyerTicketWA(${c.id})">🧾 Ticket WA</button>
          </td>
        </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="color:var(--rouge);padding:24px;text-align:center">
      ❌ Erreur</td></tr>`;
  }
}

/** Envoie le ticket WhatsApp acheteur pour une commande donnée. */
async function envoyerTicketWA(commandeId) {
  if (!commandeId) return;
  try {
    const rep  = await fetch(`/admin/api/ticket-wa/${commandeId}`);
    const data = await rep.json();
    if (data.url) {
      window.open(data.url, "_blank");
    } else {
      afficherToast("❌ Impossible de générer le ticket", "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
    console.error("envoyerTicketWA:", e);
  }
}


// ══════════════════════════════════════════════════════════════
// AUDIT STOCK — Historique des mouvements
// ══════════════════════════════════════════════════════════════

const ICONES_MOUVEMENT = {
  vente               : "🛒",
  vente_magasin       : "🏪",
  annulation_commande : "↩️",
  ajustement_manuel   : "✏️",
  ajout_initial       : "➕",
  desactivation       : "🗑️",
  reactivation        : "♻️",
  correction          : "🔧",
};

let _filtreAuditType = "";

/** Charge l'historique de stock avec le filtre actif. */
async function chargerAuditStock(type) {
  if (type !== undefined) _filtreAuditType = type;
  const tbody = document.getElementById("tbody-audit");
  if (!tbody) return;

  const url = _filtreAuditType
    ? `/admin/api/historique-stock?type=${_filtreAuditType}&limite=300`
    : "/admin/api/historique-stock?limite=300";

  try {
    const rep  = await fetch(url);
    const data = await rep.json();

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:32px;color:var(--brun-clair)">
        Aucun mouvement enregistré${_filtreAuditType ? " pour ce filtre" : ""}.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(m => {
      const icone  = ICONES_MOUVEMENT[m.type] || "📦";
      const deltaC = m.delta >= 0
        ? `<span style="color:var(--vert);font-weight:700">+${m.delta}</span>`
        : `<span style="color:var(--rouge);font-weight:700">${m.delta}</span>`;
      return `
        <tr>
          <td style="font-size:11px;white-space:nowrap">${m.date}</td>
          <td><span class="badge-statut s-info" style="font-size:10px">${icone} ${m.type}</span></td>
          <td style="font-weight:600;font-size:12px">${m.produit_nom}</td>
          <td style="font-family:monospace;font-size:10px;color:var(--brun-clair)">${m.produit_ref}</td>
          <td style="text-align:center">${m.avant}</td>
          <td style="text-align:center;font-weight:700">${m.apres}</td>
          <td style="text-align:center">${deltaC}</td>
          <td style="font-size:10px;color:var(--brun-clair)">
            ${m.commande_num ? `<a href="#" onclick="event.preventDefault();ouvrirModalCommande(${m.commande_id})" style="color:var(--or-sombre)">${m.commande_num}</a>` : "—"}
          </td>
          <td style="font-size:11px;color:var(--brun-clair)">${m.note}</td>
        </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" style="color:var(--rouge);padding:24px;text-align:center">
      ❌ Erreur de chargement</td></tr>`;
    console.error("chargerAuditStock:", e);
  }
}

/** Filtre l'audit stock par type de mouvement. */
function filtrerAuditStock(type, btn) {
  document.querySelectorAll("#sec-stock-audit .filtre-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  chargerAuditStock(type);
}
"""

js_content = _read("static/js/admin.js")
if "ouvrirModalMagasin" not in js_content:
    _write("static/js/admin.js", js_content.rstrip() + "\n" + JS_ADDITIONS)
    print("  ✅ Fonctions JS caisse + audit ajoutées dans admin.js")
else:
    print("  ⏭  Fonctions JS déjà présentes")

# 5c. Ajouter modal-magasin-bg au gestionnaire de fermeture (click fond)
_patch(
    "static/js/admin.js",
    '  ["modal-bg", "modal-commande-bg", "modal-banniere-bg", "modal-client-bg"].forEach(id => {',
    '  ["modal-bg", "modal-commande-bg", "modal-banniere-bg", "modal-client-bg",\n'
    '   "modal-magasin-bg"].forEach(id => {',
    "fermerModalMagasin() ajouté au click-fond"
)

# 5d. Ajouter fermerModalMagasin au raccourci Échap
_patch(
    "static/js/admin.js",
    "    if (e.key === \"Escape\") {\n"
    "      fermerModalProduit();\n"
    "      fermerModalCommande();\n"
    "      fermerModalBanniere();\n"
    "      fermerModalClient();\n"
    "    }",
    "    if (e.key === \"Escape\") {\n"
    "      fermerModalProduit();\n"
    "      fermerModalCommande();\n"
    "      fermerModalBanniere();\n"
    "      fermerModalClient();\n"
    "      fermerModalMagasin();\n"
    "    }",
    "fermerModalMagasin() ajouté au raccourci Échap"
)


# ══════════════════════════════════════════════════════════════
# 6. Git commit + push
# ══════════════════════════════════════════════════════════════
subprocess.run("git add -A", shell=True)
subprocess.run(
    'git commit -m '
    '"feat: caisse magasin + ticket WhatsApp acheteur + audit stock UI"',
    shell=True
)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("  ✅ Script terminé !")
print()
print("  N'oubliez pas de relancer le serveur :")
print("  python main.py")
print("=" * 60)
