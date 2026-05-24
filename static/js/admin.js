// =============================================================
// admin.js — JavaScript du dashboard admin IKLILOUNE
// Gère : navigation, tables, modal produit, marketing
// =============================================================

// ── État global admin ─────────────────────────────────────────
const ADMIN = {
  typeProduit  : null,   // type sélectionné dans le modal
  editId       : null,   // ID du produit en cours de modification
  couleurs     : [],     // couleurs sélectionnées
  pointures    : [],     // pointures sélectionnées (chaussures)
  tailles      : [],     // tailles sélectionnées (vêtements)
};

// ── Toast (réutilise la même fonction que boutique) ───────────
let toastTimer;
function afficherToast(msg, icone = "✅") {
  const t = document.getElementById("toast");
  if(!t) return;
  document.getElementById("toast-msg").textContent = msg;
  document.getElementById("toast-icone").textContent = icone;
  t.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("visible"), 3500);
}

// ── Navigation entre sections ────────────────────────────────
function adminSection(section, btn) {
  document.querySelectorAll(".sbar-item").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  document.querySelectorAll(".admin-section").forEach(s => s.classList.remove("active"));
  const sec = document.getElementById("sec-" + section);
  if(sec) sec.classList.add("active");

  // Charger les données selon la section
  if(section === "produits")  chargerTableProduits();
  if(section === "commandes") chargerTableCommandes();
  if(section === "clients")   chargerTableClients();
  if(section === "marketing") chargerStatsClients();
}

// ── Formatage prix ────────────────────────────────────────────
function formaterPrix(n) {
  return new Intl.NumberFormat("fr-CI").format(n) + " FCFA";
}

// ── Table produits ────────────────────────────────────────────
async function chargerTableProduits() {
  try {
    const rep  = await fetch("/admin/api/produits");
    const data = await rep.json();
    const tbody = document.getElementById("tbody-produits");
    if(!tbody) return;
    tbody.innerHTML = data.map(p => `
      <tr>
        <td>
          <div style="display:flex;align-items:center;gap:10px">
            <div style="width:36px;height:36px;border-radius:8px;background:var(--ivoire);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0">
              ${p.photo
                ? `<img src="/static/images/produits/${p.photo}" style="width:100%;height:100%;object-fit:cover;border-radius:8px" alt="${p.nom}">`
                : ({parfum:"🌸",sac:"👜",chaussure:"👟",vetement:"👗"}[p.categorie]||"📦")}
            </div>
            <div>
              <div style="font-weight:700;font-size:12px">${p.nom}</div>
              <div style="font-size:10px;color:var(--brun-clair)">${p.description?.slice(0,40) || ""}...</div>
            </div>
          </div>
        </td>
        <td>${{parfum:"Parfum",sac:"Sac",chaussure:"Chaussure",vetement:"Vêtement"}[p.categorie]||p.categorie}</td>
        <td>${{femme:"🫧 Femme",homme:"🪸 Homme",mixte:"✨ Mixte"}[p.genre]||p.genre}</td>
        <td style="font-weight:700;color:var(--or-sombre)">${formaterPrix(p.prix_actuel)}</td>
        <td><span class="badge-statut ${p.stock>5?"s-ok":p.stock>0?"s-warn":"s-info"}">${p.stock > 0 ? p.stock+" unités" : "Rupture"}</span></td>
        <td><span class="badge-statut ${p.actif?"s-ok":"s-info"}">${p.actif?"Actif":"Inactif"}</span></td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn-primaire" style="padding:5px 10px;font-size:10px" onclick="editerProduit(${p.id})">✏️</button>
            <button style="background:rgba(232,52,28,0.1);color:var(--rouge);border:none;border-radius:20px;padding:5px 10px;font-size:10px;font-weight:800;cursor:pointer" onclick="supprimerProduit(${p.id},'${p.nom}')">🗑️</button>
          </div>
        </td>
      </tr>`
    ).join("") || `<tr><td colspan="7" style="text-align:center;padding:24px;color:var(--brun-clair)">Aucun article</td></tr>`;
  } catch(e) { console.error("Erreur chargement produits:", e); }
}

function filtrerTableAdmin(q) {
  const rows = document.querySelectorAll("#tbody-produits tr");
  rows.forEach(row => {
    const txt = row.textContent.toLowerCase();
    row.style.display = txt.includes(q.toLowerCase()) ? "" : "none";
  });
}

async function supprimerProduit(id, nom) {
  if(!confirm(`Retirer "${nom}" du catalogue ?`)) return;
  try {
    await fetch(`/admin/api/produit/supprimer/${id}`, { method:"DELETE" });
    afficherToast(`🗑️ "${nom}" retiré du catalogue`);
    chargerTableProduits();
  } catch(e) { afficherToast("❌ Erreur", "❌"); }
}

async function editerProduit(id) {
  try {
    const rep = await fetch(`/api/produit/${id}`);
    const p   = await rep.json();

    ADMIN.editId   = id;
    ADMIN.couleurs = p.couleurs || [];
    ADMIN.pointures = p.tailles || [];
    ADMIN.tailles   = p.tailles || [];

    document.getElementById("modal-titre").textContent = `✏️ Modifier "${p.nom}"`;
    document.getElementById("f-nom").value       = p.nom || "";
    document.getElementById("f-prix").value      = p.prix || "";
    document.getElementById("f-prix-promo").value = p.prix_promo || "";
    document.getElementById("f-stock").value     = p.stock || "";
    document.getElementById("f-desc").value      = p.description || "";
    document.getElementById("f-genre").value     = p.genre || "femme";
    document.getElementById("f-badge").value     = p.badge || "";

    choisirType(p.categorie, document.querySelector(`.type-btn:nth-child(${["parfum","sac","chaussure","vetement"].indexOf(p.categorie)+1})`));
    rendreCouleurTags();
    rendreTailleTags();
    rendrePointureTags();

    document.getElementById("modal-bg").classList.add("show");
  } catch(e) { afficherToast("❌ Erreur chargement produit", "❌"); }
}

// ── Table commandes ────────────────────────────────────────────
async function chargerTableCommandes() {
  try {
    const rep   = await fetch("/admin/api/commandes");
    const data  = await rep.json();
    const tbody = document.getElementById("tbody-commandes");
    if(!tbody) return;
    const labelStatut = { en_attente:"⏳ En attente", confirmee:"✅ Confirmée", en_preparation:"📦 Préparation", livree:"🚚 Livrée", annulee:"❌ Annulée" };
    const classeStatut = { en_attente:"s-warn", confirmee:"s-ok", en_preparation:"s-info", livree:"s-ok", annulee:"s-info" };
    tbody.innerHTML = data.map(c => `
      <tr>
        <td style="font-weight:700;color:var(--or-sombre)">${c.numero}</td>
        <td>${c.client_nom}</td>
        <td>${c.client_telephone}</td>
        <td style="font-weight:700">${formaterPrix(c.total)}</td>
        <td>${{orange:"🟠 Orange",momo:"🟡 MoMo",wave:"🔵 Wave",whatsapp:"💬 WhatsApp"}[c.paiement]||c.paiement||"—"}</td>
        <td><span class="badge-statut ${classeStatut[c.statut]||"s-info"}">${labelStatut[c.statut]||c.statut}</span></td>
        <td>${c.cree_le}</td>
        <td>
          <select onchange="changerStatutCommande(${c.id}, this.value)" style="padding:5px 8px;border:1px solid var(--border);border-radius:8px;font-size:11px">
            ${["en_attente","confirmee","en_preparation","livree","annulee"].map(s =>
              `<option value="${s}" ${c.statut===s?"selected":""}>${labelStatut[s]}</option>`
            ).join("")}
          </select>
        </td>
      </tr>`
    ).join("") || `<tr><td colspan="8" style="text-align:center;padding:24px">Aucune commande</td></tr>`;
  } catch(e) { console.error("Erreur commandes:", e); }
}

async function changerStatutCommande(id, statut) {
  try {
    await fetch(`/admin/api/commande/statut/${id}`, {
      method:"POST",
      headers:{"Content-Type":"application/json"},
      body:JSON.stringify({statut})
    });
    afficherToast(`✅ Statut mis à jour`);
  } catch(e) { afficherToast("❌ Erreur", "❌"); }
}

// ── Table clients ─────────────────────────────────────────────
async function chargerTableClients() {
  try {
    const rep   = await fetch("/admin/api/clients");
    const data  = await rep.json();
    const tbody = document.getElementById("tbody-clients");
    if(!tbody) return;
    tbody.innerHTML = data.map(c => `
      <tr>
        <td>${c.prenom}</td>
        <td>${c.nom||"—"}</td>
        <td style="color:var(--or-sombre)">${c.email}</td>
        <td>${c.telephone||"—"}</td>
        <td>${c.interet||"—"}</td>
        <td><span class="badge-statut s-info">${c.source||"popup"}</span></td>
        <td style="text-align:center">${c.nb_commandes}</td>
        <td>${c.cree_le}</td>
      </tr>`
    ).join("") || `<tr><td colspan="8" style="text-align:center;padding:24px">Aucun client enregistré</td></tr>`;
  } catch(e) { console.error("Erreur clients:", e); }
}

// ── Stats marketing ───────────────────────────────────────────
async function chargerStatsClients() {
  try {
    const rep  = await fetch("/admin/api/clients");
    const data = await rep.json();
    const el   = document.getElementById("stats-clients");
    if(!el) return;
    const total   = data.length;
    const popup   = data.filter(c => c.source === "popup").length;
    const commande = data.filter(c => c.source === "commande").length;
    el.innerHTML = `
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px">
        <div style="background:var(--ivoire);border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--or)">${total}</div>
          <div style="font-size:10px;color:var(--brun-clair);text-transform:uppercase;letter-spacing:1px">Total</div>
        </div>
        <div style="background:var(--ivoire);border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--rose-sombre)">${popup}</div>
          <div style="font-size:10px;color:var(--brun-clair);text-transform:uppercase;letter-spacing:1px">Pop-up</div>
        </div>
        <div style="background:var(--ivoire);border-radius:8px;padding:12px;text-align:center">
          <div style="font-size:22px;font-weight:700;color:var(--vert)">${commande}</div>
          <div style="font-size:10px;color:var(--brun-clair);text-transform:uppercase;letter-spacing:1px">Commandes</div>
        </div>
      </div>`;
  } catch(e) {}
}

// ── Modal ajout / modification produit ───────────────────────
function ouvrirModalProduit() {
  ADMIN.editId    = null;
  ADMIN.couleurs  = [];
  ADMIN.pointures = [];
  ADMIN.tailles   = [];
  document.getElementById("modal-titre").textContent = "Nouvel article";
  document.getElementById("modal-bg").classList.add("show");
  // Remettre les champs à zéro
  ["f-nom","f-prix","f-prix-promo","f-stock","f-desc"].forEach(id => {
    const el = document.getElementById(id);
    if(el) el.value = "";
  });
  document.getElementById("photo-preview").style.display = "none";
  document.getElementById("upload-zone").classList.remove("has-img");
  document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".champs-type").forEach(el => el.style.display = "none");
  ADMIN.typeProduit = null;
  rendreCouleurTags(); rendreTailleTags(); rendrePointureTags();
}

function fermerModalProduit() {
  document.getElementById("modal-bg").classList.remove("show");
}

function choisirType(type, btn) {
  ADMIN.typeProduit = type;
  document.querySelectorAll(".type-btn").forEach(b => b.classList.remove("active"));
  if(btn) btn.classList.add("active");
  document.querySelectorAll(".champs-type").forEach(el => el.style.display = "none");
  const cible = document.getElementById("champs-" + type);
  if(cible) cible.style.display = "block";
}

function previewPhoto(input) {
  const file = input.files[0]; if(!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.getElementById("photo-preview");
    img.src = e.target.result;
    img.style.display = "block";
    document.getElementById("upload-zone").classList.add("has-img");
  };
  reader.readAsDataURL(file);
}

// Gestion des tags couleurs
function ajouterCouleurTag(e) {
  if(e.key !== "Enter" && e.key !== ",") return;
  e.preventDefault();
  const val = document.getElementById("input-couleur").value.trim();
  if(!val) return;
  const mapCouleurs = {
    noir:"#1a1a1a",blanc:"#ffffff",or:"#C9922A",rouge:"#E8341C",
    bleu:"#1E3A5F",vert:"#1E8A3C",caramel:"#D2691E",bordeaux:"#8B0000",
    rose:"#F2AEBB",gris:"#808080",marine:"#1E3A5F"
  };
  const hex = mapCouleurs[val.toLowerCase()] || "#C9922A";
  ajouterCouleurVite(hex, val);
  document.getElementById("input-couleur").value = "";
}
function ajouterCouleurVite(hex, nom) {
  if(ADMIN.couleurs.find(c => c.hex === hex)) return;
  ADMIN.couleurs.push({ hex, nom });
  rendreCouleurTags();
}
function retirerCouleur(i) { ADMIN.couleurs.splice(i, 1); rendreCouleurTags(); }
function rendreCouleurTags() {
  const wrap = document.getElementById("tags-couleurs");
  const input = document.getElementById("input-couleur");
  if(!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.couleurs.forEach((c,i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-couleur";
    tag.style.background = c.hex;
    tag.style.color = c.hex === "#ffffff" || c.hex === "#FBF3E8" ? "#333" : "white";
    tag.innerHTML = `${c.nom}<button onclick="retirerCouleur(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// Gestion des tags pointures
function ajouterPointureTag(e) {
  if(e.key !== "Enter") return; e.preventDefault();
  const val = document.getElementById("input-pointure").value.trim();
  if(!val || ADMIN.pointures.includes(val)) return;
  ADMIN.pointures.push(val);
  document.getElementById("input-pointure").value = "";
  rendrePointureTags();
}
function ajouterPointureVite(t) {
  if(!ADMIN.pointures.includes(t)) { ADMIN.pointures.push(t); rendrePointureTags(); }
}
function retirerPointure(i) { ADMIN.pointures.splice(i,1); rendrePointureTags(); }
function rendrePointureTags() {
  const wrap  = document.getElementById("tags-pointures");
  const input = document.getElementById("input-pointure");
  if(!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.pointures.forEach((t,i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-taille";
    tag.innerHTML = `${t}<button onclick="retirerPointure(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// Gestion des tags tailles vêtements
function ajouterTailleTag(e) {
  if(e.key !== "Enter") return; e.preventDefault();
  const val = document.getElementById("input-taille").value.trim();
  if(!val || ADMIN.tailles.includes(val)) return;
  ADMIN.tailles.push(val);
  document.getElementById("input-taille").value = "";
  rendreTailleTags();
}
function ajouterTailleVite(t) {
  if(!ADMIN.tailles.includes(t)) { ADMIN.tailles.push(t); rendreTailleTags(); }
}
function retirerTaille(i) { ADMIN.tailles.splice(i,1); rendreTailleTags(); }
function rendreTailleTags() {
  const wrap  = document.getElementById("tags-tailles");
  const input = document.getElementById("input-taille");
  if(!wrap || !input) return;
  wrap.innerHTML = "";
  ADMIN.tailles.forEach((t,i) => {
    const tag = document.createElement("span");
    tag.className = "tag-item tag-taille";
    tag.innerHTML = `${t}<button onclick="retirerTaille(${i})">✕</button>`;
    wrap.appendChild(tag);
  });
  wrap.appendChild(input);
}

// ── Sauvegarder un produit ────────────────────────────────────
async function sauvegarderProduit() {
  const nom      = document.getElementById("f-nom")?.value.trim();
  const prix     = document.getElementById("f-prix")?.value;
  const stock    = document.getElementById("f-stock")?.value;

  if(!nom || !prix) { afficherToast("⚠️ Nom et prix obligatoires", "⚠️"); return; }
  if(!ADMIN.typeProduit) { afficherToast("⚠️ Choisissez un type d'article", "⚠️"); return; }

  // Construire les attributs selon le type
  let attributs = {};
  if(ADMIN.typeProduit === "parfum") {
    attributs = {
      ml      : document.getElementById("f-ml")?.value || "",
      olfactif: document.getElementById("f-olfactif")?.value || "",
      tenue   : document.getElementById("f-tenue")?.value || "",
    };
  } else if(ADMIN.typeProduit === "sac") {
    attributs = {
      matiere   : document.getElementById("f-matiere-sac")?.value || "",
      dimensions: document.getElementById("f-dims")?.value || "",
    };
  } else if(ADMIN.typeProduit === "chaussure") {
    attributs = {
      matiere: document.getElementById("f-matiere-chaussure")?.value || "",
      talon  : document.getElementById("f-talon")?.value || "0",
    };
  } else if(ADMIN.typeProduit === "vetement") {
    attributs = {
      tissu      : document.getElementById("f-tissu")?.value || "",
      type_vetement: document.getElementById("f-type-vet")?.value || "",
    };
  }

  const tailles = ADMIN.typeProduit === "chaussure" ? ADMIN.pointures : ADMIN.tailles;

  // Construire le FormData (pour envoyer la photo + les champs)
  const fd = new FormData();
  fd.append("nom",        nom);
  fd.append("categorie",  ADMIN.typeProduit);
  fd.append("genre",      document.getElementById("f-genre")?.value || "mixte");
  fd.append("prix",       prix);
  fd.append("prix_promo", document.getElementById("f-prix-promo")?.value || "");
  fd.append("stock",      stock || "0");
  fd.append("description",document.getElementById("f-desc")?.value || "");
  fd.append("badge",      document.getElementById("f-badge")?.value || "");
  fd.append("couleurs",   JSON.stringify(ADMIN.couleurs));
  fd.append("tailles",    JSON.stringify(tailles));
  fd.append("attributs",  JSON.stringify(attributs));

  const photoInput = document.getElementById("photo-input");
  if(photoInput?.files[0]) fd.append("photo", photoInput.files[0]);

  const url = ADMIN.editId
    ? `/admin/api/produit/modifier/${ADMIN.editId}`
    : `/admin/api/produit/ajouter`;

  try {
    const rep  = await fetch(url, { method:"POST", body:fd });
    const data = await rep.json();
    if(data.succes) {
      fermerModalProduit();
      chargerTableProduits();
      afficherToast(`✅ "${nom}" enregistré avec succès !`);
    } else {
      afficherToast("❌ " + (data.erreur || "Erreur"), "❌");
    }
  } catch(e) { afficherToast("❌ Erreur réseau", "❌"); }
}

// ── Ticker admin ──────────────────────────────────────────────
function ajouterTicker() {
  const texte = document.getElementById("new-ticker")?.value.trim();
  if(!texte) return;
  afficherToast("📢 Message ajouté au bandeau");
  document.getElementById("new-ticker").value = "";
}

// ── Initialisation ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  chargerTableProduits();  // charger le tableau produits dès l'ouverture
  document.getElementById("modal-bg")?.addEventListener("click", function(e) {
    if(e.target === this) fermerModalProduit();
  });
});
