from app.models import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    article = db.Column(db.String(50), nullable=True)
    package = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=True)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    sales = db.relationship('Sale', backref='product', lazy=True)

    def __init__(self, name, category, price, stock_quantity, description=None, discount_price=None, article=None, package=None):
        self.name = name
        self.article = article
        self.package = package
        self.category = category
        self.price = price
        self.discount_price = discount_price
        self.stock_quantity = stock_quantity
        self.description = description

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'price': float(self.price),
            'stock_quantity': self.stock_quantity,
            'description': self.description
        }


class ProductRepo:
    def all(self):
        return db.session.query(Product).all()

    def get_by_id(self, product_id):
        return Product.query.get(product_id)

    def add(self, name, category, price, stock_quantity, description=None, article=None, package=None):
        product = Product(name, category, price, stock_quantity, description, None, article, package)
        db.session.add(product)
        db.session.commit()
        return product

    def update(self, product_id, name=None, category=None, price=None, 
               stock_quantity=None, description=None, discount_price=None, article=None, package=None):
        product = self.get_by_id(product_id)
        if not product:
            return None
        if name:
            product.name = name
        if category:
            product.category = category
        if price is not None:
            product.price = price
        if stock_quantity is not None:
            product.stock_quantity = stock_quantity
        if description is not None:
            product.description = description
        if discount_price is not None:
            product.discount_price = discount_price
        if article is not None:
            product.article = article
        if package is not None:
            product.package = package
        db.session.commit()
        return product

    def delete(self, product_id):
        product = self.get_by_id(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return True
        return False

    def filter_by_category(self, category):
        return Product.query.filter_by(category=category).all()

    def filter_by_name(self, search_term):
        return Product.query.filter(Product.name.ilike(f'%{search_term}%')).all()

    def get_categories(self):
        categories = db.session.query(Product.category).distinct().all()
        return [cat[0] for cat in categories]

