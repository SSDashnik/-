from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import UserRepo, User, ROLE_CASHIER

bp = Blueprint("auth", __name__, url_prefix="/auth")

repo = UserRepo()

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.list_products"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = repo.get_by_username(username)
        if user and user.check_password(password):
            login_user(user)
            role_name = "Директор" if user.is_director() else "Кассир"
            flash(f"Вход выполнен успешно! Вы вошли как {role_name}.", "success")
            return redirect(url_for("products.list_products"))
        else:
            flash("Неверное имя пользователя или пароль", "error")
    return render_template("auth/login.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы.", "info")
    return redirect(url_for("auth.login"))

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.list_products"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if repo.get_by_username(username):
            flash("Пользователь с таким именем уже существует", "error")
        else:
            repo.add(username, password, ROLE_CASHIER)
            flash("Регистрация успешна! Пожалуйста, войдите в систему.", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html")