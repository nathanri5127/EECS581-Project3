from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user
)

from extensions import db

from models.user import User

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = (
            request.form["confirm_password"]
        )
        if password != confirm_password:
            flash(
                "Passwords do not match",
                "error"
            )
            return render_template("register.html")
        existing_user = (
            User.query.filter_by(username=username).first()
        )
        if existing_user:
            flash(
                "Username already exists",
                "error"
            )
            return render_template("register.html")
        user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard.dashboard"))
    return render_template("register.html")

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if (
            user
            and
            check_password_hash(
                user.password_hash,
                password
            )
        ):
            login_user(user)
            return redirect(
                url_for("dashboard.dashboard")
            )
        flash(
            "Invalid username or password",
            "error"
        )
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = (
            request.form[
                "confirm_password"
            ]
        )
        if password != confirm_password:
            flash(
                "Passwords do not match",
                "error"
            )
            return render_template("password_reset.html")
        user = User.query.filter_by(username=username).first()
        if not user:
            flash(
                "No account exists with that username.",
                "error"
            )
            return redirect(url_for("auth.reset_password"))
        user.password_hash = (
            generate_password_hash(
                password
            )
        )
        db.session.commit()
        return redirect(url_for("auth.login"))
    return render_template("password_reset.html")