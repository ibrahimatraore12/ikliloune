// =============================================================
// boutique.js — JavaScript de la page client IKLILOUNE
// Gère : catalogue, panier, commande, pop-up, carrousel
// =============================================================

// ── État global de l'application ────────────────────────────
const ETAT = {
  produits     : [],     // tous les produits chargés depuis l'API
  panier       : [],     // articles dans le panier
  promoApplique: false,  // code promo actif ?
  slideActuel  : 0,      // slide du carrousel actuellement affiché
  tickerPause  : false,  // ticker en pause ?
};

// ── Utilitaires ──────────────────────────────────────────────

// Formate un prix en FCFA avec espace comme séparateur
function formaterPrix(n) {
  return new Intl.NumberFormat("fr-CI").format(n) + " FCFA";
}

// Label lisible pour une catégorie
function labelCat(c) {
  return { parfum:"Parfum", sac:"Sac", chaussure:"Chaussure", vetement:"Vêtement" }[c] || c;
}

// Label lisible pour un genre
function labelGenre(g) {
  return { femme:"🫧 Perle", homme:"🪸 Corail", mixte:"✨ Mixte" }[g] || g;
}

// Calcule la classe CSS de la barre de stock
function classeStock(stock) {
  if(stock > 10) return "haut";
  if(stock > 3)  return "moyen";
  return "faible";
}

// Label affiché pour le stock
function labelStock(stock) {
  if(stock === 0)  return "Rupture de stock";
  if(stock <= 3)   return `⚠️ Plus que ${stock} !`;
  if(stock <= 8)   return `${stock} disponibles`;
  return `${stock} en stock`;
}

// ── Toast notification ───────────────────────────────────────
let toastTimer;
function afficherToast(msg, icone = "✅") {
  const t = document.getElementById("toast");
  document.getElementById("toast-msg").textContent = msg;
  document.getElementById("toast-icone").textContent = icone;
  t.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("visible"), 3500);
}

// ── Ticker défilant ──────────────────────────────────────────
function toggleTicker() {
  ETAT.tickerPause = !ETAT.tickerPause;
  const wrap = document.getElementById("ticker-wrap");
  const btn  = document.getElementById("ticker-pause");
  wrap.classList.toggle("paused", ETAT.tickerPause);
  btn.textContent = ETAT.tickerPause ? "▶" : "⏸";
}

// ── Carrousel hero ───────────────────────────────────────────
function construireDots() {
  const dotsEl = document.getElementById("hero-dots");
  if(!dotsEl) return;
  dotsEl.innerHTML = [0,1,2].map((i) =>
    `<button class="hero-dot${i===0?" active":""}" onclick="allerSlide(${i})" aria-label="Slide ${i+1}"></button>`
  ).join("");
}

function allerSlide(n) {
  const total = 3;
  ETAT.slideActuel = (n + total) % total;
  const slides = document.getElementById("hero-slides");
  if(slides) slides.style.transform = `translateX(-${ETAT.slideActuel * 100}%)`;
  document.querySelectorAll(".hero-dot").forEach((d,i) =>
    d.classList.toggle("active", i === ETAT.slideActuel)
  );
}

function deplacerSlide(dir) { allerSlide(ETAT.slideActuel + dir); }

// Auto-défilement toutes les 5 secondes
setInterval(() => deplacerSlide(1), 5000);

// ── Menu mobile ──────────────────────────────────────────────
function toggleMenu() {
  document.getElementById("nav-menu").classList.toggle("open");
}

// ── Chargement des produits depuis l'API ─────────────────────
async function chargerProduits(params = {}) {
  const url = new URL("/api/produits", window.location.origin);
  Object.entries(params).forEach(([k,v]) => url.searchParams.set(k, v));

  try {
    const rep  = await fetch(url);
    const data = await rep.json();
    ETAT.produits = data.produits || [];
    afficherProduits(ETAT.produits);
  } catch(e) {
    document.getElementById("produits-grille").innerHTML =
      `<div class="chargement">Erreur de chargement. Vérifiez votre connexion.</div>`;
  }
}

// ── Rendu HTML d'une carte produit ───────────────────────────
function htmlCarte(p) {
  const pct    = Math.min(100, Math.round((p.stock / 20) * 100));
  const sClass = classeStock(p.stock);
  const sLabel = labelStock(p.stock);
  const isOut  = p.stock === 0;

  const badgeHtml = p.badge === "new"
    ? `<span class="badge badge-new">Nouveau</span>`
    : p.badge === "promo"
      ? `<span class="badge badge-promo">Promo</span>` : "";

  const oldPrixHtml = p.prix_promo
    ? `<span class="prix-old">${formaterPrix(p.prix)}</span>` : "";

  // Couleurs disponibles (max 4 + compteur)
  const couleursHtml = p.couleurs.length
    ? `<div class="carte-couleurs">
         <span class="couleur-lbl">Couleurs :</span>
         <div class="couleur-dots">
           ${p.couleurs.slice(0,4).map(c =>
             `<div class="couleur-dot" style="background:${c.hex}" title="${c.nom}"
                  onclick="event.stopPropagation();this.parentElement.querySelectorAll('.couleur-dot').forEach(d=>d.classList.remove('selected'));this.classList.add('selected')"></div>`
           ).join("")}
           ${p.couleurs.length > 4 ? `<span class="couleur-lbl">+${p.couleurs.length-4}</span>` : ""}
         </div>
       </div>` : "";

  // Tailles disponibles
  const taillesHtml = p.tailles.length
    ? `<div class="carte-tailles">
         ${p.tailles.map(t =>
           `<button class="taille-btn" onclick="event.stopPropagation();this.closest('.carte-tailles').querySelectorAll('.taille-btn').forEach(b=>b.classList.remove('selected'));this.classList.add('selected')">${t}</button>`
         ).join("")}
       </div>` : "";

  // Photo ou emoji
  const imgHtml = p.photo
    ? `<img class="carte-img" src="/static/images/produits/${p.photo}" alt="${p.nom}" loading="lazy">`
    : `<div class="carte-emoji">${ {parfum:"🌸",sac:"👜",chaussure:"👟",vetement:"👗"}[p.categorie] || "📦" }</div>`;

  return `
    <article class="carte-produit" aria-label="${p.nom}">
      <div class="carte-img-wrap">
        ${imgHtml}
        <div class="carte-badges">${badgeHtml}</div>
        <div class="stock-info">
          <div class="stock-lbl"><span>${sLabel}</span><span>${pct}%</span></div>
          <div class="stock-bar"><div class="stock-fill ${sClass}" style="width:${pct}%"></div></div>
        </div>
      </div>
      <div class="carte-body">
        <div class="carte-meta">
          <span class="carte-cat">${labelCat(p.categorie)}</span>
          <span style="color:var(--border)">·</span>
          <span class="carte-genre">${labelGenre(p.genre)}</span>
        </div>
        <h3 class="carte-nom">${p.nom}</h3>
        <p class="carte-desc">${p.description || ""}</p>
        ${couleursHtml}
        ${taillesHtml}
        <div class="carte-footer">
          <div class="carte-prix">
            <span class="prix-now">${formaterPrix(p.prix_actuel)}</span>
            ${oldPrixHtml}
          </div>
          <button class="btn-ajouter" onclick="ajouterAuPanier(${p.id})" ${isOut?"disabled":""}>
            🛒 Ajouter
          </button>
        </div>
      </div>
    </article>`;
}

function afficherProduits(liste) {
  const grille = document.getElementById("produits-grille");
  const count  = document.getElementById("produits-count");
  if(count) count.textContent = `(${liste.length} article${liste.length > 1 ? "s" : ""})`;

  if(!liste.length) {
    grille.innerHTML = `<div class="chargement">🔍 Aucun article trouvé pour ce filtre.</div>`;
    return;
  }
  grille.innerHTML = liste.map(htmlCarte).join("");
}

// ── Filtres ──────────────────────────────────────────────────
function filtrerCategorie(cat, btn) {
  if(btn) {
    document.querySelectorAll(".cat-pill").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }
  chargerProduits(cat !== "tous" ? { categorie: cat } : {});
}

function filtrerGenre(genre, btn) {
  if(btn) {
    document.querySelectorAll(".nav-lien").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  }
  chargerProduits(genre !== "tous" ? { genre } : {});
}

function rechercherProduits(q) {
  if(q.trim()) chargerProduits({ q });
  else chargerProduits({});
}

function trierProduits(critere) {
  let liste = [...ETAT.produits];
  if(critere === "prix-asc")  liste.sort((a,b) => a.prix_actuel - b.prix_actuel);
  if(critere === "prix-desc") liste.sort((a,b) => b.prix_actuel - a.prix_actuel);
  if(critere === "nouveau")   liste.sort((a,b) => (b.badge === "new") - (a.badge === "new"));
  afficherProduits(liste);
}

// ── Panier ───────────────────────────────────────────────────
function ajouterAuPanier(id) {
  const produit = ETAT.produits.find(p => p.id === id);
  if(!produit || !produit.en_stock) return;

  const exist = ETAT.panier.find(item => item.id === id);
  if(exist) exist.qty++;
  else ETAT.panier.push({ ...produit, qty: 1 });

  mettreAJourBadgePanier();
  afficherToast(`✅ "${produit.nom}" ajouté au panier`);
}

function mettreAJourBadgePanier() {
  const total = ETAT.panier.reduce((s,x) => s + x.qty, 0);
  const badge = document.getElementById("panier-badge");
  if(badge) badge.textContent = total;
}

function ouvrirPanier() {
  document.getElementById("panier-overlay").classList.add("show");
  document.getElementById("panier-panel").classList.add("open");
  rendrePanier();
}

function fermerPanier() {
  document.getElementById("panier-overlay").classList.remove("show");
  document.getElementById("panier-panel").classList.remove("open");
}

function rendrePanier() {
  const vide    = document.getElementById("panier-vide");
  const artEl   = document.getElementById("panier-articles");
  const footer  = document.getElementById("panier-footer");

  if(!ETAT.panier.length) {
    vide.style.display  = "block";
    artEl.innerHTML     = "";
    footer.style.display = "none";
    return;
  }

  vide.style.display   = "none";
  footer.style.display = "block";

  // Calculs
  const sousTotal = ETAT.panier.reduce((s,x) => s + x.prix_actuel * x.qty, 0);
  const remise    = ETAT.promoApplique ? Math.round(sousTotal * 0.05) : 0;
  const total     = sousTotal - remise;

  document.getElementById("panier-sous-total").textContent = formaterPrix(sousTotal);
  document.getElementById("panier-total-final").textContent = formaterPrix(total);

  const remiseLigne = document.getElementById("panier-remise-ligne");
  if(ETAT.promoApplique) {
    remiseLigne.style.display = "flex";
    document.getElementById("panier-remise-montant").textContent = "- " + formaterPrix(remise);
  } else {
    remiseLigne.style.display = "none";
  }

  // HTML des articles
  artEl.innerHTML = ETAT.panier.map(item => `
    <div class="panier-article">
      <div class="art-img">
        ${item.photo
          ? `<img src="/static/images/produits/${item.photo}" style="width:100%;height:100%;object-fit:cover;border-radius:6px" alt="${item.nom}">`
          : ({parfum:"��",sac:"👜",chaussure:"👟",vetement:"👗"}[item.categorie] || "📦")}
      </div>
      <div class="art-info">
        <div class="art-nom">${item.nom}</div>
        <div class="art-meta">${labelCat(item.categorie)} · ${formaterPrix(item.prix_actuel)}/unité</div>
        <div class="qty-row">
          <button class="qty-btn" onclick="changerQty(${item.id}, -1)">−</button>
          <span class="qty-val">${item.qty}</span>
          <button class="qty-btn" onclick="changerQty(${item.id}, 1)">+</button>
        </div>
      </div>
      <div class="art-droite">
        <div class="art-prix">${formaterPrix(item.prix_actuel * item.qty)}</div>
        <button class="btn-del" onclick="retirerDuPanier(${item.id})" aria-label="Supprimer">🗑️</button>
      </div>
    </div>`
  ).join("");
}

function changerQty(id, delta) {
  const item = ETAT.panier.find(x => x.id === id);
  if(!item) return;
  item.qty += delta;
  if(item.qty <= 0) retirerDuPanier(id);
  else { mettreAJourBadgePanier(); rendrePanier(); }
}

function retirerDuPanier(id) {
  ETAT.panier = ETAT.panier.filter(x => x.id !== id);
  mettreAJourBadgePanier();
  rendrePanier();
}

function appliquerPromo(code) {
  const codesValides = ["IKLI5", "BIENVENUE"];
  const actif = codesValides.includes(code.toUpperCase());
  if(actif !== ETAT.promoApplique) {
    ETAT.promoApplique = actif;
    rendrePanier();
    if(actif) afficherToast("🎉 Code promo appliqué ! -5% sur votre commande");
  }
}

// ── Commande ─────────────────────────────────────────────────
async function validerCommande() {
  if(!ETAT.panier.length) { afficherToast("⚠️ Votre panier est vide", "⚠️"); return; }

  const nom     = document.getElementById("c-nom").value.trim();
  const tel     = document.getElementById("c-tel").value.trim();
  const email   = document.getElementById("c-email").value.trim();
  const adresse = document.getElementById("c-adresse").value.trim();
  const paiement = document.querySelector("input[name='pay']:checked")?.value || "orange";

  if(!nom || !tel) { afficherToast("⚠️ Nom et téléphone obligatoires", "⚠️"); return; }

  const sousTotal = ETAT.panier.reduce((s,x) => s + x.prix_actuel * x.qty, 0);
  const remise    = ETAT.promoApplique ? Math.round(sousTotal * 0.05) : 0;

  const payload = {
    client_nom       : nom,
    client_telephone : tel,
    client_email     : email,
    client_adresse   : adresse,
    paiement,
    articles : ETAT.panier.map(x => ({
      id: x.id, nom: x.nom, categorie: x.categorie,
      prix_actuel: x.prix_actuel, qty: x.qty,
      photo: x.photo || ""
    })),
    total  : sousTotal - remise,
    remise,
  };

  try {
    const rep  = await fetch("/api/commande", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(payload),
    });
    const data = await rep.json();

    if(data.succes) {
      fermerPanier();
      document.getElementById("confirm-num").textContent = "N° " + data.numero;
      document.getElementById("btn-wa-confirm").onclick = () => window.open(data.url_whatsapp, "_blank");
      document.getElementById("confirm-overlay").classList.add("show");
      // Vider le panier après confirmation
      ETAT.panier = [];
      mettreAJourBadgePanier();
    } else {
      afficherToast("❌ Erreur : " + (data.erreur || "Réessayez"), "❌");
    }
  } catch(e) {
    afficherToast("❌ Erreur réseau. Essayez WhatsApp.", "❌");
  }
}

function commanderWhatsApp() {
  const nom     = document.getElementById("c-nom")?.value || "";
  const tel     = document.getElementById("c-tel")?.value || "";
  const adresse = document.getElementById("c-adresse")?.value || "";
  const paiement = document.querySelector("input[name='pay']:checked")?.value || "";

  const lignes = ETAT.panier.map(x =>
    `• ${x.nom} × ${x.qty} = ${formaterPrix(x.prix_actuel * x.qty)}`
  ).join("\n") || "Voir ma sélection";

  const sousTotal = ETAT.panier.reduce((s,x) => s + x.prix_actuel * x.qty, 0);
  const remise    = ETAT.promoApplique ? Math.round(sousTotal * 0.05) : 0;
  const total     = sousTotal - remise;

  const msg = encodeURIComponent(
    `Bonjour IKLILOUNE 🌸\n\n*Ma commande :*\n${lignes}\n\n💰 *Total : ${formaterPrix(total)}*\n👤 ${nom}\n📞 ${tel}\n📍 ${adresse}\n💳 ${paiement}\n\nMerci !`
  );
  window.open(`https://wa.me/2250104144141?text=${msg}`, "_blank");
}

function fermerConfirm() {
  document.getElementById("confirm-overlay").classList.remove("show");
}

// ── Pop-up email ──────────────────────────────────────────────
let popupMontree = false;

function afficherPopup() {
  if(popupMontree || sessionStorage.getItem("popup_vu")) return;
  popupMontree = true;
  document.getElementById("popup-overlay").classList.add("show");
}

function fermerPopup() {
  document.getElementById("popup-overlay").classList.remove("show");
  sessionStorage.setItem("popup_vu", "1");  // ne plus montrer dans cette session
}

async function soumettrePopup(e) {
  e.preventDefault();
  const payload = {
    prenom  : document.getElementById("p-prenom").value.trim(),
    nom     : document.getElementById("p-nom").value.trim(),
    email   : document.getElementById("p-email").value.trim(),
    telephone: document.getElementById("p-tel").value.trim(),
    interet : document.getElementById("p-interet").value,
  };
  try {
    const rep  = await fetch("/api/lead", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify(payload),
    });
    const data = await rep.json();
    fermerPopup();
    // Appliquer automatiquement le code promo
    if(data.code) {
      const inputPromo = document.getElementById("c-promo");
      if(inputPromo) { inputPromo.value = data.code; appliquerPromo(data.code); }
    }
    afficherToast(`🎁 Bienvenue ${payload.prenom} ! Code ${data.code || "IKLI5"} appliqué.`);
  } catch(e) {
    afficherToast("✅ Inscription réussie ! Code IKLI5 pour -5%");
    fermerPopup();
  }
}

// ── Initialisation ────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  construireDots();
  chargerProduits();                     // charger le catalogue
  setTimeout(afficherPopup, 9000);      // pop-up après 9 secondes

  // Fermer les overlays en cliquant dessus
  document.getElementById("confirm-overlay")?.addEventListener("click", function(e) {
    if(e.target === this) fermerConfirm();
  });
  document.getElementById("popup-overlay")?.addEventListener("click", function(e) {
    if(e.target === this) fermerPopup();
  });
});
