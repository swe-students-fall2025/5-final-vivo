import os
from flask import (
    Flask,
    render_template,
    url_for,
    session,
    redirect,
    flash,
    jsonify,
    request,
)
from authlib.integrations.flask_client import OAuth
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev_key")

# OAuth Configuration
oauth = OAuth(app)
oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    api_base_url="https://www.googleapis.com/oauth2/v3/",
    client_kwargs={"scope": "openid email profile"},
)

# Mongo
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["bathrooms"]
bathrooms_collection = db["bathrooms"]
users_collection = db["users"]


@app.route("/")
def index():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    return render_template("index.html", user=user)


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/login/google")
def login_google():
    redirect_uri = url_for("authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def authorized():
    token = oauth.google.authorize_access_token()
    if not token:
        flash("Login failed. Please try again.")
        return redirect(url_for("login"))

    user_info = oauth.google.get("userinfo").json()

    email = user_info.get("email")
    if not email:
        flash("Unable to retrieve email from Google. Please try again.")
        return redirect(url_for("login"))

    existing_user = users_collection.find_one({"email": email})

    if not existing_user:
        new_user = {
            "email": email,
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = users_collection.insert_one(new_user)
        user_record = users_collection.find_one({"_id": result.inserted_id})
    else:
        users_collection.update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "name": user_info.get("name"),
                    "picture": user_info.get("picture"),
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        user_record = users_collection.find_one({"_id": existing_user["_id"]})

    session["user"] = {
        "id": str(user_record.get("_id")),
        "name": user_record.get("name"),
        "email": user_record.get("email"),
        "picture": user_record.get("picture"),
    }

    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/api/bathrooms")
def get_bathrooms():
    bathrooms = []
    for doc in bathrooms_collection.find():
        bathrooms.append(
            {
                "osm_id": doc["osm_id"],
                "lat": doc["lat"],
                "lon": doc["lon"],
                "tags": doc.get("tags", {}),
            }
        )
    return jsonify({"bathrooms": bathrooms})


def serialize_bathroom(doc):
    if not doc:
        return {}
    return {
        "osm_id": doc.get("osm_id"),
        "lat": doc.get("lat"),
        "lon": doc.get("lon"),
        "tags": doc.get("tags", {}),
        "reviews": doc.get("reviews", []),
        "average_rating": doc.get("average_rating"),
        "rating_count": doc.get("rating_count", 0),
    }


@app.route("/api/bathrooms/add", methods=["POST"])
def add_bathroom():
    data = request.get_json() or {}

    required = ["osm_id", "lat", "lon"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    bathrooms_collection.insert_one(
        {
            "osm_id": data["osm_id"],
            "lat": data["lat"],
            "lon": data["lon"],
            "tags": data.get("tags", {}),
            "reviews": [],
            "average_rating": None,
            "rating_count": 0,
        }
    )

    return jsonify({"message": "Bathroom added!", "bathroom": data}), 201


@app.route("/api/bathrooms/full")
def get_bathrooms_full():
    bathrooms = [serialize_bathroom(doc) for doc in bathrooms_collection.find()]
    return jsonify({"bathrooms": bathrooms})


@app.route("/api/bathrooms/<string:osm_id>", methods=["GET"])
def get_bathroom_detail(osm_id):
    doc = bathrooms_collection.find_one({"osm_id": osm_id})
    if not doc:
        return jsonify({"error": "Bathroom not found"}), 404
    return jsonify(serialize_bathroom(doc))


@app.route("/api/bathrooms/<string:osm_id>/reviews", methods=["GET"])
def get_bathroom_reviews(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400
    doc = bathrooms_collection.find_one({"osm_id": osm_id})
    if not doc:
        return jsonify({"error": "Bathroom not found"}), 404

    reviews = doc.get("reviews", [])
    return jsonify({"osm_id": osm_id, "reviews": reviews})


@app.route("/api/bathrooms/<string:osm_id>/reviews", methods=["POST"])
def add_bathroom_review(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400
    doc = bathrooms_collection.find_one({"osm_id": osm_id})
    if not doc:
        return jsonify({"error": "Bathroom not found"}), 404

    user = session.get("user") or {}
    user_email = user.get("email")
    if not user_email:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json() or {}
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()

    if rating is None:
        return jsonify({"error": "rating is required"}), 400
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be a number"}), 400
    if rating < 0 or rating > 5:
        return jsonify({"error": "rating must be between 0 and 5"}), 400

    review = {
        "rating": rating,
        "comment": comment,
        "user_name": user.get("name", "Anonymous"),
        "user_email": user.get("email"),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    existing_reviews = doc.get("reviews", [])
    new_reviews = [r for r in existing_reviews if r.get("user_email") != user_email]
    new_reviews.append(review)

    # Recalculate average and count
    ratings = [r["rating"] for r in new_reviews]
    new_avg = sum(ratings) / len(ratings)
    new_count = len(new_reviews)

    bathrooms_collection.update_one(
        {"osm_id": osm_id},
        {
            "$set": {
                "reviews": new_reviews,
                "average_rating": new_avg,
                "rating_count": new_count,
            }
        },
    )

    updated = bathrooms_collection.find_one({"osm_id": osm_id})
    return jsonify(serialize_bathroom(updated)), 201


if __name__ == "__main__":
    app.run(debug=True)
