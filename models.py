from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Проверка расширения файла
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='guest')  # guest, manager, admin

# Модель выпускника
class Graduate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(20), nullable=False)
    graduation_year = db.Column(db.String(4), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(200), nullable=True)
    tags = db.relationship('Tag', secondary='graduate_tags', backref=db.backref('graduates', lazy='dynamic'))

# Модель тега
class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

# Таблица связи выпускников и тегов
graduate_tags = db.Table('graduate_tags',
    db.Column('graduate_id', db.Integer, db.ForeignKey('graduate.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)