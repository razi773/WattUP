# -*- coding: utf-8 -*-
"""
Module documentation
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["ai_energy_db"]
def insert_data(collection_name, data):
    collection = db[collection_name]
    if isinstance(data, list):
        collection.insert_many(data)
    else:
        collection.insert_one(data)
def replace_collection(collection_name, data):
    collection = db[collection_name]
    collection.delete_many({})
    insert_data(collection_name, data)
def get_all(collection_name):
    collection = db[collection_name]
    return list(collection.find({}, {"_id": 0}))
def drop_collection(collection_name):
    db.drop_collection(collection_name)
