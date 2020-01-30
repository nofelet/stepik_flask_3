from flask import Flask, render_template, request

from flask_sqlalchemy import SQLAlchemy

import json

with open('goals.json', encoding='utf-8') as g:
    all_goals = json.load(g)

with open('teachers.json', encoding='utf-8') as t:
    teachers = json.load(t)

links = [{'title': 'Все репетиторы', 'link': '/'}, {'title': 'Заявка на подбор', 'link': '/request'}]
days = {'mo': 'Понедельник', 'tu': 'Вторник', 'we': 'Среда', 'th': 'Четверг', 'fr': 'Пятница'}

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tinysteps.db'
db = SQLAlchemy(app)

class Goal(db.Model):
    __tablename__ = 'goals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    teachers = db.relationship('Teacher',
                               secondary=teachers_goals_association,
                               back_populates='goals')

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primery_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    goals = db.relationship('Goal',
                            secondary=teachers_goals_association,
                            back_populates='teachers')
    free = db.Column(db.String, nullable=False)
    bookings = db.relationship('Booking',
                               db.ForeignKey('bookings.id'),
                               back_populates='teacher_id')

teachers_goals_association = db.Table('teacher_has_goal',
                                      db.Column('teacher_id', db.Integer, db.ForeignKey('teachers.id')),
                                      db.Column('goal_id', db.Integer, db.ForeignKey('goals.id')))

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.relationship('teachers',
                                 db.ForeignKey('teachers.id'),
                                 back_populates='bookings')
    day = db.Column(db.String)
    time = db.Column(db.Time)
    name = db.Column(db.String)
    phone = db.Column(db.String)

class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.Integer, db.ForeingKey('goals.id'))
    time = db.Column(db.String)
    name = db.Column(db.String)
    phone = db.Column(db.String)


@app.route('/')
def main():
    output = render_template('index.html',
                             links=links,
                             teachers=teachers,
                             teacher_ids=[])
    return output


@app.route('/goals/<goal>/')
def goals(goal):
    goal_ru = all_goals[goal].lower()
    teachers_with_goal = []
    for teacher_id in teachers:
        if goal in teachers[teacher_id]['goals']:
            teachers_with_goal.append(teacher_id)
    teachers_with_goal.sort(key=lambda teacher_id: teachers[teacher_id]['rating'], reverse=True)

    output = render_template('goal.html',
                             links=links,
                             teachers_with_goal=teachers_with_goal,
                             teachers=teachers,
                             goal=goal,
                             goal_ru=goal_ru)
    return output

@app.route('/profiles/<id>/')
def profiles(id):
    output = render_template('profile.html',
                             links=links,
                             goals=all_goals,
                             teacher=teachers[id],
                             id=id)
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
    app.run()
