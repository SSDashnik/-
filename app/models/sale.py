from app.models import db
from datetime import datetime


class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    sale_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, product_id, cashier_id, quantity, total_price):
        self.product_id = product_id
        self.cashier_id = cashier_id
        self.quantity = quantity
        self.total_price = total_price
        self.sale_date = datetime.utcnow()

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'cashier_id': self.cashier_id,
            'quantity': self.quantity,
            'total_price': float(self.total_price),
            'sale_date': self.sale_date.isoformat()
        }


class SaleRepo:
    def add(self, product_id, cashier_id, quantity, total_price):
        sale = Sale(product_id, cashier_id, quantity, total_price)
        db.session.add(sale)
        db.session.commit()
        return sale

    def all(self):
        return Sale.query.order_by(Sale.sale_date.desc()).all()

    def get_by_id(self, sale_id):
        return Sale.query.get(sale_id)

    def get_by_cashier(self, cashier_id):
        return Sale.query.filter_by(cashier_id=cashier_id).order_by(Sale.sale_date.desc()).all()

    def get_by_product(self, product_id):
        return Sale.query.filter_by(product_id=product_id).all()

    def get_total_revenue(self):
        from sqlalchemy import func
        result = db.session.query(func.sum(Sale.total_price)).scalar()
        return float(result) if result else 0.0

    def get_total_sales_count(self):
        return Sale.query.count()

    def get_revenue_by_date_range(self, start_date, end_date):
        from sqlalchemy import func
        result = db.session.query(func.sum(Sale.total_price)).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date
        ).scalar()
        return float(result) if result else 0.0

    def get_top_products(self, limit=10):
        from sqlalchemy import func
        from app.models.product import Product
        results = db.session.query(
            Product.name,
            func.sum(Sale.quantity).label('total_quantity'),
            func.sum(Sale.total_price).label('total_revenue')
        ).join(Sale).group_by(Product.id, Product.name).order_by(
            func.sum(Sale.total_price).desc()
        ).limit(limit).all()
        return results

