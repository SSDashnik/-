from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.product import ProductRepo
from decimal import Decimal

bp = Blueprint("products", __name__, url_prefix="/products")
repo = ProductRepo()


@bp.get("/")
@login_required
def list_products():
    category_filter = request.args.get('category', '')
    search_term = request.args.get('search', '')

    products = repo.all()
    
    if category_filter:
        products = repo.filter_by_category(category_filter)
    elif search_term:
        products = repo.filter_by_name(search_term)

    categories = repo.get_categories()
    return render_template("products/list.html", 
                         products=products, 
                         categories=categories,
                         current_category=category_filter,
                         search_term=search_term,
                         is_director=current_user.is_director())


@bp.get("/create")
@login_required
def create_form():
    if not current_user.is_director():
        flash("Доступ запрещен. Только директор может добавлять товары.", "error")
        return redirect(url_for("products.list_products"))
    
    categories = repo.get_categories()
    return render_template("products/create.html", categories=categories)


@bp.post("/create")
@login_required
def create_product():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    name = request.form.get("name")
    article = request.form.get("article")
    package = request.form.get("package")
    category = request.form.get("category")
    price = request.form.get("price")
    stock_quantity = request.form.get("stock_quantity")
    description = request.form.get("description")

    if not all([name, category, price, stock_quantity]):
        flash("Заполните все обязательные поля", "error")
        return redirect(url_for("products.create_form"))

    try:
        price = Decimal(price)
        stock_quantity = int(stock_quantity)
        repo.add(name, category, price, stock_quantity, description, article, package)
        flash("Товар успешно добавлен!", "success")
    except Exception as e:
        flash(f"Ошибка при добавлении товара: {str(e)}", "error")

    return redirect(url_for("products.list_products"))


@bp.get("/<int:product_id>/edit")
@login_required
def edit_form(product_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    product = repo.get_by_id(product_id)
    if not product:
        flash("Товар не найден", "error")
        return redirect(url_for("products.list_products"))

    categories = repo.get_categories()
    return render_template("products/edit.html", product=product, categories=categories)


@bp.post("/<int:product_id>/edit")
@login_required
def update_product(product_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    name = request.form.get("name")
    article = request.form.get("article")
    package = request.form.get("package")
    category = request.form.get("category")
    price = request.form.get("price")
    stock_quantity = request.form.get("stock_quantity")
    description = request.form.get("description")

    try:
        price = Decimal(price) if price else None
        stock_quantity = int(stock_quantity) if stock_quantity else None
        repo.update(product_id, name, category, price, stock_quantity, description, None, article, package)
        flash("Товар успешно обновлен!", "success")
    except Exception as e:
        flash(f"Ошибка при обновлении товара: {str(e)}", "error")

    return redirect(url_for("products.list_products"))


@bp.post("/<int:product_id>/delete")
@login_required
def delete_product(product_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    if repo.delete(product_id):
        flash("Товар успешно удален!", "success")
    else:
        flash("Товар не найден", "error")

    return redirect(url_for("products.list_products"))


@bp.get("/discounts")
@login_required
def discounts():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    search_term = request.args.get('search', '')
    products = repo.all()
    
    if search_term:
        products = repo.filter_by_name(search_term)

    return render_template("products/discounts.html", 
                         products=products,
                         search_term=search_term)


@bp.post("/<int:product_id>/set_discount")
@login_required
def set_discount(product_id):
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    discount_price_str = request.form.get("discount_price", "").strip()
    
    try:
        # Если строка пустая или None, устанавливаем discount_price в None
        if not discount_price_str or discount_price_str == "":
            discount_price = None
        else:
            discount_price = Decimal(discount_price_str)
            if discount_price <= 0:
                flash("Цена со скидкой должна быть больше нуля", "error")
                return redirect(url_for("products.discounts", search=request.form.get("search", "")))
        
        repo.update(product_id, discount_price=discount_price)
        flash("Скидка успешно установлена!" if discount_price else "Скидка удалена!", "success")
    except (ValueError, Exception) as e:
        flash(f"Ошибка при установке скидки: {str(e)}", "error")

    return redirect(url_for("products.discounts", search=request.form.get("search", "")))

