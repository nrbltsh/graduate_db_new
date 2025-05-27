from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import Graduate, Tag, db
from werkzeug.utils import secure_filename
import os
import pandas as pd  # Импорт pandas для обработки CSV и Excel
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

graduate_bp = Blueprint('graduate', __name__)


# Проверка существования папки для загрузки файлов
def ensure_upload_folder():
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_folder):
        logger.info(f"Создание папки для загрузки: {upload_folder}")
        os.makedirs(upload_folder)
    return upload_folder


# Проверка допустимого формата файла
def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'csv', 'xlsx', 'xls'}  # Поддержка CSV и Excel
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# Добавление выпускника
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
            email_file = request.form['email_file'].strip() or ''
            phone = request.form['phone'].strip() or ''
            work = request.form['work'].strip() or ''
            bio = request.form['bio'].strip() or ''
            tags_input = request.form.get('tags', '').strip()

            # Валидация обязательных полей
            if not name:
                flash('Имя не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))
            if not group:
                flash('Группа не может быть пустой.', 'danger')
                return redirect(url_for('graduate.add'))
            if not faculty:
                flash('Институт не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))
            if not graduation_year:
                flash('Год выпуска не может быть пустым.', 'danger')
                return redirect(url_for('graduate.add'))
            # Валидация года выпуска
            if not graduation_year.isdigit():
                flash('Год выпуска должен быть числом.', 'danger')
                return redirect(url_for('graduate.add'))
            year = int(graduation_year)
            if not (1900 <= year <= 2100):
                flash('Год выпуска должен быть в диапазоне 1900–2100.', 'danger')
                return redirect(url_for('graduate.add'))

            photo_path = None
            if 'photo' in request.files:
                file = request.files['photo']
                logger.debug(f"Получен файл: {file.filename if file else 'None'}")
                if file and file.filename:
                    if allowed_file(file.filename, {'jpg', 'jpeg', 'png'}):
                        filename = secure_filename(file.filename)
                        upload_folder = ensure_upload_folder()
                        file_path = os.path.join(upload_folder, filename)
                        logger.debug(f"Сохранение файла в: {file_path}")
                        file.save(file_path)
                        photo_path = filename
                        logger.debug(f"Файл сохранён: {photo_path}")
                    else:
                        flash('Недопустимый формат файла. Разрешены: jpg, jpeg, png.', 'danger')
                        return redirect(url_for('graduate.add'))
                else:
                    logger.debug("Файл не выбран или имя пустое")

            # Обработка Направления (Образовательная программа)
            tags = []
            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tag_names:
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
                email_file=email_file,
                phone=phone,
                work=work,
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
            logger.error(f"Ошибка при добавлении выпускника: {str(e)}")
            flash(f'Ошибка при добавлении выпускника: {str(e)}', 'danger')
            return redirect(url_for('graduate.add'))

    return render_template('add.html')


# Редактирование выпускника
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
            email_file = request.form['email_file'].strip() or ''
            phone = request.form['phone'].strip() or ''
            work = request.form['work'].strip() or ''
            bio = request.form['bio'].strip() or ''
            tags_input = request.form.get('tags', '').strip()
            remove_photo = 'remove_photo' in request.form

            # Валидация обязательных полей
            if not name:
                flash('Имя не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not group:
                flash('Группа не может быть пустой.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not faculty:
                flash('Институт не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            if not graduation_year:
                flash('Год выпуска не может быть пустым.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            # Валидация года выпуска
            if not graduation_year.isdigit():
                flash('Год выпуска должен быть числом.', 'danger')
                return redirect(url_for('graduate.edit', id=id))
            year = int(graduation_year)
            if not (1900 <= year <= 2100):
                flash('Год выпуска должен быть в диапазоне 1900–2100.', 'danger')
                return redirect(url_for('graduate.edit', id=id))

            graduate.name = name
            graduate.group = group
            graduate.graduation_year = graduation_year
            graduate.faculty = faculty
            graduate.email_file = email_file
            graduate.phone = phone
            graduate.work = work
            graduate.bio = bio

            # Обработка фото
            if remove_photo:
                if graduate.photo:
                    photo_path = os.path.join(ensure_upload_folder(), graduate.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        logger.debug(f"Удалено фото: {photo_path}")
                    graduate.photo = None
                    logger.debug("Поле фото очищено")
            elif 'photo' in request.files:
                file = request.files['photo']
                logger.debug(f"Получен файл: {file.filename if file else 'None'}")
                if file and file.filename:
                    if allowed_file(file.filename, {'jpg', 'jpeg', 'png'}):
                        if graduate.photo:
                            old_photo_path = os.path.join(ensure_upload_folder(), graduate.photo)
                            if os.path.exists(old_photo_path):
                                os.remove(old_photo_path)
                                logger.debug(f"Удалено старое фото: {old_photo_path}")
                        filename = secure_filename(file.filename)
                        upload_folder = ensure_upload_folder()
                        file_path = os.path.join(upload_folder, filename)
                        logger.debug(f"Сохранение файла в: {file_path}")
                        file.save(file_path)
                        graduate.photo = filename
                        logger.debug(f"Файл сохранён: {graduate.photo}")
                    else:
                        flash('Недопустимый формат файла. Разрешены: jpg, jpeg, png.', 'danger')
                        return redirect(url_for('graduate.edit', id=id))
                else:
                    logger.debug("Файл не выбран или имя пустое")

            # Обработка тегов
            tags = []
            if tags_input:
                tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tag_names:
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
            logger.error(f"Ошибка при обновлении данных: {str(e)}")
            flash(f'Ошибка при обновлении данных: {str(e)}', 'danger')
            return redirect(url_for('graduate.edit', id=id))

    current_tags = ', '.join(tag.name for tag in graduate.tags)
    return render_template('edit.html', graduate=graduate, current_tags=current_tags)


# Удаление одного выпускника с переиндексацией ID
@graduate_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))
    graduate = Graduate.query.get_or_404(id)
    try:
        db.session.delete(graduate)
        db.session.commit()

        graduates = Graduate.query.order_by(Graduate.id).all()
        new_id = 1
        for grad in graduates:
            db.session.execute(
                db.text("UPDATE graduate_tags SET graduate_id = :new_id WHERE graduate_id = :old_id"),
                {"new_id": new_id, "old_id": grad.id}
            )
            grad.id = new_id
            new_id += 1
        db.session.commit()

        flash('Выпускник удалён, ID переиндексированы!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении или переиндексации: {str(e)}', 'danger')
    return redirect(url_for('main.index'))


# Массовое удаление выпускников
@graduate_bp.route('/delete_multiple', methods=['POST'])
@login_required
def delete_multiple():
    if current_user.role not in ['admin', 'manager']:
        flash('Доступ разрешён только администраторам и менеджерам.', 'danger')
        return redirect(url_for('main.index'))

    try:
        # Получение списка ID из формы
        graduate_ids = request.form.getlist('graduate_ids')
        if not graduate_ids:
            flash('Не выбраны выпускники для удаления.', 'danger')
            return redirect(url_for('main.index'))

        # Преобразование ID в целые числа и проверка существования
        graduate_ids = [int(id) for id in graduate_ids]
        graduates_to_delete = Graduate.query.filter(Graduate.id.in_(graduate_ids)).all()

        if not graduates_to_delete:
            flash('Выбранные выпускники не найдены.', 'danger')
            return redirect(url_for('main.index'))

        # Удаление записей
        for graduate in graduates_to_delete:
            db.session.delete(graduate)
        db.session.commit()

        # Переиндексация ID
        graduates = Graduate.query.order_by(Graduate.id).all()
        new_id = 1
        for grad in graduates:
            db.session.execute(
                db.text("UPDATE graduate_tags SET graduate_id = :new_id WHERE graduate_id = :old_id"),
                {"new_id": new_id, "old_id": grad.id}
            )
            grad.id = new_id
            new_id += 1
        db.session.commit()

        flash(f'Удалено {len(graduates_to_delete)} выпускников, ID переиндексированы!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при массовом удалении: {str(e)}")
        flash(f'Ошибка при массовом удалении или переиндексации: {str(e)}', 'danger')

    return redirect(url_for('main.index'))


# Загрузка данных из CSV или Excel
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

            # Проверка допустимого формата файла
            if file and allowed_file(file.filename, {'csv', 'xlsx', 'xls'}):
                filename = secure_filename(file.filename)
                file_extension = filename.rsplit('.', 1)[1].lower()
                logger.debug(f"Обработка файла: {filename}, расширение: {file_extension}")

                # Ожидаемые заголовки
                expected_headers = ['ID', 'Имя', 'Группа', 'Год выпуска', 'Институт', 'Email', 'Номер телефона', 'Место работы', 'Биография', 'Направление (Образовательная программа)']

                # Чтение файла в зависимости от формата
                if file_extension == 'csv':
                    try:
                        df = pd.read_csv(file, encoding='utf-8')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='cp1251')
                else:
                    df = pd.read_excel(file)

                # Проверка наличия ожидаемых заголовков
                if not all(header in df.columns for header in expected_headers):
                    flash(
                        'Неверный формат файла. Ожидаемые столбцы: ID, Имя, Группа, Год выпуска, Институт, Email, Номер телефона, Место работы, Биография, Направление (Образовательная программа).',
                        'danger')
                    return redirect(url_for('graduate.upload'))

                added = 0
                for index, row in df.iterrows():
                    try:
                        # Пропуск строк с пустым именем
                        name = str(row['Имя']).strip() if pd.notna(row['Имя']) else ''
                        if not name:
                            flash(f"Ошибка в строке {index + 2}: Имя не может быть пустым.", 'danger')
                            continue

                        group = str(row['Группа']).strip() if pd.notna(row['Группа']) else ''
                        faculty = str(row['Институт']).strip() if pd.notna(row['Институт']) else ''
                        graduation_year = str(row['Год выпуска']).strip() if pd.notna(row['Год выпуска']) else ''

                        # Валидация обязательных полей
                        if not group:
                            flash(f"Ошибка в строке {index + 2}: Группа не может быть пустой.", 'danger')
                            continue
                        if not faculty:
                            flash(f"Ошибка в строке {index + 2}: Институт не может быть пустым.", 'danger')
                            continue
                        if not graduation_year:
                            flash(f"Ошибка в строке {index + 2}: Год выпуска не может быть пустым.", 'danger')
                            continue
                        if not graduation_year.isdigit():
                            flash(f"Ошибка в строке {index + 2}: Год выпуска должен быть числом.", 'danger')
                            continue
                        year = int(graduation_year)
                        if not (1900 <= year <= 2100):
                            flash(f"Ошибка в строке {index + 2}: Год выпуска должен быть в диапазоне 1900–2100.",
                                  'danger')
                            continue

                        # Обработка биографии
                        email_file = str(row['Email']).strip() if pd.notna(row['Email']) else ''
                        phone = str(row['Номер телефона']).strip() if pd.notna(row['Номер телефона']) else ''
                        work = str(row['Место работы']).strip() if pd.notna(row['Место работы']) else ''
                        bio = str(row['Биография']).strip() if pd.notna(row['Биография']) else ''

                        # Обработка тегов
                        tags_input = str(row['Направление (Образовательная программа)']).strip() if pd.notna(row['Направление (Образовательная программа)']) else ''
                        tags = []
                        if tags_input and tags_input.lower() != 'nan':
                            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                            for tag_name in tag_names:
                                tag = Tag.query.filter_by(name=tag_name).first()
                                if not tag:
                                    tag = Tag(name=tag_name)
                                    db.session.add(tag)
                                tags.append(tag)

                        # Создание записи о выпускнике
                        graduate = Graduate(
                            name=name,
                            group=group,
                            graduation_year=graduation_year,
                            faculty=faculty,
                            email_file=email_file,
                            phone=phone,
                            work=work,
                            bio=bio,
                            photo=None
                        )
                        graduate.tags = tags
                        db.session.add(graduate)
                        added += 1
                    except Exception as e:
                        flash(f"Ошибка в строке {index + 2}: {str(e)}", 'danger')
                        continue

                db.session.commit()
                flash(f'Успешно добавлено {added} выпускников.', 'success')
                return redirect(url_for('main.index'))
            else:
                flash('Файл должен быть в формате CSV, XLSX или XLS.', 'danger')
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при обработке файла: {str(e)}")
            flash(f'Ошибка при обработке файла: {str(e)}', 'danger')
    return render_template('upload.html')