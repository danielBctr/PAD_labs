from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from __main__ import app, db, limiter, redis_client
from models.movies import Movies
from models.movies import Reviews
from sqlalchemy import text
import requests
import json

LOGIN_SERVICE_URL = 'http://login-service:5000/api/'

# Movie routes

@app.route('/api/movies/<int:id>', methods=['GET'])
def get_movie(id):
    movie = Movies.query.get(id)
    if movie:
        return jsonify({
            'id': movie.id,
            'title': movie.title,
            'description': movie.description,
            'release_date': movie.release_date.isoformat(),
            'genre': movie.genre,
            'director': movie.director,
            'poster_url': movie.poster_url,
            'average_rating': movie.average_rating
        })
    else:
        return jsonify({'message': 'Movie not found'}), 404

@app.route('/api/movies/', methods=['GET'])
def get_all_movies():
    movies = Movies.query.all()
    return jsonify([{
        'id': movie.id,
        'title': movie.title,
        'description': movie.description,
        'release_date': movie.release_date.isoformat(),
        'genre': movie.genre,
        'director': movie.director,
        'poster_url': movie.poster_url,
        'average_rating': movie.average_rating
    } for movie in movies])

@app.route('/api/movies/popular', methods=['GET'])
def get_popular_movies():
    cache_key = 'popular_movies'

    cached_results = redis_client.get(cache_key)
    if cached_results:
        return jsonify(message='Results retrieved from cache', data=json.loads(cached_results))

    movies = Movies.query.order_by(Movies.average_rating.desc()).limit(10).all()

    response_data = [{
        'id': movie.id,
        'title': movie.title,
        'description': movie.description,
        'release_date': movie.release_date.isoformat(),
        'genre': movie.genre,
        'director': movie.director,
        'poster_url': movie.poster_url,
        'average_rating': movie.average_rating
    } for movie in movies]

    redis_client.set(cache_key, json.dumps(response_data), ex=300)

    return jsonify(response_data)

@app.route('/api/movies/search', methods=['GET'])
def search_movies():
    title = request.args.get('title')
    genre = request.args.get('genre')
    director = request.args.get('director')
    min_rating = request.args.get('min_rating')

    cache_key = f"search:movies:title={title}&genre={genre}&director={director}&min_rating={min_rating}"

    cached_results = redis_client.get(cache_key)
    if cached_results:
        return jsonify(message='Results retrieved from cache', data=json.loads(cached_results))

    query = Movies.query

    if title:
        query = query.filter(Movies.title.ilike(f'%{title}%'))
    if genre:
        query = query.filter(Movies.genre.ilike(f'%{genre}%'))
    if director:
        query = query.filter(Movies.director.ilike(f'%{director}%'))
    if min_rating:
        try:
            query = query.filter(Movies.average_rating >= float(min_rating))
        except ValueError:
            return jsonify({'message': 'Invalid min_rating format'}), 400

    movies = query.all()

    response_data = [{
        'id': movie.id,
        'title': movie.title,
        'description': movie.description,
        'release_date': movie.release_date.isoformat(),
        'genre': movie.genre,
        'director': movie.director,
        'poster_url': movie.poster_url,
        'average_rating': movie.average_rating
    } for movie in movies]

    redis_client.set(cache_key, json.dumps(response_data), ex=300)

    return jsonify(response_data)

@app.route('/api/movies/', methods=['POST'])
@jwt_required()
def post_movie():
    data = request.get_json()
    
    required_fields = ['title', 'description', 'release_date', 'genre', 'director', 'poster_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'Missing required field: {field}'}), 400

    new_movie = Movies(
        title=data.get('title'),
        description=data.get('description'),
        release_date=data.get('release_date'),
        genre=data.get('genre'),
        director=data.get('director'),
        poster_url=data.get('poster_url'),
        average_rating=0
    )
    db.session.add(new_movie)
    db.session.commit()

    redis_client.delete('popular_movies')

    search_pattern = 'search:movies:*'
    for key in redis_client.scan_iter(search_pattern):
        redis_client.delete(key)

    return jsonify({'message': 'Movie created', 'id': new_movie.id}), 201

@app.route('/api/movies/<int:id>', methods=['PUT'])
@jwt_required()
def update_movie(id):
    movie = Movies.query.get(id)
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404

    data = request.get_json()

    if 'title' in data:
        movie.title = data['title']
    if 'description' in data:
        movie.description = data['description']
    if 'release_date' in data:
        movie.release_date = data['release_date']
    if 'genre' in data:
        movie.genre = data['genre']
    if 'director' in data:
        movie.director = data['director']
    if 'poster_url' in data:
        movie.poster_url = data['poster_url']

    db.session.commit()

    redis_client.delete('popular_movies')

    search_pattern = 'search:movies:*'
    for key in redis_client.scan_iter(search_pattern):
        redis_client.delete(key)

    return jsonify({'message': 'Movie updated successfully'}), 200

@app.route('/api/movies/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_movie(id):
    movie = Movies.query.get(id)
    if not movie:
        return jsonify({'message': 'Movie not found'}), 404

    db.session.delete(movie)
    db.session.commit()

    redis_client.delete('popular_movies')

    search_pattern = 'search:movies:*'
    for key in redis_client.scan_iter(search_pattern):
        redis_client.delete(key)

    return jsonify({'message': 'Movie deleted successfully'}), 200

# Review routes

@app.route('/api/reviews/<int:id>', methods=['GET'])
def get_review(id):
    review = Reviews.query.get(id)
    if review:
        return jsonify({
            'id': review.id,
            'movie_id': review.movie_id,
            'user_id': review.user_id,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.isoformat()
        })
    else:
        return jsonify({'message': 'Review not found'}), 404

@app.route('/api/movies/<int:movie_id>/reviews', methods=['GET'])
def get_movie_reviews(movie_id):
    reviews = Reviews.query.filter_by(movie_id=movie_id).all()
    return jsonify([{
        'id': review.id,
        'movie_id': review.movie_id,
        'user_id': review.user_id,
        'rating': review.rating,
        'comment': review.comment,
        'created_at': review.created_at.isoformat()
    } for review in reviews])

@app.route('/api/reviews/', methods=['POST'])
@jwt_required()
def post_review():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    # Check if the user exists
    headers = {
        'Authorization': f'{request.headers.get("Authorization")}'
    }
    user_response = requests.get(f'{LOGIN_SERVICE_URL}/users/{user_id}', headers=headers)
    
    if user_response.status_code != 200:
        return jsonify({'message': 'User not found or unauthorized'}), 401
    
    required_fields = ['movie_id', 'rating', 'comment']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'Missing required field: {field}'}), 400

    try:
        rating = float(data.get('rating'))
        if rating < 0 or rating > 5:
            return jsonify({'message': 'Rating must be between 0 and 5'}), 400
    except ValueError:
        return jsonify({'message': 'Rating must be a number'}), 400

    new_review = Reviews(
        movie_id=data.get('movie_id'),
        user_id=user_id,
        rating=rating,
        comment=data.get('comment')
    )
    db.session.add(new_review)
    db.session.commit()

    # Update movie's average rating
    movie = Movies.query.get(data.get('movie_id'))
    if movie:
        reviews = Reviews.query.filter_by(movie_id=movie.id).all()
        movie.average_rating = sum(review.rating for review in reviews) / len(reviews)
        db.session.commit()

    redis_client.delete('popular_movies')

    return jsonify({'message': 'Review created', 'id': new_review.id}), 201

@app.route('/api/reviews/<int:id>', methods=['PUT'])
@jwt_required()
def update_review(id):
    review = Reviews.query.get(id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    if review.user_id != get_jwt_identity():
        return jsonify({'message': 'Unauthorized to update this review'}), 403

    data = request.get_json()

    if 'rating' in data:
        try:
            rating = float(data['rating'])
            if rating < 0 or rating > 5:
                return jsonify({'message': 'Rating must be between 0 and 5'}), 400
            review.rating = rating
        except ValueError:
            return jsonify({'message': 'Rating must be a number'}), 400
    if 'comment' in data:
        review.comment = data['comment']

    db.session.commit()

    # Update movie's average rating
    movie = Movies.query.get(review.movie_id)
    if movie:
        reviews = Reviews.query.filter_by(movie_id=movie.id).all()
        movie.average_rating = sum(review.rating for review in reviews) / len(reviews)
        db.session.commit()

    redis_client.delete('popular_movies')

    return jsonify({'message': 'Review updated successfully'}), 200

@app.route('/api/reviews/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_review(id):
    review = Reviews.query.get(id)
    if not review:
        return jsonify({'message': 'Review not found'}), 404

    if review.user_id != get_jwt_identity():
        return jsonify({'message': 'Unauthorized to delete this review'}), 403

    movie_id = review.movie_id
    db.session.delete(review)
    db.session.commit()

    # Update movie's average rating
    movie = Movies.query.get(movie_id)
    if movie:
        reviews = Reviews.query.filter_by(movie_id=movie.id).all()
        if reviews:
            movie.average_rating = sum(review.rating for review in reviews) / len(reviews)
        else:
            movie.average_rating = 0
        db.session.commit()

    redis_client.delete('popular_movies')

    return jsonify({'message': 'Review deleted successfully'}), 200

# User profile routes

@app.route('/api/movies/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    
    headers = {
        'Authorization': f'{request.headers.get("Authorization")}'
    }
    
    # Send a GET request to the login service to fetch the user profile
    profile_response = requests.get(f'{LOGIN_SERVICE_URL}/users/{user_id}', headers=headers)
    
    if profile_response.status_code != 200:
        return jsonify({'message': profile_response.json().get('message', 'Error occurred')}), profile_response.status_code
    
    return jsonify(profile_response.json()), 200

@app.route('/api/movies/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()

    headers = {
        'Authorization': f'{request.headers.get("Authorization")}'
    }

    # Send a PUT request to the login service to update the user profile
    update_response = requests.put(f'{LOGIN_SERVICE_URL}/users/{user_id}', json=data, headers=headers)
    
    if update_response.status_code != 200:
        return jsonify({'message': update_response.json().get('message', 'Error occurred')}), update_response.status_code
    
    if data.get('password'):
        return jsonify({'message': 'Password updated successfully. Please log-in again'}), 200
    else:
        return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/api/movies/cache/clear', methods=['DELETE'])
def clear_all_cache():
    redis_client.flushall()
    return jsonify({'message': 'All cache cleared successfully'}), 200
