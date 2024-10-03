from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from __main__ import application as app_instance, database as db_instance, rate_limiter as limiter
from sqlalchemy import text
import time

# Authentication Endpoints

@app_instance.route('/api/auth/login', methods=['POST'])
def user_login():
    payload = request.get_json()
    user_email = payload.get('email')
    user_password = payload.get('password')

    registered_user = User.query.filter_by(email=user_email).first()
    if registered_user and check_password_hash(registered_user.password, user_password):
        jwt_token = create_access_token(identity=registered_user.id)
        return jsonify({'message': 'Login successful', 'token': jwt_token, 'user': registered_user.username}), 200
    return jsonify({'message': 'Incorrect email or password'}), 401


@app_instance.route('/api/auth/register', methods=['POST'])
def user_registration():
    details = request.get_json()
    username = details.get('username')
    email = details.get('email')
    password = details.get('password')
    confirm_password = details.get('confirm_password')

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already taken'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already in use'}), 400

    password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    new_account = User(username=username, email=email, password=password_hash)
    db_instance.session.add(new_account)
    db_instance.session.commit()

    return jsonify({'message': 'User successfully registered'}), 201


@app_instance.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def user_logout():
    return jsonify({'message': 'User logged out'}), 200


@app_instance.route('/api/auth/status', methods=['GET'])
def check_status():
    try:
        db_instance.session.execute(text('SELECT 1'))
        return jsonify({'status': 'OK', 'database': 'Connected'}), 200
    except Exception as e:
        return jsonify({'status': 'ERROR', 'database': 'Disconnected', 'error': str(e)}), 500


@app_instance.route('/api/auth/timeout', methods=['GET'])
def simulate_timeout():
    time.sleep(10)
    return jsonify({'message': 'Operation completed after timeout'}), 200


# User Management Endpoints

@app_instance.route('/api/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_details(user_id):
    selected_user = User.query.get(user_id)
    if selected_user:
        return jsonify({'id': selected_user.id, 'username': selected_user.username, 'email': selected_user.email}), 200
    return jsonify({'message': 'User not found'}), 404


@app_instance.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_info(user_id):
    payload = request.get_json()
    user_to_update = User.query.get(user_id)

    if not user_to_update:
        return jsonify({'message': 'User not found'}), 404

    new_username = payload.get('username')
    new_email = payload.get('email')
    new_password = payload.get('password')
    old_password = payload.get('old_password')

    if new_username and new_username != user_to_update.username:
        if User.query.filter_by(username=new_username).first():
            return jsonify({'message': 'Username already in use'}), 400
        user_to_update.username = new_username

    if new_email and new_email != user_to_update.email:
        if User.query.filter_by(email=new_email).first():
            return jsonify({'message': 'Email already in use'}), 400
        user_to_update.email = new_email

    if new_password:
        if not old_password or not check_password_hash(user_to_update.password, old_password):
            return jsonify({'message': 'Old password is incorrect'}), 400
        user_to_update.password = generate_password_hash(new_password, method='pbkdf2:sha256')

    db_instance.session.commit()
    return jsonify({'message': 'User information updated successfully'}), 200


@app_instance.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user_account(user_id):
    user_to_delete = User.query.get(user_id)
    if not user_to_delete:
        return jsonify({'message': 'User not found'}), 404

    db_instance.session.delete(user_to_delete)
    db_instance.session.commit()
    return jsonify({'message': 'User account deleted successfully'}), 200
