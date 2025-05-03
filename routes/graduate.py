from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Graduate, Tag, db, allowed_file
from werkzeug.utils import secure_filename
import os
import csv
import io

graduate_bp = Blueprint('graduate', __name__)


# Страница добавления выпускника
@graduate_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            photo_path = None
            if 'photo' in request.files:
                file = request.files['photo']
                if file and allowed_file(file.filename, graduate_bp.app.config['ALLOWED_EXTENSIONS']):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(graduate_bp.app.config['UPLOAD_FOLDER'], filename))
                    photo_path = filename

            tags_input = request.form.getlist('tags')
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
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(str(e), 'danger')

    groups = db.session.query(Graduate.group).distinct().all()
    groups = [group[0] for group in groups if group[0]]
    faculties = db.session.query(Graduate.faculty).distinct().all()
    faculties = [faculty[0] for faculty in faculties if faculty[0]]

    return render_template('add.html', tags=Tag.query.all(), groups=groups, faculties=faculties)


# Страница редактирования выпускника
@graduate_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
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
                if file and allowed_file(file.filename, graduate_bp.app.config['ALLOWED_EXTENSIONS']):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(graduate_bp.app.config['UPLOAD_FOLDER'], filename))
                    graduate.photo = filename

            tags_input = request.form.getlist('tags')
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
            return redirect(url_for('main.graduate', id=graduate.id))
        except Exception as e:
            flash(str(e), 'danger')

    groups = db.session.query(Graduate.group).distinct().all()
    groups = [group[0] for group in groups if group[0]]
    faculties = db.session.query(Graduate.faculty).distinct().all()
    faculties = [faculty[0] for faculty in faculties if faculty[0]]

    return render_template('edit.html', graduate=graduate, tags=Tag.query.all(), groups=groups, faculties=faculties)


# Удаление выпускника
@graduate_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    graduate = Graduate.query.get_or_404(id)
    db.session.delete(graduate)
    db.session.commit()
    flash('Выпускник удалён!', 'success')
    return redirect(url_for('main.index'))


# Загрузка данных из CSV
@graduate_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('Файл не выбран.', 'danger')
                return redirect(url_for('graduate.upload'))
            file = request.files['file']
            if file.filename == '':
                flash('Файл не выбран.', 'danger')
                return redirect(url_for('graduate.upload'))
            if file and file.filename.endswith('.csv'):
                stream = io.StringIO(file.stream.read().decode('utf-8'), newline='')
                csv_reader = csv.DictReader(stream)
                expected_headers = ['ID', 'Имя', 'Группа', 'Год выпуска', 'Факультет', 'Биография', 'Теги']
                if not all(header in csv_reader.fieldnames for header in expected_headers):
                    flash(
                        'Неверный формат CSV. Ожидаемые столбцы: ID, Имя, Группа, Год выпуска, Факультет, Биография, Теги.',
                        'danger')
                    return redirect(url_for('graduate.upload'))

                added = 0
                for row in csv_reader:
                    try:
                        # Пропускаем пустые строки
                        if not row['Имя'].strip():
                            continue

                        # Проверка года выпуска
                        graduation_year = row['Год выпуска'].strip()
                        if graduation_year and not graduation_year.isdigit():
                            flash(f"Ошибка в строке {csv_reader.line_num}: Год выпуска должен быть числом.", 'danger')
                            continue

                        # Обработка тегов
                        tags_input = row['Теги'].split(',') if row['Теги'] else []
                        tags = []
                        for tag_name in tags_input:
                            tag_name = tag_name.strip()
                            if tag_name:
                                tag = Tag.query.filter_by(name=tag_name).first()
                                if not tag:
                                    tag = Tag(name=tag_name)
                                    db.session.add(tag)
                                tags.append(tag)

                        # Создание выпускника
                        graduate = Graduate(
                            name=row['Имя'].strip(),
                            group=row['Группа'].strip() or None,
                            graduation_year=row['Год выпуска'].strip() or None,
                            faculty=row['Факультет'].strip() or None,
                            bio=row['Биография'].strip() or None,
                            photo=None  # Фото через CSV не загружаем
                        )
                        graduate.tags = tags
                        db.session.add(graduate)
                        added += 1
                    except Exception as e:
                        flash(f"Ошибка в строке {csv_reader.line_num}: {str(e)}", 'danger')
                        continue

                db.session.commit()
                flash(f'Успешно добавлено {added} выпускников.', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Файл должен быть в формате CSV.', 'danger')
        except Exception as e:
            flash(f'Ошибка при обработке файла: {str(e)}', 'danger')
    return render_template('upload.html')