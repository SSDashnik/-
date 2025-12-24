from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models.user import UserRepo, ROLE_CASHIER, ROLE_DIRECTOR

bp = Blueprint("users", __name__, url_prefix="/users")
repo = UserRepo()


@bp.get("/")
@login_required
def list_users():
    if not current_user.is_director():
        flash("Доступ запрещен. Только директор может просматривать пользователей.", "error")
        return redirect(url_for("products.list_products"))

    users = repo.all()
    return render_template("users/list.html", users=users)


@bp.get("/create")
@login_required
def create_form():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    return render_template("users/create.html", roles=[ROLE_CASHIER, ROLE_DIRECTOR])


@bp.post("/create")
@login_required
def create_user():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    full_name = request.form.get("full_name")

    if not all([username, password, role]):
        flash("Заполните все обязательные поля", "error")
        return redirect(url_for("users.create_form"))

    if repo.get_by_username(username):
        flash("Пользователь с таким именем уже существует", "error")
        return redirect(url_for("users.create_form"))

    try:
        repo.add(username, password, role, full_name)
        flash("Пользователь успешно создан!", "success")
    except Exception as e:
        flash(f"Ошибка при создании пользователя: {str(e)}", "error")

    return redirect(url_for("users.list_users"))


@bp.get("/<int:user_id>/edit")
@login_required
def edit_form(user_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    user = repo.get_by_id(user_id)
    if not user:
        flash("Пользователь не найден", "error")
        return redirect(url_for("users.list_users"))

    return render_template("users/edit.html", user=user, roles=[ROLE_CASHIER, ROLE_DIRECTOR])


@bp.post("/<int:user_id>/edit")
@login_required
def update_user(user_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")
    full_name = request.form.get("full_name")

    existing_user = repo.get_by_username(username)
    if existing_user and existing_user.id != user_id:
        flash("Пользователь с таким именем уже существует", "error")
        return redirect(url_for("users.edit_form", user_id=user_id))

    try:
        repo.update(user_id, username, password, role, full_name)
        flash("Пользователь успешно обновлен!", "success")
    except Exception as e:
        flash(f"Ошибка при обновлении пользователя: {str(e)}", "error")

    return redirect(url_for("users.list_users"))


@bp.post("/<int:user_id>/delete")
@login_required
def delete_user(user_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    if user_id == current_user.id:
        flash("Нельзя удалить самого себя", "error")
        return redirect(url_for("users.list_users"))

    if repo.delete(user_id):
        flash("Пользователь успешно удален!", "success")
    else:
        flash("Пользователь не найден", "error")

    return redirect(url_for("users.list_users"))

