from flask import Flask
from flask_login import LoginManager
from config import Config

# Инициализация приложения
app = Flask(__name__)
app.config.from_object(Config)

# Инициализация расширений
from models import db
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def init_db():
    """Создание таблиц базы данных и начальных данных"""
    from models import Category
    db.create_all()
    
    # Создание базовых категорий для финансов
    if Category.query.count() == 0:
        default_categories = [
            Category(name='Еда', type='expense'),
            Category(name='Транспорт', type='expense'),
            Category(name='Развлечения', type='expense'),
            Category(name='Здоровье', type='expense'),
            Category(name='Образование', type='expense'),
            Category(name='Покупки', type='expense'),
            Category(name='Коммунальные услуги', type='expense'),
            Category(name='Зарплата', type='income'),
            Category(name='Подработка', type='income'),
            Category(name='Другое', type='income'),
        ]
        for category in default_categories:
            db.session.add(category)
        db.session.commit()

# Импорт маршрутов
from routes.auth import auth_bp
from routes.finance import finance_bp
from routes.habits import habits_bp
from routes.recipes import recipes_bp
from routes.study import study_bp
from routes.inventory import inventory_bp
from routes.events import events_bp
from routes.main import main_bp
from routes.demo import demo_bp

# Регистрация Blueprint'ов
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(demo_bp)
app.register_blueprint(finance_bp, url_prefix='/finance')
app.register_blueprint(habits_bp, url_prefix='/habits')
app.register_blueprint(recipes_bp, url_prefix='/recipes')
app.register_blueprint(study_bp, url_prefix='/study')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(events_bp, url_prefix='/events')

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
