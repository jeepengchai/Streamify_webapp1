# movie_webapp/models.py
# No need to import login_manager or define load_user here anymore
from . import db # Import db from the initialized instance in __init__.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# The load_user function and @login_manager.user_loader decorator have been moved to __init__.py

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # For NCF later
    interactions = db.relationship('Rating', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Include Movie and Rating models
class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True) # This TMDB ID is crucial for matching
    title = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(255)) # Example
    # Add other info if needed

    interactions = db.relationship('Rating', backref='movie', lazy=True)

    def __repr__(self):
        return f'<Movie {self.title} (ID: {self.id})>'

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False) # This is the Movie.id (TMDB ID)
    rating = db.Column(db.Float, nullable=False) # Could be 0.0 for implicit, or 0-5 for explicit
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False) # Added timestamp

    __table_args__ = (db.UniqueConstraint('user_id', 'movie_id', name='_user_movie_uc'),)

    def __repr__(self):
        return f'<Rating User {self.user_id} Movie {self.movie_id} Value {self.rating} Time {self.timestamp}>'