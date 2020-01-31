from flask import Flask, render_template, request

from flask_sqlalchemy import SQLAlchemy

import json

with open('goals.json', encoding='utf-8') as g:
    all_goals = json.load(g)

with open('teachers.json', encoding='utf-8') as t:
    teachers = json.load(t)

links = [{'title': 'Все репетиторы', 'link': '/'}, {'title': 'Заявка на подбор', 'link': '/request'}]
days = {'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда', 'thu': 'Четверг', 'fri': 'Пятница'}
times = {'8': '8:00', '10': '10:00', '12': '12:00', '14': '14:00', '16': '16:00'}


app = Flask(__name__)

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

class Days(db.Model):
    ___tablename__ = 'db_days'
    id = db.Column(db.Integer, primary_key=True)
    day_en = db.Column(db.String, unique=True, nullable=False)
    day_ru = db.Column(db.String, unique=True, nullable=False)

class Booking(db.Model):
    __tablename__ = 'db_bookings'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('db_teachers.id'))
    teacher = db.relationship('Teacher', back_populates='bookings')
    day = db.Column(db.String)
    time = db.Column(db.Time)
    name = db.Column(db.String)
    phone = db.Column(db.String)


class Request(db.Model):
    __tablename__ = 'db_requests'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.Integer, db.ForeignKey('db_goals.id'))
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


# Routes section
@app.route('/')
def main():
    output = render_template('index.html',
                             links=links,
                             teachers=teachers,
                             teacher_ids=[])
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
    output = render_template('pick.html',
                             links=links)
    return output

@app.route('/booking/<id>/<day>/<time>')
def booking(id, day, time):
    with open ('request.json', 'w', encoding='utf-8') as r:
        json.dump({'day': days[day], 'time': time+':00'}, r)
    output = render_template('booking.html',
                             links=links,
                             teacher=teachers[id],
                             days=days,
                             id=id,
                             day=day,
                             time=time)
    return output

@app.route('/message/<id>')
def message(id):
    output = render_template('message.html',
                             links=links,
                             id=id,
                             teachers=teachers)
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
    app.run(debug=True)
