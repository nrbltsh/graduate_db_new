from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
from werkzeug.security import generate_password_hash, check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

# Страница регистрации
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        keyword = request.form.get('keyword', '').strip()

        # Валидация логина (только латинские буквы, цифры, подчеркивание)
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            flash('Имя пользователя должно содержать только латинские буквы, цифры или подчеркивание.', 'danger')
            return redirect(url_for('auth.register'))
        # Валидация длины логина
        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа.', 'danger')
            return redirect(url_for('auth.register'))
        # Валидация пароля (только латинские буквы, цифры, специальные символы, минимум 8 символов)
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*_-]+$', password):
            flash('Пароль должен содержать только латинские буквы, цифры или символы !@#$%^&*_-', 'danger')
            return redirect(url_for('auth.register'))
        if len(password) < 8:
            flash('Пароль должен содержать минимум 8 символов.', 'danger')
            return redirect(url_for('auth.register'))
        # Проверка уникальности логина
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято.', 'danger')
            return redirect(url_for('auth.register'))
        # Проверка ключевого слова для менеджера
        if role == 'manager' and keyword.lower() != 'knumanager':
            flash('Неверное ключевое слово для роли менеджера.', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=username,
            password=generate_password_hash(password),
            role=role if role in ['guest', 'manager'] else 'guest'
        )
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

# Страница логина
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('main.index'))
        flash('Неверное имя пользователя или пароль.', 'danger')
    return render_template('login.html')

# Логаут
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'success')
    return redirect(url_for('auth.login'))