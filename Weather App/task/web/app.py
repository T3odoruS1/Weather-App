
import requests
import json

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import *
from sqlalchemy import func


app = Flask(__name__)
app.config['SECRET_KEY'] = 'So-Seckrekt'


# Database init

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)
SQLALCHEMY_TRACK_MODIFICATIONS = False
api_key = "your_api_code"


def get_coords_from_city_name(city_name: str) -> tuple:
    city_name = city_name.replace(" ", "-")
    req = requests.\
        get(f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={api_key}")
    req = json.loads(req.text)[0]
    lat = req['lat']
    lon = req['lon']
    coords = (lat, lon)
    return coords


def get_weather_data(coords: tuple) -> dict:
    req = requests.\
        get(f"https://api.openweathermap.org/data/2.5/weather?lat={coords[0]}&lon={coords[1]}&appid={api_key}&units"
            f"=metric")
    req = json.loads(req.text)
    return req


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
        return '<Name %r>' % self.name


def get_data_from_database():
    cities = City.query.all()
    weather = []
    for city in cities:
        city_weather = get_weather_data(get_coords_from_city_name(city.name))
        city_weather['main']['temp'] = int(round(city_weather['main']['temp']))
        weather.append(city_weather)
    return weather


@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        city_data = request.form['city_name']  # City name
        try:
            weather_data = get_weather_data(get_coords_from_city_name(city_data))
        except IndexError:
            flash("The city doesn't exist!", "error")
            weather = get_data_from_database()  # Json list
            return render_template('index.html', weather_data=weather)

        city_data = weather_data['name']
        exists = bool(City.query.filter(func.lower(City.name) == func.lower(city_data)).first())
        if not exists:
            city_name = get_weather_data(get_coords_from_city_name(city_data))['name']
            db.session.add(City(id=None, name=city_name))
            db.session.commit()  # Adding the city name to the database
        if exists:
            flash('The city has already been added to the list!', 'info')
        weather = get_data_from_database()  # Json list
        return render_template('index.html', weather_data=weather)
    weather = get_data_from_database()
    return render_template('index.html', weather_data=weather)


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter(func.lower(City.name) == func.lower(city_id)).first()
    db.session.delete(city)
    db.session.commit()
    return redirect('/')


if __name__ == '__main__':
    db.create_all()
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
