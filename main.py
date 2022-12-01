from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import requests

MOVIE_DB_API_KEY = "15dbf7c1ea7d5e10a167bde4b158b679"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

class RateMovieForm(FlaskForm):
    rating = StringField(label="Your Rating out of 10 e.g. 7.5")
    review = TextAreaField(label="Your Review")
    submit = SubmitField(label="Done")

class AddMovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
db.init_app(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, unique=True, nullable=True)
    review = db.Column(db.String, unique=True, nullable=True)
    img_url = db.Column(db.String, unique=True, nullable=False)

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    movies = db.session.execute(db.select(Movie).order_by(Movie.rating)).scalars().all()

    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    #db.session.commit()

    return render_template("index.html", movies=movies)


@app.route("/edit", methods=["GET","POST"])
def edit():
    edit_movie_form = RateMovieForm()

    if edit_movie_form.validate_on_submit():
        movie_id = request.args.get('id')
        selected_movie = db.get_or_404(Movie, movie_id)
        if edit_movie_form.rating.data != "":
            selected_movie.rating = edit_movie_form.rating.data
            db.session.commit()
        if edit_movie_form.review.data != "":
            selected_movie.review = edit_movie_form.review.data
            db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=edit_movie_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    selected_movie = db.get_or_404(Movie, movie_id)
    db.session.delete(selected_movie)
    db.session.commit()

    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddMovieForm()

    if add_form.validate_on_submit():
        title = add_form.title.data
        parameters = {
            "api_key": MOVIE_DB_API_KEY,
            "query": title,
        }
        response = requests.get(url="https://api.themoviedb.org/3/search/movie", params=parameters)
        movie_data = response.json()["results"]

        return render_template('select.html', data=movie_data)

    return render_template('add.html', form=add_form)


@app.route("/find")
def movie_details():
    api_id = request.args.get('id')
    parameters = {
        "api_key": MOVIE_DB_API_KEY,
    }
    response = requests.get(url=f"https://api.themoviedb.org/3/movie/{api_id}", params=parameters)
    data = response.json()
    
    new_movie = Movie(
        title=data["original_title"],
        year=data["release_date"].split("-")[0],
        description=data["overview"],
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}"
        )

    db.session.add(new_movie)
    db.session.commit()

    movie = db.session.execute(db.select(Movie).filter_by(title=data["original_title"])).one()
    movie_id = movie[0].id

    return redirect(url_for('edit', id=movie_id))


if __name__ == '__main__':
    app.run(debug=True)
