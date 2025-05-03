from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from models import Graduate, Tag, graduate_tags, db
from sqlalchemy import or_, and_
import csv
import io
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch

main_bp = Blueprint('main', __name__)


# Главная страница: список выпускников с фильтрацией и пагинацией
@main_bp.route('/')
@login_required
def index():
    # Параметры фильтрации
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    tags = request.args.get('tags', '')

    # Параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Количество записей на странице

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

    # Пагинация
    pagination = query.order_by(order).paginate(page=page, per_page=per_page, error_out=False)
    graduates = pagination.items

    # Доступные теги для формы
    all_tags = Tag.query.all()

    return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order,
                           name=name, graduation_year=graduation_year, faculty=faculty, tags=tags,
                           all_tags=all_tags, pagination=pagination)


# Экспорт в CSV
@main_bp.route('/export')
@login_required
def export():
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

    # Получение всех записей
    graduates = query.order_by(order).all()

    # Создание CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Имя', 'Группа', 'Год выпуска', 'Факультет', 'Биография', 'Теги'])

    for graduate in graduates:
        tags = ', '.join([tag.name for tag in graduate.tags])
        writer.writerow([
            graduate.id,
            graduate.name,
            graduate.group,
            graduate.graduation_year,
            graduate.faculty,
            graduate.bio or '',
            tags
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='graduates_export.csv'
    )


# Экспорт в PDF
@main_bp.route('/export_pdf')
@login_required
def export_pdf():
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

    # Получение всех записей
    graduates = query.order_by(order).all()

    # Создание PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    data = [['ID', 'Имя', 'Группа', 'Год выпуска', 'Факультет', 'Теги']]

    for graduate in graduates:
        tags = ', '.join([tag.name for tag in graduate.tags])
        data.append([
            str(graduate.id),
            graduate.name,
            graduate.group,
            graduate.graduation_year,
            graduate.faculty,
            tags
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    elements = [table]
    doc.build(elements)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='graduates_export.pdf'
    )


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
    years_data = db.session.query(
        Graduate.graduation_year,
        db.func.count(Graduate.id).label('count')
    ).group_by(Graduate.graduation_year).all()

    faculties_data = db.session.query(
        Graduate.faculty,
        db.func.count(Graduate.id).label('count')
    ).group_by(Graduate.faculty).all()

    return render_template('stats.html', years_data=years_data, faculties_data=faculties_data)