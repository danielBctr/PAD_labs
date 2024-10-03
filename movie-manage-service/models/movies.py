from flask_sqlalchemy import SQLAlchemy
from __main__ import db

class Movie(db.Model):
    __tablename__ = 'movies'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    release_date = db.Column(db.Date, nullable=False)
    rating = db.Column(db.Float, nullable=True)  # Set to nullable=True initially
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Adding CheckConstraint directly
    __table_args__ = (
        db.CheckConstraint('rating >= 0 AND rating <= 10', name='check_rating'),
    )

    # Relationship to reviews
    reviews = db.relationship('Review', backref='movie', lazy=True)
    
    # Relationship to genres through the junction table
    genres = db.relationship('Genre', secondary='movie_genres', backref=db.backref('movies', lazy='dynamic'))

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)  # Set to nullable=True initially

    # Adding CheckConstraint directly
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 10', name='check_review_rating'),
    )

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
