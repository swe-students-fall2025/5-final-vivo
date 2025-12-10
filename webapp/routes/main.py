from flask import Blueprint, render_template, session, redirect, url_for
from datetime import datetime, timezone
from webapp.db import bathrooms_collection

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))
    return render_template("index.html", user=user)


@bp.route("/my-reviews")
def my_reviews_page():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))

    user_email = user.get("email")
    cursor = bathrooms_collection.find({"reviews.user_email": user_email})

    reviews = []
    for doc in cursor:
        osm_id = doc.get("osm_id")
        tags = doc.get("tags", {})
        bathroom_name = tags.get("name") or f"Bathroom {osm_id}"
        lat = doc.get("lat")
        lon = doc.get("lon")
        for review in doc.get("reviews", []):
            if review.get("user_email") == user_email:
                created_at = review.get("created_at")
                display_date = None
                if created_at:
                    try:
                        normalized = created_at.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(normalized)
                        display_date = (
                            dt.astimezone(timezone.utc).strftime("%b %d, %Y %H:%M UTC")
                        )
                    except ValueError:
                        display_date = created_at

                reviews.append(
                    {
                        "osm_id": osm_id,
                        "bathroom_name": bathroom_name,
                        "rating": review.get("rating"),
                        "comment": review.get("comment"),
                        "created_at": display_date,
                        "lat": lat,
                        "lon": lon,
                    }
                )

    return render_template("my_reviews.html", user=user, reviews=reviews)
