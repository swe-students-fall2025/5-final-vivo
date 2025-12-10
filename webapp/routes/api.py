from flask import Blueprint, jsonify, request, session
from datetime import datetime
from webapp.db import bathrooms_collection, users_collection

bp = Blueprint("api", __name__, url_prefix="/api")


def serialize_bathroom(doc):
    if not doc:
        return {}
    return {
        "osm_id": doc.get("osm_id"),
        "lat": doc.get("lat"),
        "lon": doc.get("lon"),
        "tags": doc.get("tags", {}),
        "reviews": doc.get("reviews", []),
        "images": doc.get("images", []),
        "average_rating": doc.get("average_rating"),
        "rating_count": doc.get("rating_count", 0),
    }


@bp.route("/bathrooms/add", methods=["POST"])
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


@bp.route("/bathrooms/full")
def get_bathrooms_full():
    bathrooms = [serialize_bathroom(doc) for doc in bathrooms_collection.find()]
    return jsonify({"bathrooms": bathrooms})


@bp.route("/bathrooms/<string:osm_id>", methods=["GET"])
def get_bathroom_detail(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400
    doc = bathrooms_collection.find_one({"osm_id": osm_id})
    if not doc:
        return jsonify({"error": "Bathroom not found"}), 404
    return jsonify(serialize_bathroom(doc))


@bp.route("/bathrooms/<string:osm_id>/reviews", methods=["GET"])
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


@bp.route("/bathrooms/<string:osm_id>/reviews", methods=["POST"])
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


@bp.route("/bathrooms", methods=["GET"])
def get_bathrooms():
    min_lat = request.args.get("min_lat", type=float)
    max_lat = request.args.get("max_lat", type=float)
    min_lon = request.args.get("min_lon", type=float)
    max_lon = request.args.get("max_lon", type=float)

    keyword = request.args.get("q", type=str)
    sort_param = request.args.get("sort", type=str)
    limit = request.args.get("limit", default=2000, type=int)

    query: dict = {}

    if None not in (min_lat, max_lat, min_lon, max_lon):
        query["lat"] = {"$gte": min_lat, "$lte": max_lat}
        query["lon"] = {"$gte": min_lon, "$lte": max_lon}

    if keyword:
        query["tags.name"] = {"$regex": keyword, "$options": "i"}

    sort_spec = None
    if sort_param == "rating":
        sort_spec = [("average_rating", -1)]
    elif sort_param == "reviews":
        sort_spec = [("rating_count", -1)]
    elif sort_param == "name":
        sort_spec = [("tags.name", 1)]

    cursor = bathrooms_collection.find(query)

    if sort_spec:
        cursor = cursor.sort(sort_spec)

    if limit and limit > 0:
        cursor = cursor.limit(limit)

    docs = list(cursor)

    bathrooms = []
    for doc in docs:
        bathrooms.append(
            {
                "osm_id": doc.get("osm_id"),
                "lat": doc.get("lat"),
                "lon": doc.get("lon"),
                "tags": doc.get("tags", {}),
                "average_rating": doc.get("average_rating"),
                "rating_count": doc.get("rating_count", 0),
            }
        )

    return jsonify({"bathrooms": bathrooms})


@bp.route("/my-reviews", methods=["GET"])
def get_my_reviews():
    """Return all reviews made by the currently logged-in user."""
    user = session.get("user") or {}
    user_email = user.get("email")
    if not user_email:
        return jsonify({"error": "User not logged in"}), 401

    cursor = bathrooms_collection.find({"reviews.user_email": user_email})

    results = []
    for doc in cursor:
        osm_id = doc.get("osm_id")
        tags = doc.get("tags", {})
        bathroom_name = tags.get("name") or f"Bathroom {osm_id}"

        for review in doc.get("reviews", []):
            if review.get("user_email") == user_email:
                results.append(
                    {
                        "osm_id": osm_id,
                        "bathroom_name": bathroom_name,
                        "rating": review.get("rating"),
                        "comment": review.get("comment"),
                        "created_at": review.get("created_at"),
                    }
                )

    return jsonify({"reviews": results})


@bp.route("/bathrooms/<string:osm_id>/reviews", methods=["DELETE"])
def delete_bathroom_review(osm_id):
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

    existing_reviews = doc.get("reviews", [])

    remaining_reviews = [
        r for r in existing_reviews if r.get("user_email") != user_email
    ]

    if len(remaining_reviews) == len(existing_reviews):
        return jsonify({"message": "No review from this user to delete."}), 200

    if remaining_reviews:
        ratings = [r["rating"] for r in remaining_reviews]
        new_avg = sum(ratings) / len(ratings)
        new_count = len(remaining_reviews)
    else:
        new_avg = None
        new_count = 0

    bathrooms_collection.update_one(
        {"osm_id": osm_id},
        {
            "$set": {
                "reviews": remaining_reviews,
                "average_rating": new_avg,
                "rating_count": new_count,
            }
        },
    )

    updated = bathrooms_collection.find_one({"osm_id": osm_id})
    return jsonify(serialize_bathroom(updated)), 200


@bp.route("/bathrooms/<string:osm_id>/images", methods=["POST"])
def add_bathroom_image(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400

    doc = bathrooms_collection.find_one({"osm_id": osm_id})
    if not doc:
        return jsonify({"error": "Bathroom not found"}), 404

    user = session.get("user")
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json() or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"error": "No image data provided"}), 400

    bathrooms_collection.update_one(
        {"osm_id": osm_id}, {"$push": {"images": image_data}}
    )

    updated = bathrooms_collection.find_one({"osm_id": osm_id})
    return jsonify(serialize_bathroom(updated)), 201


@bp.route("/users/favorites", methods=["GET"])
def get_favorites():
    user = session.get("user")
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    user_doc = users_collection.find_one({"email": user["email"]})
    if not user_doc:
        return jsonify({"favorites": []})

    return jsonify({"favorites": user_doc.get("favorites", [])})


@bp.route("/users/favorites/<string:osm_id>", methods=["POST"])
def add_favorite(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400

    user = session.get("user")
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    # Check if already favorited to avoid double counting
    user_doc = users_collection.find_one({"email": user["email"], "favorites": osm_id})
    if not user_doc:
        users_collection.update_one(
            {"email": user["email"]}, {"$addToSet": {"favorites": osm_id}}
        )
        bathrooms_collection.update_one(
            {"osm_id": osm_id}, {"$inc": {"favorite_count": 1}}
        )

    return jsonify({"message": "Added to favorites", "osm_id": osm_id}), 200


@bp.route("/users/favorites/<string:osm_id>", methods=["DELETE"])
def remove_favorite(osm_id):
    try:
        osm_id = int(osm_id)
    except ValueError:
        return jsonify({"error": "Invalid osm_id"}), 400

    user = session.get("user")
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    # Check if favorited
    user_doc = users_collection.find_one({"email": user["email"], "favorites": osm_id})
    if user_doc:
        users_collection.update_one(
            {"email": user["email"]}, {"$pull": {"favorites": osm_id}}
        )
        bathrooms_collection.update_one(
            {"osm_id": osm_id}, {"$inc": {"favorite_count": -1}}
        )

    return jsonify({"message": "Removed from favorites", "osm_id": osm_id}), 200


@bp.route("/bathrooms/recommendations", methods=["GET"])
def get_recommendations():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid lat/lon"}), 400

    # Top Rated (highest average_rating, min 1 review)
    top_rated_cursor = (
        bathrooms_collection.find({"average_rating": {"$ne": None}})
        .sort("average_rating", -1)
        .limit(5)
    )
    top_rated = [serialize_bathroom(doc) for doc in top_rated_cursor]

    # Most Favorited (highest favorite_count)
    most_favorited_cursor = (
        bathrooms_collection.find({"favorite_count": {"$gt": 0}})
        .sort("favorite_count", -1)
        .limit(5)
    )
    most_favorited = [serialize_bathroom(doc) for doc in most_favorited_cursor]

    all_bathrooms = list(
        bathrooms_collection.find(
            {},
            {
                "osm_id": 1,
                "lat": 1,
                "lon": 1,
                "tags": 1,
                "average_rating": 1,
                "rating_count": 1,
            },
        )
    )

    for b in all_bathrooms:
        # Simple squared euclidean distance is enough for sorting
        b["dist_sq"] = (b["lat"] - lat) ** 2 + (b["lon"] - lon) ** 2

    all_bathrooms.sort(key=lambda x: x["dist_sq"])
    nearest_docs = all_bathrooms[:5]

    nearest = []
    for doc in nearest_docs:
        nearest.append(
            {
                "osm_id": doc.get("osm_id"),
                "lat": doc.get("lat"),
                "lon": doc.get("lon"),
                "tags": doc.get("tags", {}),
                "average_rating": doc.get("average_rating"),
                "rating_count": doc.get("rating_count", 0),
            }
        )

    return jsonify(
        {"top_rated": top_rated, "most_favorited": most_favorited, "nearest": nearest}
    )
