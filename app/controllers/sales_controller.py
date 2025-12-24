from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models.product import ProductRepo
from app.models.sale import SaleRepo, Sale
from decimal import Decimal

bp = Blueprint("sales", __name__, url_prefix="/sales")
product_repo = ProductRepo()
sale_repo = SaleRepo()


@bp.get("/")
@login_required
def list_sales():
    if current_user.is_director():
        sales = sale_repo.all()
    else:
        sales = sale_repo.get_by_cashier(current_user.id)

    sales_with_products = []
    for sale in sales:
        product = product_repo.get_by_id(sale.product_id)
        sales_with_products.append({
            'sale': sale,
            'product': product
        })

    return render_template("sales/list.html", 
                         sales_with_products=sales_with_products,
                         is_director=current_user.is_director())


@bp.get("/create")
@login_required
def create_sale_form():
    products = product_repo.all()
    available_products = [p for p in products if p.stock_quantity > 0]
    return render_template("sales/create.html", products=available_products)


@bp.post("/create")
@login_required
def create_sale():
    product_ids = request.form.getlist("product_ids")
    quantities = request.form.getlist("quantities")
    confirmed = request.form.get("confirmed")

    if not product_ids or not quantities or not confirmed:
        flash("Добавьте товары в корзину и подтвердите продажу", "error")
        return redirect(url_for("sales.create_sale_form"))

    if len(product_ids) != len(quantities):
        flash("Ошибка: несоответствие количества товаров и количеств", "error")
        return redirect(url_for("sales.create_sale_form"))

    try:
        total_sales_amount = Decimal('0')
        sales_created = 0
        errors = []

        # Сначала проверяем все товары на доступность
        for i, product_id_str in enumerate(product_ids):
            try:
                product_id = int(product_id_str)
                quantity = int(quantities[i])

                product = product_repo.get_by_id(product_id)
                if not product:
                    errors.append(f"Товар с ID {product_id} не найден")
                    continue

                if quantity <= 0:
                    errors.append(f"Количество для товара '{product.name}' должно быть больше нуля")
                    continue

                if product.stock_quantity < quantity:
                    errors.append(f"Недостаточно товара '{product.name}' на складе. Доступно: {product.stock_quantity}")
                    continue
            except (ValueError, IndexError) as e:
                errors.append(f"Ошибка обработки товара: {str(e)}")
                continue

        if errors:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("sales.create_sale_form"))

        # Если все проверки пройдены, создаем продажи и обновляем остатки
        for i, product_id_str in enumerate(product_ids):
            product_id = int(product_id_str)
            quantity = int(quantities[i])

            product = product_repo.get_by_id(product_id)
            price_to_use = product.discount_price if product.discount_price else product.price
            total_price = Decimal(str(price_to_use)) * quantity

            sale_repo.add(product_id, current_user.id, quantity, total_price)
            product_repo.update(product_id, stock_quantity=product.stock_quantity - quantity)

            total_sales_amount += total_price
            sales_created += 1

        if sales_created > 0:
            flash(f"Продажа успешно оформлена! Продано товаров: {sales_created}, Общая сумма: {total_sales_amount:.2f} руб.", "success")
        else:
            flash("Не удалось оформить продажу", "error")

    except Exception as e:
        flash(f"Ошибка при создании продажи: {str(e)}", "error")

    return redirect(url_for("sales.list_sales"))


@bp.get("/statistics")
@login_required
def statistics():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    total_revenue = sale_repo.get_total_revenue()
    total_sales_count = sale_repo.get_total_sales_count()
    top_products = sale_repo.get_top_products(limit=10)

    return render_template("sales/statistics.html",
                         total_revenue=total_revenue,
                         total_sales_count=total_sales_count,
                         top_products=top_products,
                         is_director=True)


@bp.get("/my_sales")
@login_required
def my_sales():
    if current_user.is_director():
        return redirect(url_for("sales.list_sales"))

    sales = sale_repo.get_by_cashier(current_user.id)
    
    sales_with_products = []
    total_revenue = 0
    for sale in sales:
        product = product_repo.get_by_id(sale.product_id)
        total_revenue += float(sale.total_price)
        sales_with_products.append({
            'sale': sale,
            'product': product
        })

    return render_template("sales/my_sales.html",
                         sales_with_products=sales_with_products,
                         total_revenue=total_revenue,
                         sales_count=len(sales))


@bp.get("/daily_report")
@login_required
def daily_report():
    if not current_user.is_director():
        flash("Доступ запрещен.", "error")
        return redirect(url_for("products.list_products"))

    from datetime import datetime, date
    report_date = request.args.get('date')
    
    if report_date:
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except:
            report_date = date.today()
    else:
        report_date = date.today()

    start_datetime = datetime.combine(report_date, datetime.min.time())
    end_datetime = datetime.combine(report_date, datetime.max.time())

    sales = Sale.query.filter(
        Sale.sale_date >= start_datetime,
        Sale.sale_date <= end_datetime
    ).order_by(Sale.sale_date.desc()).all()

    daily_revenue = sale_repo.get_revenue_by_date_range(start_datetime, end_datetime)
    
    sales_with_products = []
    for sale in sales:
        product = product_repo.get_by_id(sale.product_id)
        sales_with_products.append({
            'sale': sale,
            'product': product
        })

    return render_template("sales/daily_report.html",
                         sales_with_products=sales_with_products,
                         daily_revenue=daily_revenue,
                         report_date=report_date,
                         sales_count=len(sales))

