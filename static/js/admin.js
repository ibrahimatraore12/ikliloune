// =============================================================
// admin.js — Dashboard admin IKLILOUNE
// Gère : navigation, tables produits/commandes/clients,
//        modal produit/commande/bannière, codes promo, export
// Philosophie : 1 fonction = 1 responsabilité (Regis N'guessan)
// =============================================================

"use strict";

// ── État global ───────────────────────────────────────────────
const ADMIN = {
  typeProduit    : null,   // type sélectionné dans le modal produit
  editId         : null,   // ID produit en cours d'édition (null = création)
  couleurs       : [],     // couleurs sélectionnées
  pointures      : [],     // pointures (chaussures)
  tailles        : [],     // tailles (vêtements)
  commandeId     : null,   // ID commande ouverte dans le modal
  banniereSec    : false,  // section bannières chargée
};

// ── Libellés et styles par statut de commande ────────────────
const STATUTS_COMMANDE = {
  recue          : { label: "📬 Reçue",          classe: "s-info" },
  confirmee      : { label: "✅ Confirmée",       classe: "s-ok"   },
  en_preparation : { label: "🔧 En préparation",  classe: "s-warn" },
  expediee       : { label: "🚚 Expédiée",        classe: "s-info" },
  livree         : { label: "🎉 Livrée",          classe: "s-ok"   },
  annulee        : { label: "❌ Annulée",         classe: "s-err"  },
};


// ══════════════════════════════════════════════════════════════
// UTILITAIRES
// ══════════════════════════════════════════════════════════════

/** Affiche un toast de notification (succès, erreur, avertissement). */
let _toastTimer;
function afficherToast(msg, icone = "✅") {
  const t = document.getElementById("toast");
  if (!t) return;
  document.getElementById("toast-icone").textContent = icone;
  document.getElementById("toast-msg").textContent   = msg;
  t.classList.add("visible");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove("visible"), 3500);
}

/** Formate un entier en prix FCFA localisé. Ex: 28500 → "28 500 FCFA" */
function formaterPrix(n) {
  return new Intl.NumberFormat("fr-CI").format(n || 0) + " FCFA";
}

/** Formate une date ISO en chaîne lisible. */
function formaterDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("fr-FR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

/**
 * Filtre les lignes d'un <tbody> selon une chaîne de recherche.
 * @param {string} tbodyId - ID du tbody à filtrer
 * @param {string} q       - Texte de recherche
 */
function filtrerTableAdmin(tbodyId, q) {
  const tbody = document.getElementById(tbodyId);
  if (!tbody) return;
  const terme = (q || "").toLowerCase();
  Array.from(tbody.querySelectorAll("tr")).forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(terme) ? "" : "none";
  });
}

/**
 * Filtre les lignes du tableau commandes par statut.
 * @param {string} statut - Statut à afficher ("" = tous)
 * @param {HTMLElement} btn - Bouton actif (pour le style)
 */
function filtrerCommandes(statut, btn) {
  // Mettre à jour le bouton actif
  document.querySelectorAll(".filtre-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");

  const rows = document.querySelectorAll("#tbody-commandes tr");
  rows.forEach(row => {
    if (!statut) {
      row.style.display = "";
    } else {
      // Le statut est stocké dans data-statut sur chaque TR
      row.style.display = (row.dataset.statut === statut) ? "" : "none";
    }
  });
}

/** Sélecteur d'emoji pour le label de catégorie produit. */
function iconeCategorie(cat) {
  return { parfum: "🌸", sac: "👜", chaussure: "👟", vetement: "👗", accessoire: "💍" }[cat] || "📦";
}


// ══════════════════════════════════════════════════════════════
// NAVIGATION ENTRE SECTIONS
// ══════════════════════════════════════════════════════════════

/**
 * Affiche la section demandée et charge ses données si nécessaire.
 * @param {string} section - Nom de la section (dashboard, produits, commandes...)
 * @param {HTMLElement|null} btn - Bouton sidebar cliqué
 */
function adminSection(section, btn) {
  // Mettre à jour le bouton actif dans la sidebar
  if (btn) {
    document.querySelectorAll(".sbar-item").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }

  // Afficher la bonne section
  document.querySelectorAll(".admin-section").forEach(s => s.classList.remove("active"));
  const sec = document.getElementById("sec-" + section);
  if (sec) sec.classList.add("active");

  // Charger les données à la demande
  switch (section) {
    case "produits":  chargerTableProduits();  break;
    case "commandes": chargerTableCommandes(); break;
    case "clients":   chargerTableClients();   break;
    case "bannieres": chargerBannieres();       break;
    case "promos":    chargerCodesPromo();      break;
    case "stats":     /* graphiques déjà rendus côté serveur */ break;
  }
}


// ══════════════════════════════════════════════════════════════
// TABLE PRODUITS
// ══════════════════════════════════════════════════════════════

/** Charge et affiche tous les produits dans le tableau admin. */
async function chargerTableProduits() {
  const tbody = document.getElementById("tbody-produits");
  if (!tbody) return;

  try {
    const rep  = await fetch("/admin/api/produits");
    const data = await rep.json();

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;padding:24px;color:var(--brun-clair)">
        Aucun article dans le catalogue. <button class="btn-primaire" onclick="ouvrirModalProduit()">+ Ajouter le premier</button>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(p => {
      // Indicateur stock couleur
      const indic = p.stock_indicateur || "vert";
      const stockLabel = {
        vert   : `<span class="badge-statut s-ok">${p.stock} en stock</span>`,
        orange : `<span class="badge-statut s-warn">${p.stock} — Stock bas</span>`,
        rouge  : `<span class="badge-statut s-err">${p.stock} — Critique !</span>`,
        rupture: `<span class="badge-statut s-err">Rupture</span>`,
      }[indic] || `<span>${p.stock}</span>`;

      const prixAff = p.prix_promo
        ? `<span style="font-weight:700;color:var(--rouge)">${formaterPrix(p.prix_promo)}</span>
           <br><small style="text-decoration:line-through;color:var(--brun-clair)">${formaterPrix(p.prix)}</small>`
        : `<span style="font-weight:700;color:var(--or-sombre)">${formaterPrix(p.prix)}</span>`;

      return `
        <tr>
          <td>
            <div class="prod-mini-photo">
              ${p.photo
                ? `<img src="/static/images/produits/${p.photo}" alt="${p.nom}">`
                : `<span style="font-size:22px">${iconeCategorie(p.categorie)}</span>`}
            </div>
          </td>
          <td style="font-size:10px;font-family:monospace;color:var(--brun-clair)">${p.reference || "—"}</td>
          <td>
            <div style="font-weight:700;font-size:12px">${p.nom}</div>
            <div style="font-size:10px;color:var(--brun-clair)">${(p.description || "").slice(0, 40)}…</div>
          </td>
          <td>${iconeCategorie(p.categorie)} ${p.categorie}</td>
          <td>${{ femme: "🫧 Femme", homme: "🪸 Homme", mixte: "✨ Mixte" }[p.genre] || p.genre}</td>
          <td>${prixAff}</td>
          <td>${p.prix_promo ? `<span style="color:var(--rouge);font-size:10px">✔ Promo</span>` : "—"}</td>
          <td>${stockLabel}</td>
          <td>${p.badge ? `<span class="badge-or">${p.badge}</span>` : "—"}</td>
          <td><span class="badge-statut ${p.actif ? "s-ok" : "s-info"}">${p.actif ? "Actif" : "Inactif"}</span></td>
          <td>
            <div style="display:flex;gap:6px">
              <button class="btn-mini" onclick="editerProduit(${p.id})" title="Modifier">✏️</button>
              ${p.actif
                ? `<button class="btn-mini btn-danger" onclick="supprimerProduit(${p.id},'${p.nom.replace(/'/g,"\\'")}')">🗑️</button>`
                : `<button class="btn-mini btn-success" onclick="reactiverProduit(${p.id},'${p.nom.replace(/'/g,"\\'")}')">♻️</button>`}
            </div>
          </td>
        </tr>`;
    }).join("");

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;color:var(--rouge);padding:24px">
      ❌ Erreur de chargement : ${e.message}
    </td></tr>`;
    console.error("chargerTableProduits:", e);
  }
}

/** Désactive (soft delete) un produit. */
async function supprimerProduit(id, nom) {
  if (!confirm(`Retirer "${nom}" du catalogue ?\n\nIl restera en base pour les commandes existantes.`)) return;
  try {
    const rep  = await fetch(`/admin/api/produit/supprimer/${id}`, { method: "DELETE" });
    const data = await rep.json();
    afficherToast(data.message || `"${nom}" retiré`);
    chargerTableProduits();
  } catch (e) {
    afficherToast("❌ Erreur lors de la suppression", "❌");
  }
}

/** Réactive un produit précédemment désactivé. */
async function reactiverProduit(id, nom) {
  try {
    const rep  = await fetch(`/admin/api/produit/reactiver/${id}`, { method: "POST" });
    const data = await rep.json();
    afficherToast(`♻️ "${nom}" remis en ligne`);
    chargerTableProduits();
  } catch (e) {
    afficherToast("❌ Erreur lors de la réactivation", "❌");
  }
}

/**
 * Pré-remplit le modal avec les données d'un produit existant.
 * @param {number} id - ID du produit à éditer
 */
async function editerProduit(id) {
  try {
    // Utiliser la route admin qui expose les vraies données de stock
    const rep = await fetch(`/api/produits/${id}`);
    const p   = await rep.json();

    ADMIN.editId   = id;
    ADMIN.couleurs = Array.isArray(p.couleurs) ? p.couleurs : [];
    ADMIN.tailles  = Array.isArray(p.tailles)  ? p.tailles  : [];
    ADMIN.pointures = ADMIN.tailles; // chaussures utilisent le même champ

    document.getElementById("modal-titre").textContent = `✏️ Modifier "${p.nom}"`;
    document.getElementById("f-id").value         = id;
    document.getElementById("f-nom").value        = p.nom || "";
    document.getElementById("f-prix").value       = p.prix || "";
    document.getElementById("f-prix-promo").value = p.prix_promo || "";
    document.getElementById("f-stock").value      = p.stock != null ? p.stock : "";
    document.getElementById("f-desc").value       = p.description || "";
    document.getElementById("f-genre").value      = p.genre || "mixte";
    document.getElementById("f-badge").value      = p.badge || "";

    const vedette = document.getElementById("f-vedette");
    if (vedette) vedette.checked = p.en_vedette || false;

    // Sélectionner le type d'article
    const typeIndex = ["parfum", "sac", "chaussure", "vetement", "accessoire"].indexOf(p.categorie);
    const typeBtn   = document.querySelectorAll(".type-btn")[typeIndex];
    choisirType(p.categorie, typeBtn || null);

    // Photo existante
    if (p.photo) {
      const preview = document.getElementById("photo-preview");
      preview.src   = `/static/images/produits/${p.photo}`;
      preview.style.display = "block";
      document.getElementById("upload-zone").classList.add("has-img");
    }

    rendreCouleurTags();
    rendreTailleTags();
    rendrePointureTags();

    document.getElementById("modal-bg").classList.add("show");

  } catch (e) {
    afficherToast("❌ Impossible de charger le produit", "❌");
    console.error("editerProduit:", e);
  }
}


// ══════════════════════════════════════════════════════════════
// TABLE COMMANDES
// ══════════════════════════════════════════════════════════════

/** Charge et affiche toutes les commandes dans le tableau. */
async function chargerTableCommandes() {
  const tbody = document.getElementById("tbody-commandes");
  if (!tbody) return;

  try {
    const rep  = await fetch("/admin/api/commandes");
    const data = await rep.json();

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--brun-clair)">
        Aucune commande enregistrée pour le moment.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(c => {
      const s = STATUTS_COMMANDE[c.statut] || { label: c.statut, classe: "s-info" };

      // Résumé des articles (ex: "Parfum Oud x2, Sac Python x1")
      let resumeArt = "—";
      try {
        const arts = typeof c.articles === "string" ? JSON.parse(c.articles) : (c.articles || []);
        if (arts.length) {
          resumeArt = arts.slice(0, 2).map(a => `${a.nom} ×${a.quantite}`).join(", ");
          if (arts.length > 2) resumeArt += ` + ${arts.length - 2} autre(s)`;
        }
      } catch (_) {}

      return `
        <tr data-statut="${c.statut}" data-id="${c.id}">
          <td style="font-weight:700;color:var(--or-sombre);font-family:monospace">${c.numero}</td>
          <td style="font-size:11px">${formaterDate(c.cree_le)}</td>
          <td style="font-weight:600">${c.client_prenom ? c.client_prenom + " " : ""}${c.client_nom || "—"}</td>
          <td>
            <a href="https://wa.me/${(c.client_telephone||"").replace(/[^0-9]/g,"")}"
               target="_blank" class="lien-tel" title="Contacter sur WhatsApp">
              ${c.client_telephone || "—"}
            </a>
          </td>
          <td style="font-size:11px;color:var(--brun-clair)">${resumeArt}</td>
          <td style="font-weight:700">${formaterPrix(c.total)}</td>
          <td style="font-size:11px">${c.canal || "site"}</td>
          <td><span class="badge-statut ${s.classe}">${s.label}</span></td>
          <td>
            <button class="btn-mini" onclick="ouvrirModalCommande(${c.id})">Voir →</button>
          </td>
        </tr>`;
    }).join("");

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--rouge);padding:24px">
      ❌ Erreur de chargement : ${e.message}
    </td></tr>`;
    console.error("chargerTableCommandes:", e);
  }
}

/**
 * Ouvre le modal de détail d'une commande.
 * Charge l'historique des statuts + prépare la zone WhatsApp.
 */
async function ouvrirModalCommande(id) {
  ADMIN.commandeId = id;
  const corps = document.getElementById("modal-commande-corps");
  corps.innerHTML = `<div style="text-align:center;padding:40px">Chargement...</div>`;
  document.getElementById("modal-commande-bg").classList.add("show");
  document.getElementById("wa-notif-zone").style.display = "none";

  try {
    const rep  = await fetch(`/admin/api/commande/${id}`);
    const data = await rep.json();
    const c    = data.commande;

    // Pré-sélectionner le statut actuel dans le select
    const sel = document.getElementById("nouveau-statut");
    if (sel) sel.value = c.statut;

    // ── Articles commandés ────────────────────────────────
    let articlesHtml = "";
    try {
      const arts = typeof c.articles === "string" ? JSON.parse(c.articles) : (c.articles || []);
      articlesHtml = arts.map(a => `
        <div class="cmd-article-ligne">
          ${a.photo
            ? `<img src="/static/images/produits/${a.photo}" class="cmd-art-img">`
            : `<span style="font-size:24px">${iconeCategorie(a.categorie)}</span>`}
          <div style="flex:1">
            <div style="font-weight:700">${a.nom}</div>
            ${a.coloris ? `<small>Coloris : ${a.coloris}</small>` : ""}
            ${a.taille  ? `<small> · Taille : ${a.taille}</small>`  : ""}
          </div>
          <div style="text-align:right">
            <div style="font-weight:700">×${a.quantite}</div>
            <div style="font-size:11px;color:var(--brun-clair)">${formaterPrix(a.prix_unitaire * a.quantite)}</div>
          </div>
        </div>`).join("") || "<p>Aucun article</p>";
    } catch (_) {
      articlesHtml = `<p style="color:var(--brun-clair)">${c.articles || "—"}</p>`;
    }

    // ── Historique des statuts ────────────────────────────
    const histHtml = (c.historique || []).length
      ? c.historique.map(h => `
        <div class="hist-ligne">
          <span class="hist-date">${formaterDate(h.change_le)}</span>
          <span class="hist-qui">${h.modifie_par}</span>
          <span>${h.statut_avant} → <strong>${h.statut_apres}</strong></span>
          ${h.note ? `<span class="hist-note">${h.note}</span>` : ""}
        </div>`).join("")
      : `<p style="color:var(--brun-clair);font-size:12px">Aucun historique — premier statut.</p>`;

    // ── Corps du modal ────────────────────────────────────
    document.getElementById("modal-commande-titre").textContent =
      `📦 Commande ${c.numero}`;

    corps.innerHTML = `
      <!-- Infos client -->
      <div class="cmd-info-grille">
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Client</div>
          <div>${c.client_prenom ? c.client_prenom + " " : ""}${c.client_nom}</div>
        </div>
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Téléphone</div>
          <div>
            <a href="https://wa.me/${(c.client_telephone||"").replace(/[^0-9]/g,"")}"
               target="_blank" class="lien-wa">${c.client_telephone || "—"}</a>
          </div>
        </div>
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Adresse</div>
          <div>${c.client_adresse || "—"}</div>
        </div>
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Canal</div>
          <div>${c.canal || "site web"}</div>
        </div>
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Date</div>
          <div>${formaterDate(c.cree_le)}</div>
        </div>
        <div class="cmd-info-item">
          <div class="cmd-info-lbl">Paiement</div>
          <div>${c.paiement || "—"}</div>
        </div>
      </div>

      <!-- Articles -->
      <div style="margin:16px 0">
        <h4 style="margin:0 0 10px;font-size:13px">🛍️ Articles commandés</h4>
        <div class="cmd-articles-liste">${articlesHtml}</div>
      </div>

      <!-- Totaux -->
      <div class="cmd-totaux">
        <div class="cmd-total-ligne">
          <span>Sous-total</span>
          <span>${formaterPrix(c.sous_total || c.total)}</span>
        </div>
        ${c.remise_montant > 0 ? `
        <div class="cmd-total-ligne" style="color:var(--vert)">
          <span>Réduction${c.code_promo_utilise ? " ("+c.code_promo_utilise+")" : ""}</span>
          <span>-${formaterPrix(c.remise_montant)}</span>
        </div>` : ""}
        <div class="cmd-total-ligne cmd-total-grand">
          <span>TOTAL</span>
          <span>${formaterPrix(c.total)}</span>
        </div>
      </div>

      <!-- Notes admin -->
      ${c.notes_admin ? `
      <div style="margin:16px 0;padding:12px;background:var(--ivoire);border-radius:8px">
        <strong style="font-size:12px">📝 Notes internes :</strong>
        <p style="margin:6px 0 0;font-size:12px">${c.notes_admin}</p>
      </div>` : ""}

      <!-- Historique statuts -->
      <div style="margin:16px 0">
        <h4 style="margin:0 0 10px;font-size:13px">📋 Historique des statuts</h4>
        <div class="historique-liste">${histHtml}</div>
      </div>`;

  } catch (e) {
    corps.innerHTML = `<div style="color:var(--rouge);padding:20px">❌ Erreur : ${e.message}</div>`;
    console.error("ouvrirModalCommande:", e);
  }
}

function fermerModalCommande() {
  document.getElementById("modal-commande-bg").classList.remove("show");
  document.getElementById("wa-notif-zone").style.display = "none";
  ADMIN.commandeId = null;
}

/**
 * Envoie le changement de statut d'une commande au serveur.
 * Affiche ensuite le lien WhatsApp de notification client.
 */
async function changerStatutCommande() {
  if (!ADMIN.commandeId) return;

  const statut = document.getElementById("nouveau-statut")?.value;
  const note   = document.getElementById("note-statut")?.value.trim();

  if (!statut) { afficherToast("⚠️ Sélectionnez un statut", "⚠️"); return; }

  try {
    const rep  = await fetch(`/admin/api/commande/statut/${ADMIN.commandeId}`, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({ statut, note })
    });
    const data = await rep.json();

    if (data.succes) {
      const libelle = STATUTS_COMMANDE[statut]?.label || statut;
      afficherToast(`✅ Statut → ${libelle}`);

      // Rafraîchir le tableau des commandes en arrière-plan
      chargerTableCommandes();

      // Afficher la zone de notification WhatsApp si disponible
      const notif = data.notification_wa;
      if (notif && notif.url) {
        const zone    = document.getElementById("wa-notif-zone");
        const lien    = document.getElementById("wa-notif-lien");
        const preview = document.getElementById("wa-notif-preview");
        lien.href       = notif.url;
        preview.textContent = notif.message ? `"${notif.message.slice(0, 100)}…"` : "";
        zone.style.display  = "block";
      }

      // Effacer la note
      const noteEl = document.getElementById("note-statut");
      if (noteEl) noteEl.value = "";

    } else {
      afficherToast("❌ " + (data.erreur || "Erreur"), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
    console.error("changerStatutCommande:", e);
  }
}


// ══════════════════════════════════════════════════════════════
// TABLE CLIENTS
// ══════════════════════════════════════════════════════════════

/** Charge et affiche le registre clients. */
async function chargerTableClients() {
  const tbody = document.getElementById("tbody-clients");
  if (!tbody) return;

  try {
    const rep  = await fetch("/admin/api/clients");
    const data = await rep.json();

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--brun-clair)">
        Aucun client enregistré.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(c => {
      // Masquer les emails fictifs (clients sans email)
      const emailAff = (!c.email || c.email.includes("sans-email")) ? "—" : c.email;

      return `
        <tr>
          <td style="font-weight:700">${c.prenom || "—"}</td>
          <td>${c.nom || "—"}</td>
          <td>
            ${c.telephone
              ? `<a href="https://wa.me/${c.telephone.replace(/[^0-9]/g,"")}"
                    target="_blank" class="lien-tel">${c.telephone}</a>`
              : "—"}
          </td>
          <td style="font-size:11px;color:var(--brun-clair)">${emailAff}</td>
          <td>${c.interet || "—"}</td>
          <td><span class="badge-statut s-info">${c.source || "popup"}</span></td>
          <td style="text-align:center;font-weight:700">${c.nb_commandes || 0}</td>
          <td>${c.consentement ? "✅" : "❌"}</td>
          <td style="font-size:11px;color:var(--brun-clair)">${formaterDate(c.cree_le)}</td>
        </tr>`;
    }).join("");

  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:var(--rouge);padding:24px">
      ❌ Erreur de chargement
    </td></tr>`;
    console.error("chargerTableClients:", e);
  }
}


// ══════════════════════════════════════════════════════════════
// BANNIÈRES — Carrousel d'accueil
// ══════════════════════════════════════════════════════════════

/** Charge et affiche la liste des bannières. */
async function chargerBannieres() {
  const conteneur = document.getElementById("bannieres-liste");
  if (!conteneur) return;

  try {
    const rep  = await fetch("/admin/api/bannieres");
    const data = await rep.json();

    if (!data.length) {
      conteneur.innerHTML = `
        <div style="text-align:center;padding:60px;color:var(--brun-clair)">
          <div style="font-size:48px;margin-bottom:12px">🖼️</div>
          <p>Aucune bannière créée.</p>
          <button class="btn-primaire" onclick="ouvrirModalBanniere()">+ Créer la première bannière</button>
        </div>`;
      return;
    }

    conteneur.innerHTML = data.map(b => `
      <div class="banniere-card ${b.actif ? "" : "banniere-inactive"}" data-id="${b.id}">
        <div class="banniere-card-header">
          <span style="font-size:28px">${b.deco_emoji || "✨"}</span>
          <div style="flex:1">
            <div style="font-weight:700">${b.titre}</div>
            ${b.sous_titre ? `<div style="font-size:11px;color:var(--brun-clair)">${b.sous_titre}</div>` : ""}
          </div>
          <div class="banniere-ordre">Ordre ${b.ordre}</div>
        </div>
        <div class="banniere-card-meta">
          <span class="badge-statut ${b.actif ? "s-ok" : "s-info"}">${b.actif ? "Active" : "Inactive"}</span>
          <span class="badge-or">${b.collection || "les-deux"}</span>
          <span style="font-size:11px;color:var(--brun-clair)">${b.style || "clair"}</span>
          ${b.date_debut || b.date_fin
            ? `<span style="font-size:11px;color:var(--brun-clair)">
                📅 ${b.date_debut ? b.date_debut.slice(0,10) : "—"} → ${b.date_fin ? b.date_fin.slice(0,10) : "∞"}
               </span>`
            : `<span style="font-size:11px;color:var(--brun-clair)">📅 Permanente</span>`}
        </div>
        <div style="margin-top:10px;display:flex;gap:8px">
          <span style="font-size:11px;flex:1">→ ${b.lien_bouton || "/"}</span>
          <button class="btn-mini" onclick="editerBanniere(${b.id})">✏️ Modifier</button>
          ${b.actif
            ? `<button class="btn-mini btn-danger" onclick="desactiverBanniere(${b.id},'${b.titre.replace(/'/g,"\\'")}')">🚫 Désactiver</button>`
            : `<button class="btn-mini" onclick="activerBanniere(${b.id},'${b.titre.replace(/'/g,"\\'")}')">▶️ Activer</button>`}
        </div>
      </div>`
    ).join("");

  } catch (e) {
    conteneur.innerHTML = `<div style="color:var(--rouge);padding:20px">❌ Erreur de chargement</div>`;
    console.error("chargerBannieres:", e);
  }
}

function ouvrirModalBanniere() {
  // Réinitialiser le formulaire
  ["b-titre","b-sous-titre","b-btn-texte","b-btn-lien","b-emoji","b-debut","b-fin"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = id === "b-btn-texte" ? "Découvrir" : id === "b-btn-lien" ? "/" : "";
  });
  document.getElementById("b-ordre").value = "99";
  document.getElementById("b-id").value    = "";
  document.getElementById("modal-banniere-titre").textContent = "Nouvelle bannière";
  document.getElementById("modal-banniere-bg").classList.add("show");
}

function fermerModalBanniere() {
  document.getElementById("modal-banniere-bg").classList.remove("show");
}

/** Pré-remplit le modal bannière pour modification. */
async function editerBanniere(id) {
  try {
    const rep  = await fetch("/admin/api/bannieres");
    const data = await rep.json();
    const b    = data.find(x => x.id === id);
    if (!b) { afficherToast("Bannière introuvable", "❌"); return; }

    document.getElementById("b-id").value         = b.id;
    document.getElementById("b-titre").value      = b.titre || "";
    document.getElementById("b-sous-titre").value = b.sous_titre || "";
    document.getElementById("b-btn-texte").value  = b.texte_bouton || "Découvrir";
    document.getElementById("b-btn-lien").value   = b.lien_bouton || "/";
    document.getElementById("b-collection").value = b.collection || "les-deux";
    document.getElementById("b-style").value      = b.style || "clair";
    document.getElementById("b-emoji").value      = b.deco_emoji || "✨";
    document.getElementById("b-ordre").value      = b.ordre || 99;
    document.getElementById("b-debut").value      = b.date_debut ? b.date_debut.slice(0,10) : "";
    document.getElementById("b-fin").value        = b.date_fin   ? b.date_fin.slice(0,10)   : "";
    document.getElementById("modal-banniere-titre").textContent = `✏️ Modifier "${b.titre}"`;
    document.getElementById("modal-banniere-bg").classList.add("show");
  } catch (e) {
    afficherToast("❌ Erreur", "❌");
  }
}

/** Sauvegarde une bannière (création ou modification). */
async function sauvegarderBanniere() {
  const titre = document.getElementById("b-titre")?.value.trim();
  if (!titre) { afficherToast("⚠️ Le titre est obligatoire", "⚠️"); return; }

  const bid = document.getElementById("b-id")?.value;
  const url = bid
    ? `/admin/api/banniere/modifier/${bid}`
    : "/admin/api/banniere/creer";

  const payload = {
    titre        : titre,
    sous_titre   : document.getElementById("b-sous-titre")?.value.trim() || "",
    texte_bouton : document.getElementById("b-btn-texte")?.value.trim() || "Découvrir",
    lien_bouton  : document.getElementById("b-btn-lien")?.value.trim() || "/",
    collection   : document.getElementById("b-collection")?.value || "les-deux",
    style        : document.getElementById("b-style")?.value || "clair",
    deco_emoji   : document.getElementById("b-emoji")?.value || "✨",
    ordre        : parseInt(document.getElementById("b-ordre")?.value || "99"),
    date_debut   : document.getElementById("b-debut")?.value || null,
    date_fin     : document.getElementById("b-fin")?.value || null,
    actif        : true,
  };

  try {
    const rep  = await fetch(url, {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify(payload)
    });
    const data = await rep.json();
    if (data.succes) {
      afficherToast(bid ? "✅ Bannière modifiée" : "✅ Bannière créée");
      fermerModalBanniere();
      chargerBannieres();
    } else {
      afficherToast("❌ " + (data.erreur || "Erreur"), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
    console.error("sauvegarderBanniere:", e);
  }
}

/** Désactive une bannière. */
async function desactiverBanniere(id, titre) {
  if (!confirm(`Désactiver la bannière "${titre}" ?`)) return;
  await fetch(`/admin/api/banniere/supprimer/${id}`, { method: "DELETE" });
  afficherToast(`Bannière "${titre}" désactivée`);
  chargerBannieres();
}

/** Réactive une bannière (passe actif=true). */
async function activerBanniere(id, titre) {
  await fetch(`/admin/api/banniere/modifier/${id}`, {
    method  : "POST",
    headers : { "Content-Type": "application/json" },
    body    : JSON.stringify({ actif: true })
  });
  afficherToast(`▶️ Bannière "${titre}" réactivée`);
  chargerBannieres();
}


// ══════════════════════════════════════════════════════════════
// CODES PROMO
// ══════════════════════════════════════════════════════════════

/** Charge et affiche la liste des codes promo. */
async function chargerCodesPromo() {
  const tbody = document.getElementById("tbody-promos");
  if (!tbody) return;

  try {
    const rep  = await fetch("/admin/api/codes-promo");
    const data = await rep.json();

    if (!data.length) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--brun-clair)">
        Aucun code promo — créez-en un ci-dessus.
      </td></tr>`;
      return;
    }

    tbody.innerHTML = data.map(c => `
      <tr>
        <td style="font-weight:800;color:var(--or-sombre);font-size:14px;font-family:monospace">${c.code}</td>
        <td style="font-size:11px">${c.type_reduction === "montant_fixe" ? "FCFA fixe" : "Pourcentage"}</td>
        <td style="font-weight:700;color:var(--vert)">-${c.reduction_pct}%</td>
        <td style="font-size:11px">${c.montant_min ? formaterPrix(c.montant_min) : "Aucun"}</td>
        <td>${c.nb_utilisations}${c.max_utilisations ? " / " + c.max_utilisations : " / ∞"}</td>
        <td style="font-size:11px">${c.expire_le ? c.expire_le.slice(0,10) : "—"}</td>
        <td style="font-size:11px;color:var(--brun-clair)">${c.description || "—"}</td>
        <td><span class="badge-statut ${c.actif ? "s-ok" : "s-warn"}">${c.actif ? "✅ Actif" : "⛔ Expiré"}</span></td>
        <td>
          ${c.actif
            ? `<button class="btn-mini btn-danger" onclick="desactiverCode(${c.id})">Désactiver</button>`
            : "—"}
        </td>
      </tr>`
    ).join("");

  } catch (e) {
    console.error("chargerCodesPromo:", e);
  }
}

/** Crée un nouveau code promo via le formulaire. */
async function creerCodePromo() {
  const code = document.getElementById("np-code")?.value.trim().toUpperCase();
  const pct  = document.getElementById("np-pct")?.value;
  const type = document.getElementById("np-type")?.value || "pourcentage";
  const min  = document.getElementById("np-min")?.value  || "";
  const max  = document.getElementById("np-max")?.value  || "";
  const cond = document.getElementById("np-conditions")?.value || "tous";
  const deb  = document.getElementById("np-debut")?.value || "";
  const exp  = document.getElementById("np-expire")?.value || "";
  const desc = document.getElementById("np-desc")?.value.trim() || "";

  if (!code || !pct) {
    afficherToast("⚠️ Code et pourcentage de réduction obligatoires", "⚠️");
    return;
  }

  try {
    const rep  = await fetch("/admin/api/code-promo/creer", {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({
        code,
        type_reduction   : type,
        reduction_pct    : parseInt(pct),
        montant_min      : min ? parseInt(min) : null,
        max_utilisations : max ? parseInt(max) : null,
        conditions       : cond,
        date_debut       : deb || null,
        expire_le        : exp || null,
        description      : desc,
      })
    });
    const data = await rep.json();

    if (data.succes) {
      afficherToast(`✅ Code "${code}" créé (-${pct}%)`);
      ["np-code","np-pct","np-min","np-max","np-debut","np-expire","np-desc"].forEach(id => {
        const el = document.getElementById(id); if (el) el.value = "";
      });
      chargerCodesPromo();
    } else {
      afficherToast("❌ " + (data.erreur || "Erreur"), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
  }
}

/** Désactive un code promo. */
async function desactiverCode(id) {
  if (!confirm("Désactiver ce code promo ?")) return;
  await fetch(`/admin/api/code-promo/desactiver/${id}`, { method: "POST" });
  afficherToast("Code désactivé");
  chargerCodesPromo();
}


// ══════════════════════════════════════════════════════════════
// MODAL PRODUIT — Création et modification
// ══════════════════════════════════════════════════════════════

/** Ouvre le modal produit en mode création. */
function ouvrirModalProduit() {
  ADMIN.editId    = null;
  ADMIN.couleurs  = [];
  ADMIN.pointures = [];
  ADMIN.tailles   = [];

  document.getElementById("modal-titre").textContent = "Nouvel article";
  document.getElementById("f-id").value = "";

  // Vider tous les champs
  ["f-nom","f-prix","f-prix-promo","f-stock","f-desc","f-ml","f-dims","f-talon","f-seuil-bas","f-seuil-haut"]
    .forEach(id => { const el = document.getElementById(id); if (el) el.value = ""; });

  const vedette = document.getElementById("f-vedette");
  if (vedette) vedette.checked = false;

  // Réinitialiser photo
  const preview = document.getElementById("photo-preview");
  if (preview) { preview.style.display = "none"; preview.src = ""; }
  document.getElementById("upload-zone")?.classList.remove("has-img");
  const input = document.getElementById("photo-input");
  if (input) input.value = "";

  // Désélectionner le type
  document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".champs-type").forEach(el => el.style.display = "none");
  ADMIN.typeProduit = null;

  rendreCouleurTags();
  rendreTailleTags();
  rendrePointureTags();

  document.getElementById("modal-bg").classList.add("show");
}

function fermerModalProduit() {
  document.getElementById("modal-bg").classList.remove("show");
}

/** Sélectionne un type d'article et affiche les champs spécifiques. */
function choisirType(type, btn) {
  ADMIN.typeProduit = type;
  document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  document.querySelectorAll(".champs-type").forEach(el => el.style.display = "none");
  const cible = document.getElementById("champs-" + type);
  if (cible) cible.style.display = "block";
}

/** Affiche un aperçu de l'image sélectionnée. */
function previewPhoto(input) {
  const file = input.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById("photo-preview");
    img.src = e.target.result;
    img.style.display = "block";
    document.getElementById("upload-zone")?.classList.add("has-img");
  };
  reader.readAsDataURL(file);
}

/** Gestion du drag & drop de photo. */
function dropPhoto(event) {
  event.preventDefault();
  const file = event.dataTransfer.files[0];
  if (!file || !file.type.startsWith("image/")) {
    afficherToast("⚠️ Fichier image requis", "⚠️");
    return;
  }
  const input = document.getElementById("photo-input");
  const dt    = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  previewPhoto(input);
}

// ── Gestion des tags couleurs ──────────────────────────────────

/** Correspondance noms de couleur → code hexadécimal. */
const MAP_COULEURS = {
  noir:"#1a1a1a", blanc:"#ffffff", or:"#C9922A", rouge:"#E8341C",
  bleu:"#1E3A5F", vert:"#2ECC71", caramel:"#D2691E", bordeaux:"#8B0000",
  rose:"#F2AEBB", gris:"#808080", marine:"#1E3A5F", violet:"#9B59B6",
  beige:"#F5DEB3", marron:"#8B4513",
};

function ajouterCouleurTag(e) {
  if (e.key !== "Enter" && e.key !== ",") return;
  e.preventDefault();
  const val = document.getElementById("input-couleur").value.trim();
  if (!val) return;
  const hex = MAP_COULEURS[val.toLowerCase()] || "#C9922A";
  ajouterCouleurVite(hex, val);
  document.getElementById("input-couleur").value = "";
}

function ajouterCouleurVite(hex, nom) {
  if (ADMIN.couleurs.find(c => c.hex === hex)) return;
  ADMIN.couleurs.push({ hex, nom });
  rendreCouleurTags();
}

function retirerCouleur(i) { ADMIN.couleurs.splice(i, 1); rendreCouleurTags(); }

function rendreCouleurTags() {
  const wrap  = document.getElementById("tags-couleurs");
  const input = document.getElementById("input-couleur");
  if (!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.couleurs.forEach((c, i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-couleur";
    tag.style.background   = c.hex;
    tag.style.color        = ["#ffffff","#FBF3E8","#F5DEB3","#beige"].includes(c.hex) ? "#333" : "white";
    tag.innerHTML = `${c.nom}<button type="button" onclick="retirerCouleur(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// ── Gestion des tags pointures ─────────────────────────────────

function ajouterPointureTag(e) {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const val = document.getElementById("input-pointure").value.trim();
  if (!val || ADMIN.pointures.includes(val)) return;
  ADMIN.pointures.push(val);
  document.getElementById("input-pointure").value = "";
  rendrePointureTags();
}

function ajouterPointureVite(t) {
  if (!ADMIN.pointures.includes(t)) { ADMIN.pointures.push(t); rendrePointureTags(); }
}

function retirerPointure(i) { ADMIN.pointures.splice(i, 1); rendrePointureTags(); }

function rendrePointureTags() {
  const wrap  = document.getElementById("tags-pointures");
  const input = document.getElementById("input-pointure");
  if (!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.pointures.forEach((t, i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-taille";
    tag.innerHTML = `${t}<button type="button" onclick="retirerPointure(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// ── Gestion des tags tailles (vêtements) ──────────────────────

function ajouterTailleTag(e) {
  if (e.key !== "Enter") return;
  e.preventDefault();
  const val = document.getElementById("input-taille").value.trim();
  if (!val || ADMIN.tailles.includes(val)) return;
  ADMIN.tailles.push(val);
  document.getElementById("input-taille").value = "";
  rendreTailleTags();
}

function ajouterTailleVite(t) {
  if (!ADMIN.tailles.includes(t)) { ADMIN.tailles.push(t); rendreTailleTags(); }
}

function retirerTaille(i) { ADMIN.tailles.splice(i, 1); rendreTailleTags(); }

function rendreTailleTags() {
  const wrap  = document.getElementById("tags-tailles");
  const input = document.getElementById("input-taille");
  if (!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.tailles.forEach((t, i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-taille";
    tag.innerHTML = `${t}<button type="button" onclick="retirerTaille(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// ── Sauvegarder un produit (création ou modification) ─────────

/** Collecte les données du modal et envoie en POST avec FormData. */
async function sauvegarderProduit() {
  const nom   = document.getElementById("f-nom")?.value.trim();
  const prix  = document.getElementById("f-prix")?.value;
  const stock = document.getElementById("f-stock")?.value;

  if (!nom || !prix) {
    afficherToast("⚠️ Nom et prix sont obligatoires", "⚠️");
    return;
  }
  if (!ADMIN.typeProduit) {
    afficherToast("⚠️ Choisissez un type d'article", "⚠️");
    return;
  }

  // Construire les attributs spécifiques selon le type
  let attributs = {};
  if (ADMIN.typeProduit === "parfum") {
    attributs = {
      ml      : document.getElementById("f-ml")?.value || "",
      olfactif: document.getElementById("f-olfactif")?.value || "",
      tenue   : document.getElementById("f-tenue")?.value || "",
    };
  } else if (ADMIN.typeProduit === "sac") {
    attributs = {
      matiere    : document.getElementById("f-matiere-sac")?.value || "",
      dimensions : document.getElementById("f-dims")?.value || "",
    };
  } else if (ADMIN.typeProduit === "chaussure") {
    attributs = {
      matiere : document.getElementById("f-matiere-chaussure")?.value || "",
      talon   : document.getElementById("f-talon")?.value || "0",
    };
  } else if (ADMIN.typeProduit === "vetement") {
    attributs = {
      tissu         : document.getElementById("f-tissu")?.value || "",
      type_vetement : document.getElementById("f-type-vet")?.value || "",
    };
  }

  // Tailles = pointures pour chaussures, tailles pour vêtements
  const taillesFinal = ADMIN.typeProduit === "chaussure" ? ADMIN.pointures : ADMIN.tailles;

  // Construction du FormData (supporte l'envoi de fichier)
  const fd = new FormData();
  fd.append("nom",        nom);
  fd.append("categorie",  ADMIN.typeProduit);
  fd.append("genre",      document.getElementById("f-genre")?.value || "mixte");
  fd.append("prix",       prix);
  fd.append("prix_promo", document.getElementById("f-prix-promo")?.value || "");
  fd.append("stock",      stock || "0");
  fd.append("description",document.getElementById("f-desc")?.value || "");
  fd.append("badge",      document.getElementById("f-badge")?.value || "");
  fd.append("en_vedette", document.getElementById("f-vedette")?.checked ? "true" : "false");
  fd.append("couleurs",   JSON.stringify(ADMIN.couleurs));
  fd.append("tailles",    JSON.stringify(taillesFinal));
  fd.append("attributs",  JSON.stringify(attributs));
  fd.append("seuil_bas",  document.getElementById("f-seuil-bas")?.value  || "3");
  fd.append("seuil_haut", document.getElementById("f-seuil-haut")?.value || "10");

  // Ajouter la photo si sélectionnée
  const photoInput = document.getElementById("photo-input");
  if (photoInput?.files[0]) fd.append("photo", photoInput.files[0]);

  const url = ADMIN.editId
    ? `/admin/api/produit/modifier/${ADMIN.editId}`
    : "/admin/api/produit/ajouter";

  // Désactiver le bouton pendant l'envoi
  const btn = document.getElementById("btn-sauvegarder-produit");
  if (btn) { btn.disabled = true; btn.textContent = "Enregistrement..."; }

  try {
    const rep  = await fetch(url, { method: "POST", body: fd });
    const data = await rep.json();

    if (data.succes) {
      fermerModalProduit();
      chargerTableProduits();
      afficherToast(`✅ "${nom}" enregistré avec succès !`);
    } else {
      afficherToast("❌ " + (data.erreur || "Erreur serveur"), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur réseau", "❌");
    console.error("sauvegarderProduit:", e);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "✅ Enregistrer l'article"; }
  }
}


// ══════════════════════════════════════════════════════════════
// MODAL CLIENT — Ajout manuel
// ══════════════════════════════════════════════════════════════

function ouvrirModalClient() {
  ["mc-prenom","mc-nom","mc-tel","mc-email","mc-adresse"].forEach(id => {
    const el = document.getElementById(id); if (el) el.value = "";
  });
  document.getElementById("modal-client-bg").classList.add("show");
}

function fermerModalClient() {
  document.getElementById("modal-client-bg").classList.remove("show");
}

/** Enregistre un client ajouté manuellement depuis l'admin. */
async function sauvegarderClientManuel() {
  const prenom   = document.getElementById("mc-prenom")?.value.trim();
  const telRaw   = document.getElementById("mc-tel")?.value.trim() || "";
  // Construire le numéro complet +225
  const chiffres = telRaw.replace(/\D/g, "");
  const tel      = chiffres ? "+225" + chiffres : "";

  if (!prenom || !tel) {
    afficherToast("⚠️ Prénom et numéro de téléphone obligatoires.", "⚠️");
    return;
  }
  if (chiffres.length < 8) {
    afficherToast("⚠️ Le numéro doit contenir au moins 8 chiffres.", "⚠️");
    return;
  }

  try {
    const rep  = await fetch("/admin/api/client/ajouter", {
      method  : "POST",
      headers : { "Content-Type": "application/json" },
      body    : JSON.stringify({
        prenom,
        nom       : document.getElementById("mc-nom")?.value.trim() || "",
        telephone : tel,
        email     : document.getElementById("mc-email")?.value.trim() || "",
        interet   : document.getElementById("mc-interet")?.value || "tout",
        adresse   : document.getElementById("mc-adresse")?.value.trim() || "",
      })
    });
    const data = await rep.json();

    if (data.succes) {
      fermerModalClient();
      chargerTableClients();
      afficherToast(`✅ ${prenom} ajouté au registre clients avec succès.`);
    } else {
      afficherToast("❌ " + (data.erreur || "Impossible d'ajouter le client. Réessayez."), "❌");
    }
  } catch (e) {
    afficherToast("❌ Erreur de connexion — vérifiez votre réseau et réessayez.", "❌");
  }
}


// ══════════════════════════════════════════════════════════════
// EXPORT — Graphique ventes par année (section Stats)
// ══════════════════════════════════════════════════════════════

let _anneeGraph = new Date().getFullYear();

/**
 * Navigue entre les années pour le graphique ventes (section Stats).
 * @param {HTMLElement} btn - Bouton cliqué (non utilisé mais reçu)
 * @param {number} delta    - +1 (suivant) ou -1 (précédent)
 */
async function chargerGraphiqueAnnee(btn, delta) {
  _anneeGraph += delta;
  document.getElementById("annee-graph-label").textContent = _anneeGraph;

  try {
    // On recharge le graphique depuis le serveur
    const rep  = await fetch(`/admin/api/stats/ventes?annee=${_anneeGraph}`);
    const data = await rep.json();
    // Le graphique matplotlib est rendu côté serveur au chargement initial.
    // Pour le rechargement dynamique, on affiche un message simple.
    const img = document.getElementById("img-graph-ventes");
    if (img) img.style.opacity = "0.5";
    afficherToast(`📊 Statistiques ${_anneeGraph} demandées. Actualisez la page pour voir le graphique.`);
  } catch (e) {
    console.error("chargerGraphiqueAnnee:", e);
  }
}


// ══════════════════════════════════════════════════════════════
// INITIALISATION
// ══════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
  // Charger le tableau produits au démarrage (section visible par défaut)
  chargerTableProduits();

  // Fermer les modals en cliquant sur le fond sombre
  ["modal-bg", "modal-commande-bg", "modal-banniere-bg", "modal-client-bg",
   "modal-magasin-bg"].forEach(id => {
    const modal = document.getElementById(id);
    if (modal) {
      modal.addEventListener("click", function(e) {
        if (e.target === this) {
          this.classList.remove("show");
          if (id === "modal-commande-bg") {
            document.getElementById("wa-notif-zone").style.display = "none";
            ADMIN.commandeId = null;
          }
        }
      });
    }
  });

  // Raccourci Échap pour fermer les modals
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") {
      fermerModalProduit();
      fermerModalCommande();
      fermerModalBanniere();
      fermerModalClient();
      fermerModalMagasin();
    }
  });
});


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
  const chiffres = telRaw.replace(/\D/g, "");
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
        if (confirm(`Vente enregistrée !\n\nEnvoyer le ticket WhatsApp à ${nom} ?`)) {
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
