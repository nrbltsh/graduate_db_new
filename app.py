from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from models import db, User
from routes.main import main_bp
from routes.auth import auth_bp
from routes.graduate import graduate_bp
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Callback для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Регистрация Blueprint’ов
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(graduate_bp)

# Создание базы данных
with app.app_context():
    db.create_all()
    if not db.session.get(User, 1):  # Проверяем, есть ли админ
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)