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

    try:
        user_email = user.get("email")
        cursor = bathrooms_collection.find({"reviews.user_email": user_email})

        reviews = []
        for doc in cursor:
            osm_id = doc.get("osm_id")
            tags = doc.get("tags", {})
            bathroom_name = (
                tags.get("name")
                or tags.get("addr:street")
                or tags.get("addr:neighbourhood")
                or f"Bathroom #{osm_id}"
            )
            lat = doc.get("lat")
            lon = doc.get("lon")

            # Build a readable location label from address tags or coordinates
            location_label = None
            address_parts = []
            if tags.get("addr:housenumber"):
                address_parts.append(tags["addr:housenumber"])
            if tags.get("addr:street"):
                address_parts.append(tags["addr:street"])
            if tags.get("addr:neighbourhood"):
                address_parts.append(tags["addr:neighbourhood"])
            if tags.get("addr:city"):
                address_parts.append(tags["addr:city"])

            if address_parts:
                location_label = ", ".join(address_parts)
            elif lat is not None and lon is not None:
                location_label = f"{round(lat, 4)}, {round(lon, 4)}"

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
                                "location_label": location_label,
                                "rating": int(float(review.get("rating", 0))),  # <-- Convert to int
                                "comment": review.get("comment"),
                                "created_at": display_date,
                                "lat": lat,
                                "lon": lon,
                            }
                        )

        return render_template("my_reviews.html", user=user, reviews=reviews)
    
    except Exception as e:
        # This will show you the actual error
        print(f"Error in my_reviews_page: {e}")
        import traceback
        traceback.print_exc()
        return f"Error loading reviews: {str(e)}", 500