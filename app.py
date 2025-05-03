from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///graduates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'  # Для сессий и flash-сообщений
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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


# Callback для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание базы данных
with app.app_context():
    db.create_all()
    # Создаём админа, если его нет
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()


# Главная страница: список выпускников
@app.route('/')
@login_required
def index():
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()
    graduates = Graduate.query.order_by(order).all()
    return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order)


# Страница добавления выпускника (только для админов и менеджеров)
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        try:
            graduate = Graduate(
                id=int(request.form['id']),
                name=request.form['name'],
                group=request.form['group'],
                graduation_year=request.form['graduation_year'],
                faculty=request.form['faculty']
            )
            db.session.add(graduate)
            db.session.commit()
            flash('Выпускник успешно добавлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('add.html')


# Страница "О проекте"
@app.route('/about')
@login_required
def about():
    return render_template('about.html')


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        keyword = request.form['keyword']

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