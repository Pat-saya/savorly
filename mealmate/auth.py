from functools import wraps

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from .extensions import db
from .models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.full_path))
        return view(**kwargs)
    return wrapped_view


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        error = None
        if len(username) < 3:
            error = "Username must be at least 3 characters."
        elif "@" not in email:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif db.session.scalar(db.select(User).where(or_(User.username == username, User.email == email))):
            error = "That username or email is already registered."
        if error:
            flash(error, "danger")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session.clear()
            session["user_id"] = user.id
            flash("Welcome to Savorly!", "success")
            return redirect(url_for("main.home"))
    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        return redirect(url_for("main.home"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        user = db.session.scalar(db.select(User).where(or_(User.username == identity, User.email == identity.lower())))
        if user is None or not user.check_password(request.form.get("password", "")):
            flash("Incorrect username/email or password.", "danger")
        else:
            session.clear()
            session["user_id"] = user.id
            flash("You are logged in.", "success")
            return redirect(url_for("main.home"))
    return render_template("auth/login.html")


@bp.post("/logout")
def logout():
    session.clear()
    flash("You are logged out.", "info")
    return redirect(url_for("main.home"))
