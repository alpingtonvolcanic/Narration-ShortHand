import re
from contextlib import closing

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.models.database import UserDatabase

auth = Blueprint("auth", __name__)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def database():
    return UserDatabase(current_app.config["DATABASE_PATH"], current_app.config["SECRET_KEY"])


def validate_credentials(username, password):
    if not USERNAME_PATTERN.fullmatch(username):
        return "Username must be 3-32 characters using letters, numbers, '.', '_' or '-'."
    if not 12 <= len(password) <= 128:
        return "Password must be between 12 and 128 characters."
    return None


@auth.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        with closing(database().connect()) as connection:
            g.user = connection.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if g.user is None:
            session.clear()


@auth.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = database().authenticate(username, password)
        if user is None:
            flash("Invalid username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("notes.index"))
    return render_template("auth/login.html")


@auth.route("/signup", methods=("GET", "POST"))
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirmation", "")
        error = validate_credentials(username, password)
        if error is None and password != confirmation:
            error = "Passwords must match."
        if error:
            flash(error, "error")
        else:
            try:
                database().create_user(username, password)
            except ValueError as error:
                flash(str(error), "error")
            else:
                flash("Account created. You can now sign in.", "success")
                return redirect(url_for("auth.login"))
    return render_template("auth/signup.html")


@auth.route("/logout", methods=("POST",))
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth.route("/admin")
def admin():
    if g.user is None or g.user["role"] != "admin":
        return redirect(url_for("auth.login"))
    return render_template("auth/admin.html", users=database().list_users())


@auth.post("/admin/users/<int:user_id>/role")
def update_user_role(user_id):
    if g.user is None or g.user["role"] != "admin":
        return redirect(url_for("auth.login"))
    role = request.form.get("role", "")
    if user_id == g.user["id"] and role != "admin":
        flash("You cannot remove your own administrator role.", "error")
    else:
        try:
            database().update_role(user_id, role)
        except ValueError as error:
            flash(str(error), "error")
        else:
            flash("Account role updated.", "success")
    return redirect(url_for("auth.admin"))


@auth.post("/admin/users/<int:user_id>/delete")
def delete_user(user_id):
    if g.user is None or g.user["role"] != "admin":
        return redirect(url_for("auth.login"))
    if user_id == g.user["id"]:
        flash("You cannot delete your own administrator account.", "error")
        return redirect(url_for("auth.admin"))
    with closing(database().connect()) as connection:
        target = connection.execute(
            "SELECT role FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        admin_count = connection.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'admin'"
        ).fetchone()[0]
    if target is None:
        flash("That account does not exist.", "error")
    elif target["role"] == "admin" and admin_count <= 1:
        flash("The last administrator cannot be deleted.", "error")
    else:
        try:
            database().delete_user(user_id, current_app.config["DOCUMENT_ROOT"])
        except (OSError, ValueError) as error:
            flash(str(error), "error")
        else:
            flash("Account deleted.", "success")
    return redirect(url_for("auth.admin"))


def login_required(view):
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    wrapped_view.__name__ = view.__name__
    return wrapped_view
