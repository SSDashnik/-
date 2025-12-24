import pytest
from app.startservice import app
from app.models import db
from app.models.user import User, UserRepo, ROLE_DIRECTOR, ROLE_CASHIER
from app.models.product import Product, ProductRepo
from app.models.sale import Sale, SaleRepo
from decimal import Decimal


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


@pytest.fixture
def admin_user(client):
    repo = UserRepo()
    return repo.add('admin', 'admin123', ROLE_DIRECTOR, 'Админ')


@pytest.fixture
def cashier_user(client):
    repo = UserRepo()
    return repo.add('cashier', 'cashier123', ROLE_CASHIER, 'Кассир')


@pytest.fixture
def test_product(client):
    repo = ProductRepo()
    return repo.add('Тестовый товар', 'Крем', Decimal('100.00'), 10, 'Описание', 'ART001', '50мл')


# Тест регистрации нового пользователя
def test_1_user_registration(client):
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    user = UserRepo().get_by_username('newuser')
    assert user is not None
    assert user.role == ROLE_CASHIER


# Тест успешного входа в систему
def test_2_user_login(client, admin_user):
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Товары'.encode('utf-8') in response.data or b'products' in response.data.lower()


# Тест входа с неверным паролем
def test_3_user_login_wrong_password(client, admin_user):
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'wrong'
    })
    assert response.status_code == 200
    assert 'Неверное'.encode('utf-8') in response.data or b'Invalid' in response.data


# Тест что создание товара требует авторизации
def test_4_product_creation_requires_auth(client):
    response = client.get('/products/create')
    assert response.status_code == 302


# Тест доступа к созданию товара для админа
def test_5_product_creation_as_admin(client, admin_user):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/products/create')
    assert response.status_code == 200


# Тест что кассир не может создавать товары
def test_6_product_creation_as_cashier_forbidden(client, cashier_user):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.get('/products/create', follow_redirects=True)
    assert response.status_code == 200
    response_lower = response.data.lower()
    assert 'запрещен'.encode('utf-8') in response_lower or b'forbidden' in response_lower


# Тест добавления нового товара админом
def test_7_product_add(client, admin_user):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.post('/products/create', data={
        'name': 'Новый товар',
        'category': 'Помада',
        'price': '250.00',
        'stock_quantity': '5',
        'article': 'ART002',
        'package': '10мл'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    product = ProductRepo().filter_by_name('Новый товар')
    assert len(product) > 0
    assert product[0].name == 'Новый товар'


# Тест отображения списка товаров
def test_8_product_list(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/products/')
    assert response.status_code == 200
    assert 'Тестовый товар'.encode('utf-8') in response.data


# Тест фильтрации товаров по категории
def test_9_product_filter_by_category(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/products/?category=Крем')
    assert response.status_code == 200
    assert 'Тестовый товар'.encode('utf-8') in response.data


# Тест фильтрации товаров по названию
def test_10_product_filter_by_name(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/products/?search=Тестовый')
    assert response.status_code == 200
    assert 'Тестовый товар'.encode('utf-8') in response.data


# Тест обновления товара админом
def test_11_product_update(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.post(f'/products/{test_product.id}/edit', data={
        'name': 'Обновленный товар',
        'category': 'Помада',
        'price': '150.00',
        'stock_quantity': '20',
        'article': 'ART003',
        'package': '15мл'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    updated = ProductRepo().get_by_id(test_product.id)
    assert updated.name == 'Обновленный товар'


# Тест удаления товара админом
def test_12_product_delete(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    product_id = test_product.id
    response = client.post(f'/products/{product_id}/delete', follow_redirects=True)
    assert response.status_code == 200
    
    deleted = ProductRepo().get_by_id(product_id)
    assert deleted is None


# Тест создания продажи кассиром
def test_13_sale_creation(client, cashier_user, test_product):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['2'],
        'confirmed': 'on'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    sales = SaleRepo().get_by_cashier(cashier_user.id)
    assert len(sales) > 0


# Тест что продажа требует подтверждения галочкой
def test_14_sale_requires_confirmation(client, cashier_user, test_product):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['2']
    }, follow_redirects=True)
    assert response.status_code == 200
    response_lower = response.data.lower()
    assert ('подтвердите'.encode('utf-8') in response_lower or 
            b'confirmed' in response_lower or 
            'добавьте'.encode('utf-8') in response_lower)


# Тест что продажа уменьшает остаток на складе
def test_15_sale_reduces_stock(client, cashier_user, test_product):
    initial_stock = test_product.stock_quantity
    
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['3'],
        'confirmed': 'on'
    }, follow_redirects=True)
    
    updated_product = ProductRepo().get_by_id(test_product.id)
    assert updated_product.stock_quantity == initial_stock - 3


# Тест что нельзя продать больше чем есть на складе
def test_16_sale_insufficient_stock(client, cashier_user, test_product):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['100'],
        'confirmed': 'on'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Недостаточно'.encode('utf-8') in response.data or b'insufficient' in response.data.lower()


# Тест страницы моих продаж для кассира
def test_17_my_sales_page(client, cashier_user, test_product):
    SaleRepo().add(test_product.id, cashier_user.id, 1, Decimal('100.00'))
    
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.get('/sales/my_sales')
    assert response.status_code == 200
    assert 'Мои продажи'.encode('utf-8') in response.data


# Тест что статистика доступна только директору
def test_18_statistics_only_for_director(client, cashier_user):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.get('/sales/statistics', follow_redirects=True)
    assert response.status_code == 200
    response_lower = response.data.lower()
    assert 'запрещен'.encode('utf-8') in response_lower or b'forbidden' in response_lower


# Тест что отчет за день доступен только директору
def test_19_daily_report_only_for_director(client, cashier_user):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.get('/sales/daily_report', follow_redirects=True)
    assert response.status_code == 200
    response_lower = response.data.lower()
    assert 'запрещен'.encode('utf-8') in response_lower or b'forbidden' in response_lower


# Тест установки скидки на товар админом
def test_20_discount_setting(client, admin_user, test_product):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.post(f'/products/{test_product.id}/set_discount', data={
        'discount_price': '80.00',
        'search': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    
    updated = ProductRepo().get_by_id(test_product.id)
    assert float(updated.discount_price) == 80.00


# Тест что скидка применяется при продаже
def test_21_discount_applied_in_sale(client, cashier_user, test_product):
    # Устанавливаем скидку
    ProductRepo().update(test_product.id, discount_price=Decimal('75.00'))
    
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    
    # Создаем продажу
    client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['1'],
        'confirmed': 'on'
    }, follow_redirects=True)
    
    # Проверяем, что использовалась цена со скидкой
    sales = SaleRepo().get_by_cashier(cashier_user.id)
    assert len(sales) > 0
    assert float(sales[0].total_price) == 75.00


# Тест что список пользователей доступен только директору
def test_22_user_list_only_for_director(client, cashier_user):
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    response = client.get('/users/', follow_redirects=True)
    assert response.status_code == 200
    response_lower = response.data.lower()
    assert 'запрещен'.encode('utf-8') in response_lower or b'forbidden' in response_lower


# Тест создания пользователя директором
def test_23_user_creation_by_director(client, admin_user):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.post('/users/create', data={
        'username': 'newcashier',
        'password': 'pass123',
        'role': ROLE_CASHIER,
        'full_name': 'Новый кассир'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    user = UserRepo().get_by_username('newcashier')
    assert user is not None
    assert user.role == ROLE_CASHIER


# Тест что при продаже используется цена со скидкой если она установлена
def test_24_sale_uses_discount_price(client, cashier_user, test_product):
    ProductRepo().update(test_product.id, discount_price=Decimal('75.00'))
    
    client.post('/auth/login', data={
        'username': 'cashier',
        'password': 'cashier123'
    }, follow_redirects=True)
    client.post('/sales/create', data={
        'product_ids': [str(test_product.id)],
        'quantities': ['2'],
        'confirmed': 'on'
    }, follow_redirects=True)
    
    sales = SaleRepo().get_by_cashier(cashier_user.id)
    assert len(sales) > 0
    assert float(sales[0].total_price) == 150.00


# Тест выхода из системы
def test_25_logout(client, admin_user):
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
