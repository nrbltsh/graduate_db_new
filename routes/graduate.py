from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Graduate, Tag, db, allowed_file
from werkzeug.utils import secure_filename
import os
import csv
import io
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

graduate_bp = Blueprint('graduate', __name__)

# Убедимся, что папка для загрузки существует
def ensure_upload_folder():
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_folder):
        logger.info(f"Creating upload folder: {upload_folder}")
        os.makedirs(upload_folder)
    return upload_folder

# Страница добавления выпускника
@graduate_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        try:
            # Получение данных из формы
            name = request.form['name'].strip()
            group = request.form['group'].strip()
            faculty = request.form['faculty'].strip()
            graduation_year = request.form['graduation_year'].strip()
            bio = request.form['bio'].strip() or ''

            # Валидация обязательных полей
            if not name:
                flash('Имя не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))
            if not group:
                flash('Группа не может быть пустой.', 'danger')
                return redirect(url_for('graduate.add'))
            if not faculty:
                flash('Факультет не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))
            if not graduation_year:
                flash('Год выпуска не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))

            photo_path = None
            if 'photo' in request.files:
                file = request.files['photo']
                logger.debug(f"Received file: {file.filename if file else 'None'}")
                if file and file.filename:
                    if allowed_file(file.filename, current_app.config.get('ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png'})):
                        filename = secure_filename(file.filename)
                        upload_folder = ensure_upload_folder()
                        file_path = os.path.join(upload_folder, filename)
                        logger.debug(f"Saving file to: {file_path}")
                        file.save(file_path)
                        photo_path = filename
                        logger.debug(f"File saved: {photo_path}")
                    else:
                        flash('Недопустимый формат файла. Разрешены: jpg, jpeg, png.', 'danger')
                        return redirect(url_for('graduate.add'))
                else:
                    logger.debug("No file selected or empty filename")

            # Обработка тегов
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
                name=name,
                group=group,
                graduation_year=graduation_year,
                faculty=faculty,
                bio=bio,
                photo=photo_path
            )
            graduate.tags = tags
            db.session.add(graduate)
            db.session.commit()
            flash('Выпускник успешно добавлен!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding graduate: {str(e)}")
            flash(f'Ошибка при добавлении выпускника: {str(e)}', 'danger')
            return redirect(url_for('graduate.add'))

    return render_template('add.html', tags=Tag.query.all())

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
            # Получение данных из формы
            name = request.form['name'].strip()
            group = request.form['group'].strip()
            faculty = request.form['faculty'].strip()
            graduation_year = request.form['graduation_year'].strip()
            bio = request.form['bio'].strip() or ''

            # Валидация обязательных полей
            if not name:
                flash('Имя не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not group:
                flash('Группа не может быть пустой.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not faculty:
                flash('Факультет не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not graduation_year:
                flash('Год выпуска не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))

            graduate.name = name
            graduate.group = group
            graduate.graduation_year = graduation_year
            graduate.faculty = faculty
            graduate.bio = bio

            if 'photo' in request.files:
                file = request.files['photo']
                logger.debug(f"Received file: {file.filename if file else 'None'}")
                if file and file.filename:
                    if allowed_file(file.filename, current_app.config.get('ALLOWED_EXTENSIONS', {'jpg', 'jpeg', 'png'})):
                        filename = secure_filename(file.filename)
                        upload_folder = ensure_upload_folder()
                        file_path = os.path.join(upload_folder, filename)
                        logger.debug(f"Saving file to: {file_path}")
                        file.save(file_path)
                        graduate.photo = filename
                        logger.debug(f"File saved: {graduate.photo}")
                    else:
                        flash('Недопустимый формат файла. Разрешены: jpg, jpeg, png.', 'danger')
                        return redirect(url_for('graduate.edit', id=id))
                else:
                    logger.debug("No file selected or empty filename")

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
            db.session.rollback()
            logger.error(f"Error updating graduate: {str(e)}")
            flash(f'Ошибка при обновлении данных: {str(e)}', 'danger')
            return redirect(url_for('graduate.edit', id=id))

    return render_template('edit.html', graduate=graduate, tags=Tag.query.all())

# Удаление выпускника с переиндексацией id
@graduate_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    graduate = Graduate.query.get_or_404(id)
    try:
        # Удаляем запись
        db.session.delete(graduate)
        db.session.commit()

        # Переиндексация оставшихся записей
        graduates = Graduate.query.order_by(Graduate.id).all()
        new_id = 1
        for grad in graduates:
            # Обновляем связи в graduate_tags
            db.session.execute(
                db.text("UPDATE graduate_tags SET graduate_id = :new_id WHERE graduate_id = :old_id"),
                {"new_id": new_id, "old_id": grad.id}
            )
            # Обновляем id выпускника
            grad.id = new_id
            new_id += 1
        db.session.commit()

        flash('Выпускник удалён, ID переиндексированы!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении или переиндексации: {str(e)}', 'danger')
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
                        if not row['Имя'].strip():
                            continue

                        name = row['Имя'].strip()
                        group = row['Группа'].strip()
                        faculty = row['Факультет'].strip()
                        graduation_year = row['Год выпуска'].strip()

                        if not name:
                            flash(f"Ошибка в строке {csv_reader.line_num}: Имя не может быть пустым.", 'danger')
                            continue
                        if not group:
                            flash(f"Ошибка в строке {csv_reader.line_num}: Группа не может быть пустой.", 'danger')
                            continue
                        if not faculty:
                            flash(f"Ошибка в строке {csv_reader.line_num}: Факультет не может быть пустым.", 'danger')
                            continue
                        if not graduation_year:
                            flash(f"Ошибка в строке {csv_reader.line_num}: Год выпуска не может быть пустым.", 'danger')
                            continue
                        if graduation_year and not graduation_year.isdigit():
                            flash(f"Ошибка в строке {csv_reader.line_num}: Год выпуска должен быть числом.", 'danger')
                            continue

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

                        graduate = Graduate(
                            name=name,
                            group=group,
                            graduation_year=graduation_year,
                            faculty=faculty,
                            bio=row['Биография'].strip() or '',
                            photo=None
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
            db.session.rollback()
            flash(f'Ошибка при обработке файла: {str(e)}', 'danger')
    return render_template('upload.html')