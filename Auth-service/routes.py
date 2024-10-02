from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from __main__ import app, db, limiter
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from sqlalchemy import text
import time


# User Authentication Routes

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify({'message': 'Login successful', 'access_token': access_token, 'user': user.username}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401


@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists'}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'User logged out'}), 200


@app.route('/api/auth/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200


@app.route('/api/auth/status', methods=['GET'])
def status():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'OK', 'database': 'Connected'}), 200
    except Exception as e:
        return jsonify({'status': 'ERROR', 'database': 'Not connected', 'error': str(e)}), 500


@app.route('/api/auth/timeout', methods=['GET'])
def timeout():
    time.sleep(10)
    return jsonify({'message': 'Timeout complete'}), 200


# User Management Routes

@app.route('/api/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    user = User.query.get(id)
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'email': user.email}), 200
    else:
        return jsonify({'message': 'User not found'}), 404


@app.route('/api/users/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    data = request.get_json()
    user = User.query.get(id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Check if new username is unique
    if data.get('username') and data.get('username') != user.username:
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'message': 'Username already taken'}), 400
        user.username = data.get('username')

    # Check if new email is unique
    if data.get('email') and data.get('email') != user.email:
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'message': 'Email already taken'}), 400
        user.email = data.get('email')

    # Verify old password before updating to new one
    new_password = data.get('password')
    if new_password:
        old_password = data.get('old_password')
        if not old_password or not check_password_hash(user.password, old_password):
            return jsonify({'message': 'Old password is incorrect'}), 400
        else:
            user.password = generate_password_hash(new_password, method='pbkdf2:sha256')

    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200


@app.route('/api/users/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'}), 200
