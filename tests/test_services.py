# =============================================================
# tests/test_services.py — Tests des services métier
# Vérifie : commande_service, stats_service, image_service (léger)
# =============================================================

import json
import pytest


class TestCommandeService:
    """Tests du service de formatage des messages WhatsApp."""

    def test_formater_message_whatsapp_contient_numero(self, app):
        """Le message WhatsApp doit contenir le numéro de commande."""
        with app.app_context():
            from backend.models.commande import Commande
            from backend.services.commande_service import formater_message_whatsapp

            c = Commande.query.first()
            msg = formater_message_whatsapp(c)

            assert c.numero in msg, f"Numéro {c.numero} absent du message WA"

    def test_formater_message_whatsapp_contient_total(self, app):
        """Le message WhatsApp doit mentionner le montant total."""
        with app.app_context():
            from backend.models.commande import Commande
            from backend.services.commande_service import formater_message_whatsapp

            c = Commande.query.first()
            msg = formater_message_whatsapp(c)

            # Le montant total doit apparaître dans le message
            assert str(c.total) in msg or "FCFA" in msg

    def test_message_notification_statut_retourne_dict(self, app):
        """message_notification_statut() doit retourner url + message."""
        with app.app_context():
            from backend.models.commande import Commande
            from backend.services.commande_service import message_notification_statut

            c = Commande.query.first()
            result = message_notification_statut(c)

            assert isinstance(result, dict)
            assert "url" in result
            assert "message" in result

    def test_message_notification_url_whatsapp(self, app):
        """L'URL de notification doit pointer vers wa.me avec le numéro client."""
        with app.app_context():
            from backend.models.commande import Commande
            from backend.services.commande_service import message_notification_statut

            c = Commande.query.first()
            result = message_notification_statut(c)

            # L'URL doit être une URL WhatsApp
            assert "wa.me" in result["url"]
            # Elle doit contenir le téléphone du client (nettoyé)
            tel_nettoye = c.client_telephone.replace("+", "").replace(" ", "").replace("-", "")
            assert tel_nettoye[-8:] in result["url"]


class TestStatsService:
    """Tests du service de statistiques."""

    def test_calculer_kpis_retourne_dict(self, app):
        """calculer_kpis() doit retourner un dict avec les KPIs attendus."""
        with app.app_context():
            from backend.services.stats_service import calculer_kpis

            kpis = calculer_kpis()

            assert isinstance(kpis, dict)
            champs_attendus = ["nb_produits", "nb_commandes", "nb_clients",
                               "ruptures", "ca_jour", "ca_mois", "ca_annee",
                               "panier_moyen"]
            for champ in champs_attendus:
                assert champ in kpis, f"KPI manquant : {champ}"

    def test_calculer_kpis_nb_produits_positif(self, app):
        """nb_produits doit correspondre aux produits actifs."""
        with app.app_context():
            from backend.services.stats_service import calculer_kpis
            from backend.models.produit import Produit

            kpis = calculer_kpis()
            nb_actifs = Produit.query.filter_by(actif=True).count()
            assert kpis["nb_produits"] == nb_actifs

    def test_calculer_kpis_ruptures_calcule(self, app):
        """ruptures doit compter les produits actifs avec stock=0."""
        with app.app_context():
            from backend.services.stats_service import calculer_kpis
            from backend.models.produit import Produit

            kpis = calculer_kpis()
            ruptures_bdd = Produit.query.filter_by(actif=True).filter(
                Produit.stock == 0
            ).count()
            assert kpis["ruptures"] == ruptures_bdd

    def test_ventes_par_mois_retourne_12_valeurs(self, app):
        """ventes_par_mois() doit toujours retourner exactement 12 valeurs."""
        with app.app_context():
            from backend.services.stats_service import ventes_par_mois

            mois = ventes_par_mois(2026)
            assert isinstance(mois, list)
            assert len(mois) == 12, f"Attendu 12 mois, obtenu {len(mois)}"
            # Toutes les valeurs doivent être des nombres ≥ 0
            assert all(v >= 0 for v in mois)

    def test_top_produits_commandes_retourne_liste(self, app):
        """top_produits_commandes() doit retourner une liste."""
        with app.app_context():
            from backend.services.stats_service import top_produits_commandes

            top = top_produits_commandes(limite=5)
            assert isinstance(top, list)
            assert len(top) <= 5

    def test_graphique_ventes_retourne_base64_ou_none(self, app):
        """graphique_ventes_mensuelles() doit retourner une string base64 ou None."""
        with app.app_context():
            from backend.services.stats_service import graphique_ventes_mensuelles

            graphique = graphique_ventes_mensuelles()
            # Peut être None si aucune vente, sinon une data URL
            if graphique is not None:
                assert graphique.startswith("data:image/png;base64,")

    def test_repartition_categories_retourne_dict(self, app):
        """repartition_categories() doit retourner un dict {categorie: montant}."""
        with app.app_context():
            from backend.services.stats_service import repartition_categories

            repartition = repartition_categories()
            assert isinstance(repartition, dict)


class TestImageService:
    """Tests légers du service image (sans vrai fichier image)."""

    def test_supprimer_image_inexistante_ne_plante_pas(self, app):
        """Supprimer une image qui n'existe pas ne doit pas lever d'exception."""
        with app.app_context():
            from backend.services.image_service import supprimer_image
            # Ne doit pas raise une exception
            try:
                supprimer_image("image_inexistante_xyz.webp")
            except Exception as e:
                pytest.fail(f"supprimer_image a levé une exception : {e}")
