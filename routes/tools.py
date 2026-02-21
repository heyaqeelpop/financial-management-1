from flask import Blueprint, render_template, session, redirect, url_for

tools_bp = Blueprint("tools", __name__)

@tools_bp.route("/tools")
def tools():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("tools.html")
