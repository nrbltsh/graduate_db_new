from flask import Blueprint, render_template, request
from flask_login import login_required
from models import Graduate, Tag, graduate_tags, db
from sqlalchemy import or_, and_

main_bp = Blueprint('main', __name__)


# Главная страница: список выпускников с фильтрацией
@main_bp.route('/')
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


# Страница профиля выпускника
@main_bp.route('/graduate/<int:id>')
@login_required
def graduate(id):
    graduate = Graduate.query.get_or_404(id)
    return render_template('graduate.html', graduate=graduate)


# Страница "О проекте"
@main_bp.route('/about')
@login_required
def about():
    return render_template('about.html')


# Страница статистики
@main_bp.route('/stats')
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