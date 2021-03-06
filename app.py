from flask import Flask, render_template, request

from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, validators

import json

from random import shuffle

with open('goals.json', encoding='utf-8') as g:
    all_goals = json.load(g)

with open('teachers.json', encoding='utf-8') as t:
    teachers = json.load(t)

links = [{'title': 'Все репетиторы', 'link': '/'}, {'title': 'Заявка на подбор', 'link': '/request'}]
days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда', 'thu': 'Четверг', 'fri': 'Пятница'}
times = {'8': '8:00', '10': '10:00', '12': '12:00', '14': '14:00', '16': '16:00'}


app = Flask(__name__)

app.secret_key = 'some-very-secret-key'

# Database section
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tinysteps.db'
db = SQLAlchemy(app)

# Database - Models
teachers_goals = db.Table('teachers_goals',
                                      db.Column('teacher_id', db.Integer, db.ForeignKey('db_teachers.id')),
                                      db.Column('goal_id', db.Integer, db.ForeignKey('db_goals.id')))


class Goal(db.Model):
    __tablename__ = 'db_goals'
    id = db.Column(db.Integer, primary_key=True)
    name_en = db.Column(db.String, nullable=False)
    name_ru = db.Column(db.String, nullable=False)
    teachers = db.relationship('Teacher',
                               secondary=teachers_goals,
                               back_populates='goals')

class Teacher(db.Model):
    __tablename__ = 'db_teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    goals = db.relationship('Goal',
                            secondary=teachers_goals,
                            back_populates='teachers')
    free = db.Column(db.String, nullable=False)
    bookings = db.relationship('Booking',
                               back_populates='teacher')

class Booking(db.Model):
    __tablename__ = 'db_bookings'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('db_teachers.id'))
    teacher = db.relationship('Teacher', back_populates='bookings')
    day = db.Column(db.String)
    time = db.Column(db.String)
    name = db.Column(db.String)
    phone = db.Column(db.String)

db.create_all()


# Database - Populating tables
for goal in all_goals:
    # without this check, "UNIQUE constraing failed" error comes out.
    if db.session.query(Goal).filter(Goal.name_en == goal).count() < 1:
        goal_for_db = Goal(name_en=goal, name_ru=all_goals[goal])
        db.session.add(goal_for_db)


for teacher in teachers:
    # without this check, "UNIQUE constraing failed" error comes out.
    if db.session.query(Teacher).filter(Teacher.id == int(teacher)).count() < 1:
        free = json.dumps(teachers[teacher]['free'])
        teacher_for_db = Teacher(id=int(teacher),
                                 name=teachers[teacher]['name'],
                                 about=teachers[teacher]['about'],
                                 rating=teachers[teacher]['rating'],
                                 price=teachers[teacher]['price'],
                                 free=free)
        db.session.add(teacher_for_db)
        for goal in teachers[teacher]['goals']:
            goal_for_db = db.session.query(Goal).filter(Goal.name_en == goal).first()
            teacher_for_db.goals.append(goal_for_db)



db.session.commit()


# Forms section
class BookingForm(FlaskForm):
    name = StringField('Вас зовут', validators=[validators.input_required()])
    phone = StringField('Ваш телефон', validators=[validators.input_required()])

class MessageForm(FlaskForm):
    name = StringField('Васс зовут', validators=[validators.input_required()])
    phone = StringField('Ваш телефон', validators=[validators.input_required()])
    message = StringField('сообщение', validators=[validators.input_required()])

class RequestForm(FlaskForm):
    goal = RadioField('Какая цель заниятий?', choices=[("travel", "Для путешествий"),
                                                       ("study", "Для учебы"),
                                                       ("work", "Для работы"),
                                                       ("relocate", "Для переезда")])
    duration = RadioField('Сколько времени есть?', choices=[("1-2", "1-2 часа в неделю"),
                                                            ("3-5", "3-5 часов в неделю"),
                                                            ("5-7", "5-7 часов в неделю"),
                                                            ("7-9", "7-9 часов в неделю")])
    name = StringField('Вас зовут', validators=[validators.input_required()])
    phone = StringField('Ваш телефон', validators=[validators.input_required()])

# Routes section
@app.route('/')
def main():
    all_goals = []
    teachers_for_index = []

    # Dictionaries are added to all_goals and all_teachers manually because .__dict__ is not working for some reason.
    # And, I could not access sqlalchemy model objects from templates, therefore lists and dictionaries.
    goals_from_db = db.session.query(Goal).all()
    for goal in goals_from_db:
        all_goals.append({'name_en': goal.name_en, 'name_ru': goal.name_ru})

    # Could not use func.random() from sqlalchemy, therefore shuffle() from python.
    teachers_from_db = db.session.query(Teacher).all()
    shuffle(teachers_from_db)
    six_random_teachers = teachers_from_db[:6]

    for teacher in six_random_teachers:
        teachers_for_index.append({'id': str(teacher.id),
                                   'name': teacher.name,
                                   'rating': teacher.rating,
                                   'price': teacher.price,
                                   'about': teacher.about})

    output = render_template('index.html',
                             links=links,
                             goals=all_goals,
                             teachers=teachers_for_index)
    return output


@app.route('/goals/<goal>/')
def goals(goal):
    goal_from_db = db.session.query(Goal).filter(Goal.name_en == goal).first()
    goal_ru_from_db = goal_from_db.name_ru.lower()
    # For some reason, db.in_() is not working, therefore filtering by goal in teacher.goals is done manually.
    teachers_with_goal = []
    all_teachers = db.session.query(Teacher).all()
    for this_teacher in all_teachers:
        if goal_from_db in this_teacher.goals:
            # .__dict__ is also not working, so dictionary is also done manually.
            teachers_with_goal.append({'id': str(this_teacher.id),
                                       'name': this_teacher.name,
                                       'rating': this_teacher.rating,
                                       'price': this_teacher.price,
                                       'about': this_teacher.about})
    output = render_template('goal.html',
                             links=links,
                             teachers_with_goal=teachers_with_goal,
                             goal=goal,
                             goal_ru=goal_ru_from_db)
    return output

@app.route('/profiles/<int:id>/')
def profiles(id):
    profile_goals = []
    teacher = db.session.query(Teacher).filter(Teacher.id == id).first()
    for goal in teacher.goals:
        profile_goals.append(goal.name_ru)
    # For some reason, json.dumps makes it Python dict string rather than JSON string.
    # Therefore, json.loads does not work (expects double quotes), but eval does.
    free = eval(teacher.free)

    output = render_template('profile.html',
                             links=links,
                             teacher=teacher,
                             id=str(teacher.id),
                             goals=profile_goals,
                             free=free,
                             days=days,
                             times=times)
    return output

@app.route('/search?s=aaaa')
def search():
    return 'Здесь будет поиск'

@app.route('/request')
def reqs():

    form = RequestForm()

    output = render_template('pick.html',
                             links=links,
                             form=form)
    return output

@app.route('/booking/<id>/<day>/<time>', methods=['GET'])
def booking(id, day, time):
    with open ('request.json', 'w', encoding='utf-8') as r:
        json.dump({'day': days[day], 'time': times[time]}, r)

    teacher_from_db = db.session.query(Teacher).filter(Teacher.id == int(id)).first()
    teacher_for_booking = {'id': id,
                           'name': teacher_from_db.name}

    form = BookingForm()

    output = render_template('booking.html',
                             links=links,
                             teacher=teacher_for_booking,
                             form=form,
                             day_ru=days[day],
                             time=times[time])
    return output

@app.route('/message/<id>')
def message(id):

    teacher_from_db = db.session.query(Teacher).filter(Teacher.id == int(id)).first()
    teacher_for_message = {'id': str(teacher_from_db.id),
                           'name': teacher_from_db.name}

    form = MessageForm()

    output = render_template('message.html',
                             links=links,
                             teacher=teacher_for_message,
                             form=form)
    return output

@app.route('/sent/', methods=['GET'])
def sent():
    name = request.args.get('name') # for some reason, request.form.get(item) and request.form[item] don't work.
    phone = request.args.get('phone')
    with open('request.json', encoding='utf-8') as r:
        jsonized_data = json.load(r)
    day = jsonized_data['day']
    time = jsonized_data['time']

    with open('request.json', 'w', encoding='utf-8') as r:
        json.dump({'day': day, 'time': time, 'name': name, 'phone': phone}, r)
    output = render_template('sent.html',
                             links=links,
                             name=name,
                             phone=phone,
                             day=day,
                             time=time)
    return output

if __name__ == '__main__':
    app.run()
