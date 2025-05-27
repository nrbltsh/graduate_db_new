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
import pandas as pd  # Import pandas for Excel export
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Main page: list of graduates with filtering and pagination
@main_bp.route('/')
@login_required
def index():
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    email_file = request.args.get('email_file', '')
    phone = request.args.get('phone', '')
    work = request.args.get('work', '')
    # tags = request.args.get('tags', '')
    page = request.args.get('page', 1, type=int)
    per_page = 100

    query = Graduate.query
    if name:
        query = query.filter(Graduate.name.ilike(f'%{name}%'))
    if graduation_year:
        query = query.filter(Graduate.graduation_year == graduation_year)
    if faculty:
        query = query.filter(Graduate.faculty.ilike(f'%{faculty}%'))
    if email_file:
        query = query.filter(Graduate.email_file.ilike(f'%{email_file}%'))
    if phone:
        query = query.filter(Graduate.phone.ilike(f'%{phone}%'))
    if work:
        query = query.filter(Graduate.work.ilike(f'%{work}%'))
    # if tags:
    #     tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    #     for tag_name in tag_list:
    #         query = query.join(graduate_tags).join(Tag).filter(Tag.name.ilike(f'%{tag_name}%'))

    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    pagination = query.order_by(order).paginate(page=page, per_page=per_page, error_out=False)
    graduates = pagination.items
    # all_tags = Tag.query.all()

    return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order,
                           name=name, graduation_year=graduation_year, faculty=faculty, email_file=email_file,
                           phone=phone, work=work, pagination=pagination)

    # return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order,
    #                        name=name, graduation_year=graduation_year, faculty=faculty, tags=tags,
    #                        all_tags=all_tags, pagination=pagination)

# Export to CSV
@main_bp.route('/export')
@login_required
def export():
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    tags = request.args.get('tags', '')

    query = Graduate.query
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

    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    graduates = query.order_by(order).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Имя', 'Группа', 'Год выпуска', 'Институт', 'Email', 'Номер телефона', 'Место работы', 'Биография', 'Направление (Образовательная программа)'])

    for graduate in graduates:
        tags = ', '.join([tag.name for tag in graduate.tags])
        writer.writerow([
            graduate.id,
            graduate.name,
            graduate.group,
            graduate.graduation_year,
            graduate.faculty,
            graduate.email_file or '',
            graduate.phone or '',
            graduate.work or '',
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

# Export to PDF
@main_bp.route('/export_pdf')
@login_required
def export_pdf():
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    tags = request.args.get('tags', '')

    query = Graduate.query
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

    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    graduates = query.order_by(order).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    data = [['ID', 'Имя', 'Группа', 'Год выпуска', 'Институт', 'Направление (Образовательная программа)']]

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

# Export to Excel
@main_bp.route('/export_excel')
@login_required
def export_excel():
    name = request.args.get('name', '')
    graduation_year = request.args.get('graduation_year', '')
    faculty = request.args.get('faculty', '')
    tags = request.args.get('tags', '')

    query = Graduate.query
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

    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    try:
        graduates = query.order_by(order).all()
        logger.debug(f"Exporting {len(graduates)} graduates to Excel with filters: name={name}, year={graduation_year}, faculty={faculty}, tags={tags}")

        # Prepare data for Excel
        data = []
        for graduate in graduates:
            tags = ', '.join([tag.name for tag in graduate.tags])
            data.append({
                'ID': graduate.id,
                'Имя': graduate.name,
                'Группа': graduate.group,
                'Год выпуска': graduate.graduation_year,
                'Институт': graduate.faculty,
                'Email': graduate.email_file or '',
                'Номер телефона': graduate.phone or '',
                'Место работы': graduate.work or '',
                'Биография': graduate.bio or '',
                'Направление (Образовательная программа)': tags
            })

        # Create a DataFrame
        df = pd.DataFrame(data, columns=['ID', 'Имя', 'Группа', 'Год выпуска', 'Институт', 'Email', 'Номер телефона', 'Место работы', 'Биография', 'Направление (Образовательная программа)'])

        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Graduates')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='graduates_export.xlsx'
        )
    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}")
        flash(f'Ошибка при создании Excel файла: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

# Graduate profile page
@main_bp.route('/graduate/<int:id>')
@login_required
def graduate(id):
    graduate = Graduate.query.get_or_404(id)
    return render_template('graduate.html', graduate=graduate)

# About page
@main_bp.route('/about')
@login_required
def about():
    return render_template('about.html')

# Statistics page
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

    tags_data = db.session.query(
        Tag.name,
        db.func.count(graduate_tags.c.graduate_id).label('count')
    ).join(graduate_tags).group_by(Tag.name).all()

    groups_data = db.session.query(
        Graduate.group,
        db.func.count(Graduate.id).label('count')
    ).group_by(Graduate.group).all()

    return render_template('stats.html', years_data=years_data, faculties_data=faculties_data,
                           tags_data=tags_data, groups_data=groups_data)