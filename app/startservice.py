from flask import Flask, render_template
from flask_login import LoginManager
from app.controllers.products_controller import bp as products_bp
from app.controllers.sales_controller import bp as sales_bp
from app.controllers.users_controller import bp as users_bp
from app.controllers.auth_controller import bp as auth_bp
from app.models import db
from app.models.user import User, UserRepo, ROLE_DIRECTOR, ROLE_CASHIER
from app.models.product import Product
from app.models.sale import Sale

app = Flask(__name__, template_folder="views", static_folder="static")
app.secret_key = "replace-this-with-a-secure-random-key-in-production"

import os
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "cosmeticshop.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(products_bp)
app.register_blueprint(sales_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)

@app.get("/")
def index():
    return render_template("index.html")

with app.app_context():
    db.create_all()

    repo = UserRepo()
    if not repo.get_by_username('1'):
        repo.add('1', '1', ROLE_DIRECTOR, 'Админ')
    
    if not repo.get_by_username('2'):
        repo.add('2', '2', ROLE_CASHIER, 'Продавец')

if __name__ == "__main__":
    app.run(debug=True, port=5001)
