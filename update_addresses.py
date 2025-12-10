import os
import time
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    print("Error: MONGO_URI not found in environment variables.")
    exit(1)

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client["bathrooms"]
collection = db["bathrooms"]

# Nominatim API URL
NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def get_address_from_nominatim(lat, lon):
    """
    Fetch address details from Nominatim Reverse Geocoding API.
    """
    params = {
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
    }
    headers = {
        "User-Agent": "VivoNYC-BathroomFinder/1.0 (educational-project; contact: swe-student@nyu.edu)",
        "Referer": "https://github.com/swe-students-fall2025/5-final-vivo",
    }

    try:
        response = requests.get(
            NOMINATIM_URL, params=params, headers=headers, timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching address for {lat}, {lon}: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return None


def update_bathrooms():
    query = {
        "$or": [
            {"tags.addr:street": {"$exists": False}},
            {"tags.addr:housenumber": {"$exists": False}},
        ]
    }

    bathrooms_to_update = list(collection.find(query))
    total = len(bathrooms_to_update)
    print(f"Found {total} bathrooms to update.")

    updated_count = 0

    for i, bathroom in enumerate(bathrooms_to_update):
        osm_id = bathroom.get("osm_id")
        lat = bathroom.get("lat")
        lon = bathroom.get("lon")

        if not lat or not lon:
            print(f"Skipping {osm_id}: Missing coordinates.")
            continue

        print(f"[{i+1}/{total}] Processing {osm_id} ({lat}, {lon})...")

        data = get_address_from_nominatim(lat, lon)

        if data and "address" in data:
            address = data["address"]

            update_fields = {}

            if "house_number" in address:
                update_fields["tags.addr:housenumber"] = address["house_number"]
            if "road" in address:
                update_fields["tags.addr:street"] = address["road"]
            if "city" in address:
                update_fields["tags.addr:city"] = address["city"]
            elif "town" in address:
                update_fields["tags.addr:city"] = address["town"]
            elif "village" in address:
                update_fields["tags.addr:city"] = address["village"]
            elif "city_district" in address:  # NYC often returns this
                update_fields["tags.addr:city"] = address["city_district"]

            if "state" in address:
                update_fields["tags.addr:state"] = address["state"]
            if "postcode" in address:
                update_fields["tags.addr:postcode"] = address["postcode"]

            if update_fields:
                collection.update_one({"_id": bathroom["_id"]}, {"$set": update_fields})
                print(f"  Updated {osm_id} with {update_fields}")
                updated_count += 1
            else:
                print(f"  No relevant address fields found for {osm_id}")
        else:
            print(f"  Failed to get address for {osm_id}")

        # Respect rate limit (1 request per second)
        time.sleep(1.1)

    print(f"Finished. Updated {updated_count} bathrooms.")


if __name__ == "__main__":
    update_bathrooms()
