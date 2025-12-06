# import_overpass.py
import os
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv() 
mongo_uri = os.getenv("MONGO_URI")

client = MongoClient(mongo_uri)
db = client["bathrooms"]  
collection = db["bathrooms"]  

# overpass api
overpass_url = "https://overpass-api.de/api/interpreter"
query = """
[out:json][timeout:25];
area["name"="City of New York"]["boundary"="administrative"]["admin_level"="5"]->.nyc;
(
  node["amenity"="toilets"](area.nyc);
  way["amenity"="toilets"](area.nyc);
  relation["amenity"="toilets"](area.nyc);
);
out center;
"""

# insert the bathrooms into mongo
def fetch_and_insert_bathrooms():
    try:
        response = requests.post(overpass_url, data=query)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print("Error fetching data from Overpass API:", e)
        return

    elements = data.get("elements", [])
    if not elements:
        print("No bathrooms found from Overpass API.")
        return

    inserted_count = 0
    for el in elements:
        osm_id = el["id"]
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

        doc = {
            "osm_id": osm_id,
            "lat": lat,
            "lon": lon,
            "tags": el.get("tags", {})
        }

        result = collection.update_one(
            {"osm_id": osm_id},
            {"$set": doc},
            upsert=True
        )

        if result.upserted_id or result.modified_count:
            inserted_count += 1

    print(f"Inserted/Updated {inserted_count} bathrooms into MongoDB.")

if __name__ == "__main__":
    fetch_and_insert_bathrooms()
