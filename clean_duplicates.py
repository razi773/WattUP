#!/usr/bin/env python3
"""
Script pour nettoyer les prédictions en double dans MongoDB
"""
from pymongo import MongoClient
from collections import defaultdict
def clean_duplicate_predictions():
    """Nettoie les prédictions en double dans MongoDB"""
    print("🧹 Nettoyage des prédictions en double...")
    client = MongoClient("mongodb://localhost:27017/")
    db = client["energy_db"]
    collections_to_clean = [
        "predicted_data",
        "xgb_predictions", 
        "cost_predictions"
    ]
    for collection_name in collections_to_clean:
        collection = db[collection_name]
        print(f"\n📊 Nettoyage de la collection '{collection_name}'...")
        xgb_docs = list(collection.find({"source": "XGBoost"}))
        if not xgb_docs:
            print(f"   ✅ Aucun document XGBoost trouvé dans {collection_name}")
            continue
        print(f"   📈 {len(xgb_docs)} documents XGBoost trouvés")
        date_groups = defaultdict(list)
        for doc in xgb_docs:
            date_key = doc.get('date')
            if date_key:
                date_groups[date_key].append(doc['_id'])
        duplicates_removed = 0
        for date, doc_ids in date_groups.items():
            if len(doc_ids) > 1:
                ids_to_remove = doc_ids[1:]
                result = collection.delete_many({"_id": {"$in": ids_to_remove}})
                duplicates_removed += result.deleted_count
                print(f"   🗑️  Date {date}: supprimé {len(ids_to_remove)} doublons")
        remaining = collection.count_documents({"source": "XGBoost"})
        print(f"   ✅ {duplicates_removed} doublons supprimés, {remaining} documents restants")
    print("\n🎉 Nettoyage terminé!")
if __name__ == "__main__":
    clean_duplicate_predictions()