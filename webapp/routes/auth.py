from flask import Blueprint, url_for, session, redirect, flash
from datetime import datetime
from webapp.extensions import oauth
from webapp.db import users_collection

bp = Blueprint("auth", __name__)


@bp.route("/login")
def login():
    from flask import render_template

    return render_template("login.html")


@bp.route("/login/google")
def login_google():
    redirect_uri = url_for("auth.authorized", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/auth/callback")
def authorized():
    token = oauth.google.authorize_access_token()
    if not token:
        flash("Login failed. Please try again.")
        return redirect(url_for("auth.login"))

    user_info = oauth.google.get("userinfo").json()

    email = user_info.get("email")
    if not email:
        flash("Unable to retrieve email from Google. Please try again.")
        return redirect(url_for("auth.login"))

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

    return redirect(url_for("main.index"))


@bp.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.login"))
