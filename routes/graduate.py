from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Graduate, Tag, db, allowed_file
from werkzeug.utils import secure_filename
import os

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
            return redirect(url_for('main.index'))
        except Exception as e:
            flash(str(e), 'danger')
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
            return redirect(url_for('main.graduate', id=graduate.id))
        except Exception as e:
            flash(str(e), 'danger')
    return render_template('edit.html', graduate=graduate, tags=Tag.query.all())


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