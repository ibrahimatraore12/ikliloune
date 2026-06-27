"""
seed_catalogue_complet.py — IKLILOUNE
======================================
Import en masse de TOUS les articles + photos vers Cloudinary + base de données.

Usage sur la VM GCP :
    cd ~/IKLILOUNE
    source ~/.pyenv/versions/ikliloune-env/bin/activate

    # Copier d'abord ce script ET le dossier produits_webp/ dans ~/IKLILOUNE/
    # puis :

    python seed_catalogue_complet.py --preview          # Voir les articles
    python seed_catalogue_complet.py --upload-only      # Upload photos Cloudinary seulement
    python seed_catalogue_complet.py                    # Upload + seed base de données
    python seed_catalogue_complet.py --reset            # Reset complet + réimport

Prérequis :
    pip install cloudinary pillow
    Variable d'env CLOUDINARY_URL définie (dans .env ou Render)
"""

import os, sys, json, argparse
from pathlib import Path

# ─── Chemin vers les photos WebP ─────────────────────────────────────────────
# Modifier si nécessaire — doit pointer vers le dossier produits_webp/
PHOTOS_DIR = Path(__file__).parent   # même dossier que ce script

# ─── Mapping couleur → hex ───────────────────────────────────────────────────
COULEUR_HEX = {
    'Bordeaux':          '#722F37', 'Rouge':             '#C0392B',
    'Rouge/Bordeaux':    '#8B1A1A', 'Rouge/Caramel':     '#B94040',
    'Fuchsia':           '#E91E8C', 'Fuchsia/Prune':     '#C2185B',
    'Violet/Noir':       '#6A0DAD', 'Violet':            '#7B2FBE',
    'Marine':            '#1B3A6B', 'Bleu Ciel':         '#87CEEB',
    'Marine/Blanc/Caramel': '#1B3A6B',
    'Blanc/Marine':      '#F5F5F5', 'Blanc/Noir':        '#F8F8F8',
    'Blanc Nacré':       '#F9F6EE',
    'Noir':              '#1A1A1A', 'Noir/Beige':        '#1A1A1A',
    'Caramel':           '#C68642', 'Caramel/Naturel':   '#D2A679',
    'Marron/Caramel':    '#7B4F2E', 'Orange/Caramel':    '#D46A2A',
    'Doré/Caramel':      '#C9A84C', 'Doré':              '#C9A84C',
    'Gris/Caramel':      '#9E9E9E', 'Argent':            '#C0C0C0',
    'Bronze':            '#CD7F32', 'Vert':              '#2E7D32',
    'Vert Émeraude':     '#006B3C',
    'Lilas':             '#C9A0DC',
    'Rose':              '#E8A0A0', 'Rose Gold':         '#E8B4A0',
    'Champagne':         '#F7E7CE',
    'Multicolore':       '#FF6B6B',
    'Groupe':            '#9E9E9E',
    'Détail':            '#9E9E9E',
}

# ─── Catalogue complet IKLILOUNE ─────────────────────────────────────────────
# Généré depuis l'analyse des 61 photos.
# Chaque entrée = 1 article dans la base (1 photo principale, toutes couleurs listées).
# ─────────────────────────────────────────────────────────────────────────────

CATALOGUE = [

    # ══════════════════════════════════════════════════════════════════════
    # SACS FEMME
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Sac Tom&Eva Y-Lock',
        'description': 'Sac à main Tom&Eva Paris en cuir grainé souple. '
                       'Serrure originale en Y, anse rigide et longue bandoulière amovible. '
                       'Style élégant et pratique pour toutes occasions.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        35000,
        'prix_promo':  None,
        'stock':       10,
        'badge':       'best_seller',
        'couleurs':    ['Bordeaux', 'Noir', 'Marine', 'Kaki'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-tomeva-ylock-bordeaux.webp',
    },
    {
        'nom':         'Sac Tom&Eva Chevron Tressé',
        'description': 'Sac Tom&Eva Paris au corps en raphia naturel tressé et rabat en cuir lisse en V. '
                       'Fermeture centrale push-lock dorée, anse rigide et bandoulière. '
                       'Parfait pour un look estival ou chic décontracté.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        35000,
        'prix_promo':  None,
        'stock':       8,
        'badge':       'nouveau',
        'couleurs':    ['Caramel/Naturel', 'Rouge/Bordeaux', 'Fuchsia/Prune'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-tomeva-chevron-caramel.webp',
    },
    {
        'nom':         'Sac Tom&Eva Baguette Snake',
        'description': 'Sac baguette Tom&Eva Paris en cuir texturé serpent bicolore. '
                       'Rabat structuré, fermeture push-lock, anse d\'épaule unique. '
                       'Style contemporain et affirmé.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        30000,
        'prix_promo':  None,
        'stock':       6,
        'badge':       'nouveau',
        'couleurs':    ['Marron/Caramel', 'Bordeaux'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-tomeva-baguette-marron.webp',
    },
    {
        'nom':         'Sac Tom&Eva Bicolore Violet',
        'description': 'Sac à main Tom&Eva Paris en cuir lisse bicolore violet et noir. '
                       'Poignée rigide arrondie haut de gamme, fermeture pression, '
                       'bandoulière réglable incluse. Pièce unique et audacieuse.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        30000,
        'prix_promo':  None,
        'stock':       4,
        'badge':       'nouveau',
        'couleurs':    ['Violet/Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-tomeva-bicolore-violet.webp',
    },
    {
        'nom':         'Sac Jacques Esterel Tote',
        'description': 'Grand sac tote Jacques Esterel Paris en cuir grainé bicolore. '
                       'Anneaux dorés, deux anses, bandoulière amovible. '
                       'Capacité généreuse, idéal au quotidien et en voyage.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        25000,
        'prix_promo':  None,
        'stock':       12,
        'badge':       'best_seller',
        'couleurs':    ['Noir', 'Marine', 'Rouge/Caramel'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-jesterel-tote-noir.webp',
    },
    {
        'nom':         'Mini Sac Jacques Esterel Kelly',
        'description': 'Mini sac à main structuré Jacques Esterel Paris, style Kelly. '
                       'Fermoir doré orné, anse rigide et chaîne bandoulière. '
                       'Parfait pour soirées, cérémonies et sorties chic.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        22000,
        'prix_promo':  None,
        'stock':       10,
        'badge':       'best_seller',
        'couleurs':    ['Blanc/Noir', 'Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-jesterel-kelly-blanc-noir.webp',
    },
    {
        'nom':         'Sac Jacques Esterel Docteur',
        'description': 'Sac style docteur Jacques Esterel Paris, rabat bicolore élégant. '
                       'Fermeture tournante dorée, anse courte et longue bandoulière. '
                       'Disponible en 4 coloris. Chic et structuré.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        28000,
        'prix_promo':  None,
        'stock':       15,
        'badge':       'best_seller',
        'couleurs':    ['Orange/Caramel', 'Blanc/Marine', 'Doré/Caramel', 'Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-jesterel-docteur-dore.webp',
    },
    {
        'nom':         'Sac Jacques Esterel Selle',
        'description': 'Sac bandoulière selle Jacques Esterel Paris, cuir bicolore patchwork. '
                       'Style contemporain et original, fermeture zippée, '
                       'bandoulière réglable. Léger et pratique.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        20000,
        'prix_promo':  None,
        'stock':       9,
        'badge':       'nouveau',
        'couleurs':    ['Marine/Blanc/Caramel', 'Noir/Beige', 'Gris/Caramel'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-jesterel-selle-marine.webp',
    },
    {
        'nom':         'Sac Gallantry Tote Anneau',
        'description': 'Grand sac tote Gallantry Paris en cuir grainé, '
                       'anneau doré central iconique, deux anses confortables. '
                       'Élégant et spacieux pour un usage quotidien sophistiqué.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        30000,
        'prix_promo':  None,
        'stock':       6,
        'badge':       'nouveau',
        'couleurs':    ['Noir', 'Vert'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-gallantry-tote-anneau-noir.webp',
    },
    {
        'nom':         'Sac Gallantry Croco',
        'description': 'Sac Gallantry Paris en cuir verni motif crocodile. '
                       'Anneau doré central, double anse, intérieur spacieux. '
                       'Un classique intemporel revisité avec élégance.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        28000,
        'prix_promo':  None,
        'stock':       5,
        'badge':       'nouveau',
        'couleurs':    ['Vert', 'Noir', 'Rouge'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-gallantry-croco-vert.webp',
    },
    {
        'nom':         'Sac Gallantry Shopping Matelassé',
        'description': 'Grand sac shopping Gallantry Paris en cuir matelassé souple. '
                       'Chaîne dorée avec breloques, double anse épaule. '
                       'Idéal pour les courses, le bureau ou les sorties. '
                       'Breloque pompon offerte.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        20000,
        'prix_promo':  None,
        'stock':       18,
        'badge':       'best_seller',
        'couleurs':    ['Rouge', 'Marine', 'Fuchsia'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-gallantry-shopping-fuchsia.webp',
    },
    {
        'nom':         'Mini Sac à Main Rivets',
        'description': 'Mini sac à main orné de rivets argentés tout autour. '
                       'Anse rigide colorée assortie, fermeture aimantée. '
                       'Tendance et fun, parfait pour les soirées entre amies.',
        'categorie':   'sac',
        'genre':       'femme',
        'prix':        15000,
        'prix_promo':  None,
        'stock':       12,
        'badge':       'nouveau',
        'couleurs':    ['Bleu Ciel', 'Rouge', 'Lilas'],
        'tailles':     ['Taille unique'],
        'photo_file':  'sac-rivets-bleu-rouge-lilas.webp',
    },

    # ══════════════════════════════════════════════════════════════════════
    # POCHETTES & MINAUDIÈRES SOIRÉE (Femme)
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Minaudière Strass Cristal',
        'description': 'Minaudière soirée entièrement ornée de cristaux scintillants. '
                       'Fermoir pression arrondi, anse métal. '
                       'Lumineuse et élégante pour mariages, gala et sorties.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        20000,
        'prix_promo':  None,
        'stock':       8,
        'badge':       'best_seller',
        'couleurs':    ['Argent', 'Rose Gold', 'Champagne'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-strass-cristal.webp',
    },
    {
        'nom':         'Minaudière Tom&Eva Strass',
        'description': 'Minaudière ovale Tom&Eva Paris entièrement couverte de strass scintillants. '
                       'Anse transparente rigide, fermeture clic. '
                       'La touche glamour pour vos soirées.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        25000,
        'prix_promo':  None,
        'stock':       6,
        'badge':       'nouveau',
        'couleurs':    ['Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-tomeva-strass-noir.webp',
    },
    {
        'nom':         'Minaudière Bijoux Ovale',
        'description': 'Minaudière ovale brodée de pierres semi-précieuses et strass. '
                       'Fermoir antique doré, doublure satinée. '
                       'Pièce d\'exception pour cérémonies et soirées de prestige.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        20000,
        'prix_promo':  None,
        'stock':       6,
        'badge':       'best_seller',
        'couleurs':    ['Vert Émeraude', 'Noir', 'Argent'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-bijoux-ovale-verte.webp',
    },
    {
        'nom':         'Minaudière Strass Rectangle',
        'description': 'Minaudière rigide rectangle ornée de strass, '
                       'fermeture magnétique discrète. '
                       'Style soirée intemporel, s\'adapte à toutes les tenues.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        20000,
        'prix_promo':  None,
        'stock':       8,
        'badge':       'nouveau',
        'couleurs':    ['Doré', 'Argent', 'Noir', 'Multicolore'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-strass-rectangle-groupe.webp',
    },
    {
        'nom':         'Minaudière Perles Nacrées',
        'description': 'Minaudière de cérémonie ornée de perles nacrées cousues à la main. '
                       'Anse métal argenté, fermoir délicat. '
                       'Le choix parfait pour mariages, baptêmes et grandes occasions.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        25000,
        'prix_promo':  None,
        'stock':       5,
        'badge':       'best_seller',
        'couleurs':    ['Blanc Nacré', 'Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-perles-blanc.webp',
    },
    {
        'nom':         'Minaudière Métal Bronze',
        'description': 'Minaudière soirée structure rigide spiralée bronze/cuivré. '
                       'Reflets métalliques warm gold, anse intégrée. '
                       'Original et luxueux, pour se démarquer en soirée.',
        'categorie':   'pochette',
        'genre':       'femme',
        'prix':        18000,
        'prix_promo':  None,
        'stock':       4,
        'badge':       'nouveau',
        'couleurs':    ['Bronze'],
        'tailles':     ['Taille unique'],
        'photo_file':  'minaudiere-metal-bronze.webp',
    },

    # ══════════════════════════════════════════════════════════════════════
    # MAROQUINERIE
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Portefeuille Gallantry Paris',
        'description': 'Portefeuille Gallantry Paris en cuir grainé souple. '
                       'Zip inférieur, nombreux rangements cartes et billets, '
                       'compartiment monnaie. Pratique et élégant au quotidien.',
        'categorie':   'maroquinerie',
        'genre':       'femme',
        'prix':        15000,
        'prix_promo':  None,
        'stock':       20,
        'badge':       'best_seller',
        'couleurs':    ['Caramel', 'Noir', 'Rouge', 'Blanc'],
        'tailles':     ['Taille unique'],
        'photo_file':  'portefeuille-gallantry-groupe.webp',
    },

    # ══════════════════════════════════════════════════════════════════════
    # PARFUMS FEMME
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Parfum Suddenly Diamonds',
        'description': 'Suddenly Fragrances Diamonds, Eau de Parfum 75ml. '
                       'Notes florales fraîches et poudrées. '
                       'Un classique accessible pour la femme moderne.',
        'categorie':   'parfum',
        'genre':       'femme',
        'prix':        10000,
        'prix_promo':  None,
        'stock':       25,
        'badge':       'best_seller',
        'couleurs':    ['Blanc'],
        'tailles':     ['75ml'],
        'photo_file':  'parfum-suddenly-diamonds-lovely-chalou.webp',
    },
    {
        'nom':         'Parfum Suddenly Lovely',
        'description': 'Suddenly Fragrances Lovely, Eau de Parfum 75ml. '
                       'Fragrance florale douce et enveloppante. '
                       'Légère et féminine, idéale au quotidien.',
        'categorie':   'parfum',
        'genre':       'femme',
        'prix':        10000,
        'prix_promo':  None,
        'stock':       20,
        'badge':       'best_seller',
        'couleurs':    ['Blanc'],
        'tailles':     ['75ml'],
        'photo_file':  'parfum-suddenly-groupe.webp',
    },
    {
        'nom':         'Parfum Suddenly Chalou',
        'description': 'Suddenly Fragrances Chalou, Eau de Parfum 75ml. '
                       'Notes de rose poudré et bois de santal. '
                       'Élégant et romantique.',
        'categorie':   'parfum',
        'genre':       'femme',
        'prix':        10000,
        'prix_promo':  None,
        'stock':       20,
        'badge':       'best_seller',
        'couleurs':    ['Rose'],
        'tailles':     ['75ml'],
        'photo_file':  'parfum-suddenly-groupe.webp',
    },
    {
        'nom':         'Brume Parfumée Corps Montagne',
        'description': 'Brume parfumée Corps Montagne 250ml. '
                       'Collection: Bellaya, Rêuh Al Arab, Rouge Absolu, '
                       'Mya Belle, Victoria, Mykonos. '
                       'Légère et longue tenue. Préciser la fragrance à la commande.',
        'categorie':   'parfum',
        'genre':       'femme',
        'prix':        7000,
        'prix_promo':  None,
        'stock':       30,
        'badge':       'best_seller',
        'couleurs':    ['Multicolore'],
        'tailles':     ['250ml'],
        'photo_file':  'parfum-brume-corps-montagne.webp',
    },
    {
        'nom':         'Parfum El Nabil',
        'description': 'El Nabil Luxury For Everyone, Eau de Parfum 65ml. '
                       'Collection: Musc Night, Musc Mayssane, Lune de Miel. '
                       'Fragrances orientales raffinées. Préciser le modèle à la commande.',
        'categorie':   'parfum',
        'genre':       'mixte',
        'prix':        15000,
        'prix_promo':  None,
        'stock':       15,
        'badge':       'nouveau',
        'couleurs':    ['Blanc'],
        'tailles':     ['65ml'],
        'photo_file':  'parfum-elnabil-groupe.webp',
    },
    {
        'nom':         'Parfum Zara Femme',
        'description': 'Zara Woman Summer Collection, Eau de Parfum. '
                       'Collection: Pink Flambé, Tuberose Summer, '
                       'Gardenia & Orchid, Gardenia & Wonder Rose. '
                       'Fragrances florales et printanières. Préciser le modèle.',
        'categorie':   'parfum',
        'genre':       'femme',
        'prix':        17000,
        'prix_promo':  None,
        'stock':       12,
        'badge':       'nouveau',
        'couleurs':    ['Multicolore'],
        'tailles':     ['80ml', '180ml'],
        'photo_file':  'parfum-zara-femme-groupe.webp',
    },

    # ══════════════════════════════════════════════════════════════════════
    # PARFUMS HOMME
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Parfum G.Bellini Homme',
        'description': 'G.Bellini Fragrances, Eau de Parfum 75ml pour homme. '
                       'One Fragrance (notes boisées dorées) et Deep (intense et mystérieux). '
                       'Préciser le modèle à la commande.',
        'categorie':   'parfum',
        'genre':       'homme',
        'prix':        10000,
        'prix_promo':  None,
        'stock':       20,
        'badge':       'best_seller',
        'couleurs':    ['Doré', 'Noir'],
        'tailles':     ['75ml'],
        'photo_file':  'parfum-gbellini-homme.webp',
    },
    {
        'nom':         'Parfum El Nabil Iconic Oud',
        'description': 'El Nabil Iconic Oud, Eau de Parfum 65ml. '
                       'Fragrance orientale boisée au bois de oud authentique. '
                       'Longue tenue exceptionnelle. Pour homme et mixte.',
        'categorie':   'parfum',
        'genre':       'homme',
        'prix':        30000,
        'prix_promo':  None,
        'stock':       8,
        'badge':       'nouveau',
        'couleurs':    ['Doré'],
        'tailles':     ['65ml'],
        'photo_file':  'parfum-elnabil-oud-homme.webp',
    },
    {
        'nom':         'Parfum Zara Homme',
        'description': 'Zara Man Collection, Eau de Toilette/Parfum. '
                       'Collection: Seoul, Blue Spirit, Silver, '
                       '800 Black Winter, Navy Black. '
                       'Fragrances modernes et tendance. Préciser le modèle.',
        'categorie':   'parfum',
        'genre':       'homme',
        'prix':        17000,
        'prix_promo':  None,
        'stock':       12,
        'badge':       'nouveau',
        'couleurs':    ['Multicolore'],
        'tailles':     ['100ml'],
        'photo_file':  'parfum-zara-homme-groupe.webp',
    },

    # ══════════════════════════════════════════════════════════════════════
    # ACCESSOIRES HOMME
    # ══════════════════════════════════════════════════════════════════════
    {
        'nom':         'Bracelet Cuir Homme',
        'description': 'Bracelets cuir tressé pour homme. '
                       'Modèles: ancre argentée sur cuir marron, '
                       'cuir noir tressé, ou perles naturelles œil de tigre. '
                       'Préciser le modèle à la commande.',
        'categorie':   'accessoire',
        'genre':       'homme',
        'prix':        10000,
        'prix_promo':  None,
        'stock':       15,
        'badge':       'nouveau',
        'couleurs':    ['Marron/Caramel', 'Noir'],
        'tailles':     ['Taille unique'],
        'photo_file':  'bracelet-cuir-homme.webp',
    },
]


# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def _couleurs_json(couleurs: list) -> str:
    import json
    result = []
    for c in couleurs:
        hex_code = COULEUR_HEX.get(c, '#9E9E9E')
        result.append({'hex': hex_code, 'nom': c})
    return json.dumps(result, ensure_ascii=False)


def _tailles_json(tailles: list) -> str:
    import json
    return json.dumps(tailles, ensure_ascii=False)


def afficher_catalogue():
    cats = {}
    for p in CATALOGUE:
        cat = p['categorie']
        cats.setdefault(cat, []).append(p)

    print(f"\n{'='*65}")
    print(f"  IKLILOUNE — Catalogue complet ({len(CATALOGUE)} articles)")
    print(f"{'='*65}")
    for cat, items in sorted(cats.items()):
        emoji = {'parfum': '🌸', 'sac': '👜', 'pochette': '✨',
                 'accessoire': '⌚', 'maroquinerie': '💼'}.get(cat, '📦')
        print(f"\n  {emoji} {cat.upper()} ({len(items)})")
        for p in items:
            couleurs = ', '.join(p['couleurs'])
            badge = f"[{p['genre'][:1].upper()}]"
            print(f"    {badge} {p['nom']:<40} {p['prix']:>8,} FCFA")
            print(f"       Couleurs: {couleurs}")
            print(f"       Photo   : {p['photo_file']}")
    print(f"\n{'='*65}\n")


def upload_cloudinary(image_bytes: bytes, nom_fichier: str) -> str:
    """Upload sur Cloudinary. Retourne l'URL sécurisée."""
    import cloudinary
    import cloudinary.uploader
    from pathlib import Path

    public_id = Path(nom_fichier).stem
    result = cloudinary.uploader.upload(
        image_bytes,
        folder='ikliloune/produits',
        public_id=public_id,
        format='webp',
        overwrite=True,
        transformation=[
            {'width': 800, 'height': 800, 'crop': 'fill', 'gravity': 'auto'},
            {'quality': 'auto:good'},
        ],
        resource_type='image'
    )
    return result['secure_url']


def importer_produits(reset=False, upload_only=False):
    """
    1. Upload les photos sur Cloudinary (ou stockage local)
    2. Insère les produits en base de données
    """
    import json as json_mod

    # ── Import Flask ────────────────────────────────────────────────────
    if not upload_only:
        sys.path.insert(0, '.')
        try:
            from main import creer_app
            from backend.database import db
            from backend.models.produit import Produit
        except ImportError as e:
            print(f"\n❌ Erreur import Flask : {e}")
            print("   Lance ce script depuis le dossier ~/IKLILOUNE avec l'env activé.")
            sys.exit(1)

        app = creer_app()

    # ── Cloudinary ──────────────────────────────────────────────────────
    mode_cloudinary = bool(os.environ.get('CLOUDINARY_URL'))
    if mode_cloudinary:
        try:
            import cloudinary
            print(f"  ☁️  Cloudinary détecté → photos uploadées dans le cloud")
        except ImportError:
            print(f"  ⚠️  CLOUDINARY_URL défini mais lib manquante → pip install cloudinary")
            mode_cloudinary = False
    else:
        print(f"  💾 Mode LOCAL → photos copiées dans static/images/produits/")

    results = []

    ctx = app.app_context() if not upload_only else _NullContext()
    with ctx:
        if not upload_only and reset:
            from backend.models.produit import Produit
            nb = Produit.query.count()
            Produit.query.delete()
            db.session.commit()
            print(f"\n  🗑️  {nb} produit(s) supprimé(s) (reset)\n")

        print(f"\n  Traitement de {len(CATALOGUE)} articles...\n")

        for p in CATALOGUE:
            photo_src = PHOTOS_DIR / p['photo_file']
            photo_ref = None

            # ── Upload photo ──────────────────────────────────────────
            if photo_src.exists():
                image_bytes = photo_src.read_bytes()

                if mode_cloudinary:
                    try:
                        url = upload_cloudinary(image_bytes, p['photo_file'])
                        photo_ref = url
                        print(f"  ☁️  Uploadé : {p['photo_file']}")
                    except Exception as e:
                        print(f"  ⚠️  Upload échoué ({p['photo_file']}) : {e}")
                        photo_ref = p['photo_file']
                else:
                    # Copie locale
                    if not upload_only:
                        dest_dir = Path('.') / 'static' / 'images' / 'produits'
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        dest = dest_dir / p['photo_file']
                        dest.write_bytes(image_bytes)
                    photo_ref = p['photo_file']
                    print(f"  💾 Copié  : {p['photo_file']}")
            else:
                print(f"  ⚠️  Photo manquante : {photo_src}")

            if upload_only:
                results.append({'nom': p['nom'], 'photo': photo_ref})
                continue

            # ── Insérer en base ───────────────────────────────────────
            from backend.models.produit import Produit
            existant = Produit.query.filter_by(nom=p['nom']).first()
            if existant and not reset:
                print(f"  ⏭️  Existe déjà : {p['nom']}")
                # Mettre à jour la photo si uploadée
                if photo_ref and photo_ref.startswith('http'):
                    existant.photo = photo_ref
                    db.session.commit()
                continue

            produit = Produit(
                nom           = p['nom'],
                description   = p['description'],
                categorie     = p['categorie'],
                genre         = p['genre'],
                prix          = p['prix'],
                prix_promo    = p.get('prix_promo'),
                stock         = p.get('stock', 10),
                badge         = p.get('badge'),
                couleurs_json = _couleurs_json(p.get('couleurs', [])),
                tailles_json  = _tailles_json(p.get('tailles', ['Taille unique'])),
                photo         = photo_ref,
                actif         = True,
            )
            db.session.add(produit)
            print(f"  ✅ Ajouté  : {p['nom']}")
            results.append({'nom': p['nom'], 'photo': photo_ref})

        if not upload_only:
            db.session.commit()
            total = Produit.query.count()
            print(f"\n  {'='*60}")
            print(f"  ✅ {len(results)} produit(s) traité(s)")
            print(f"  📦 Total en base : {total} produit(s)")
            print(f"\n  Prochaine étape :")
            print(f"  → Dashboard admin IKLILOUNE → Produits → vérifier")
            print(f"  {'='*60}\n")
        else:
            # Sauvegarder le mapping photo
            mapping = {r['nom']: r['photo'] for r in results}
            out = PHOTOS_DIR / 'photo_urls.json'
            with open(out, 'w', encoding='utf-8') as f:
                json_mod.dump(mapping, f, ensure_ascii=False, indent=2)
            print(f"\n  ✅ URLs sauvegardées dans {out}\n")


class _NullContext:
    def __enter__(self): return self
    def __exit__(self, *a): pass


# ─── Point d'entrée ──────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='IKLILOUNE — Import catalogue complet')
    parser.add_argument('--preview',     action='store_true', help='Voir le catalogue sans modifier')
    parser.add_argument('--upload-only', action='store_true', help='Upload photos seulement (pas de base)')
    parser.add_argument('--reset',       action='store_true', help='Supprimer tous les produits avant import')
    args = parser.parse_args()

    afficher_catalogue()

    if args.preview:
        print("  (Mode preview — aucune modification)\n")
        sys.exit(0)

    if args.reset:
        rep = input("\n  ⚠️  RESET : supprimer TOUS les produits existants ? [oui/non] : ")
        if rep.strip().lower() not in ('oui', 'o', 'yes'):
            print("  Annulé.")
            sys.exit(0)

    importer_produits(reset=args.reset, upload_only=args.upload_only)
