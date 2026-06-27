#!/usr/bin/env python3
"""
migrate_historique_stock.py
Crée la table historique_stock si elle n'existe pas encore.
Exécuter depuis ~/IKLILOUNE : python migrate_historique_stock.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from backend.database import db
from backend.models.historique_stock import HistoriqueStock  # noqa — force l'import du modèle

with app.app_context():
    inspector = db.inspect(db.engine)
    tables    = inspector.get_table_names()
    if "historique_stock" not in tables:
        HistoriqueStock.__table__.create(db.engine)
        print("  ✅ Table historique_stock créée")
    else:
        print("  ⏭  Table historique_stock existe déjà")
    print("  Migration terminée.")
