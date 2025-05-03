from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from sqlalchemy import or_, and_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///graduates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# Проверка расширения файла
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


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


# Callback для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


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


# Главная страница: список выпускников с фильтрацией
@app.route('/')
@login_required
def index():
    # Параметры фильтрации
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    tags = request.args.get('tags', '')

    # Базовый запрос
    query = Graduate.query

    # Применение фильтров
    if name:
        query = query.filter(Graduate.name.ilike(f'%{name}%'))
    if graduation_year:
        query = query.filter(Graduate.graduation_year == graduation_year)
    if faculty:
        query = query.filter(Graduate.faculty.ilike(f'%{faculty}%'))
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        for tag_name in tag_list:
            query = query.join(graduate_tags).join(Tag).filter(Tag.name.ilike(f'%{tag_name}%'))

    # Сортировка
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    # Получение результатов
    graduates = query.order_by(order).all()

    # Доступные теги для формы
    all_tags = Tag.query.all()

    return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order,
                           name=name, graduation_year=graduation_year, faculty=faculty, tags=tags, all_tags=all_tags)


# Страница добавления выпускника
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            photo_path = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    photo_path = filename

            tags_input = request.form.get('tags', '').split(',')
            tags = []
            for tag_name in tags_input:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    tags.append(tag)

            graduate = Graduate(
                id=int(request.form['id']),
                name=request.form['name'],
                group=request.form['group'],
                graduation_year=request.form['graduation_year'],
                faculty=request.form['faculty'],
                bio=request.form['bio'],
                photo=photo_path
            )
            graduate.tags = tags
            db.session.add(graduate)
            db.session.commit()
            flash('Выпускник успешно добавлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add.html', tags=Tag.query.all())


# Страница профиля выпускника
@app.route('/graduate/<int:id>')
@login_required
def graduate(id):
    graduate = Graduate.query.get_or_404(id)
    return render_template('graduate.html', graduate=graduate)


# Страница редактирования выпускника
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('index'))
    graduate = Graduate.query.get_or_404(id)
    if request.method == 'POST':
        try:
            graduate.name = request.form['name']
            graduate.group = request.form['group']
            graduate.graduation_year = request.form['graduation_year']
            graduate.faculty = request.form['faculty']
            graduate.bio = request.form['bio']

            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    graduate.photo = filename

            tags_input = request.form.get('tags', '').split(',')
            tags = []
            for tag_name in tags_input:
                tag_name = tag_name.strip()
                if tag_name:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    tags.append(tag)
            graduate.tags = tags

            db.session.commit()
            flash('Данные выпускника обновлены!', 'success')
            return redirect(url_for('graduate', id=graduate.id))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('edit.html', graduate=graduate, tags=Tag.query.all())


# Удаление выпускника
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('index'))
    graduate = Graduate.query.get_or_404(id)
    db.session.delete(graduate)
    db.session.commit()
    flash('Выпускник удалён!', 'success')
    return redirect(url_for('index'))


# Страница "О проекте"
@app.route('/about')
@login_required
def about():
    return render_template('about.html')


# Страница статистики
@app.route('/stats')
@login_required
def stats():
    # Подсчёт выпускников по годам
    years_data = db.session.query(
        Graduate.graduation_year,
        db.func.count(Graduate.id).label('count')
    ).group_by(Graduate.graduation_year).all()

    # Подсчёт выпускников по факультетам
    faculties_data = db.session.query(
        Graduate.faculty,
        db.func.count(Graduate.id).label('count')
    ).group_by(Graduate.faculty).all()

    return render_template('stats.html', years_data=years_data, faculties_data=faculties_data)


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        keyword = request.form.get('keyword', '')

        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'danger')
        elif role == 'manager' and keyword.lower() != 'knumanager':
            flash('Неверное ключевое слово для роли менеджера.', 'danger')
        else:
            user = User(
                username=username,
                password=generate_password_hash(password),
                role=role if role in ['guest', 'manager'] else 'guest'
            )
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')


# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html')


# Логаут
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)