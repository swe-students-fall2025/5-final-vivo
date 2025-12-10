import os
from pymongo import MongoClient

mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["bathrooms"]
bathrooms_collection = db["bathrooms"]
users_collection = db["users"]
