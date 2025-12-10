from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login"))
    return render_template("index.html", user=user)
