from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///graduates.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель выпускника
class Graduate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(20), nullable=False)
    graduation_year = db.Column(db.String(4), nullable=False)
    faculty = db.Column(db.String(100), nullable=False)


# Создание базы данных
with app.app_context():
    db.create_all()


# Главная страница: список выпускников
@app.route('/')
def index():
    # Получаем параметр сортировки из URL
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')

    # Определяем порядок сортировки
    order = getattr(Graduate, sort_by)
    if sort_order == 'desc':
        order = order.desc()

    graduates = Graduate.query.order_by(order).all()
    return render_template('index.html', graduates=graduates, sort_by=sort_by, sort_order=sort_order)


# Страница добавления выпускника
@app.route('/add', methods=['GET', 'POST'])
def add():
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
            return redirect(url_for('index'))
        except Exception as e:
            return render_template('add.html', error=str(e))
    return render_template('add.html')


# Страница "О проекте"
@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)