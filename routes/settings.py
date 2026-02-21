from flask import Blueprint, render_template, session, redirect, url_for

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings")
def settings():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("settings.html")
