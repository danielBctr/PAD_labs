from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models.users import User
from __main__ import application as app_instance, database as db_instance, rate_limiter as limiter
from sqlalchemy import text
import time
import uuid

class TransactionManager:
    def __init__(self):
        self.transactions = {}
    
    def create_transaction(self, operation, data):
        transaction_id = str(uuid.uuid4())
        self.transactions[transaction_id] = {
            'id': transaction_id,
            'operation': operation,
            'data': data,
            'status': 'PENDING',
            'prepared_data': None,
            'created_at': time.time(),
            'logs': []
        }
        return transaction_id
    
    def prepare_transaction(self, transaction_id):
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        # Validate data based on operation
        if transaction['operation'] == 'register':
            # Perform pre-commit checks for registration
            username = transaction['data'].get('username')
            email = transaction['data'].get('email')
            
            if User.query.filter_by(username=username).first():
                return False, 'Username already taken'
            
            if User.query.filter_by(email=email).first():
                return False, 'Email already in use'
            
            # Store prepared data
            transaction['prepared_data'] = {
                'username': username,
                'email': email,
                'password_hash': generate_password_hash(
                    transaction['data'].get('password'), 
                    method='pbkdf2:sha256'
                )
            }
        
        elif transaction['operation'] == 'update':
            user_id = transaction['data'].get('user_id')
            user_to_update = User.query.get(user_id)
            
            if not user_to_update:
                return False, 'User not found'
            
            # Validate new data
            new_username = transaction['data'].get('username')
            new_email = transaction['data'].get('email')
            new_password = transaction['data'].get('password')
            
            if new_username and User.query.filter_by(username=new_username).first():
                return False, 'Username already in use'
            
            if new_email and User.query.filter_by(email=new_email).first():
                return False, 'Email already in use'
            
            # Store prepared update data
            transaction['prepared_data'] = {
                'user': user_to_update,
                'new_username': new_username,
                'new_email': new_email,
                'new_password_hash': generate_password_hash(new_password, method='pbkdf2:sha256') if new_password else None
            }
        
        elif transaction['operation'] == 'delete':
            user_id = transaction['data'].get('user_id')
            user_to_delete = User.query.get(user_id)
            
            if not user_to_delete:
                return False, 'User not found'
            
            transaction['prepared_data'] = {
                'user': user_to_delete
            }
        
        else:
            return False, 'Unsupported operation'
        
        transaction['status'] = 'PREPARED'
        transaction['logs'].append(f'Prepared at {time.time()}')
        return True, 'Ready to commit'
    
    def commit_transaction(self, transaction_id):
        transaction = self.transactions.get(transaction_id)
        if not transaction or transaction['status'] != 'PREPARED':
            raise ValueError('Transaction not in prepared state')
        
        try:
            if transaction['operation'] == 'register':
                # Commit new user registration
                prepared_data = transaction['prepared_data']
                new_account = User(
                    username=prepared_data['username'], 
                    email=prepared_data['email'], 
                    password=prepared_data['password_hash']
                )
                db_instance.session.add(new_account)
            
            elif transaction['operation'] == 'update':
                # Commit user update
                prepared_data = transaction['prepared_data']
                user = prepared_data['user']
                
                if prepared_data['new_username']:
                    user.username = prepared_data['new_username']
                if prepared_data['new_email']:
                    user.email = prepared_data['new_email']
                if prepared_data['new_password_hash']:
                    user.password = prepared_data['new_password_hash']
            
            elif transaction['operation'] == 'delete':
                # Commit user deletion
                user_to_delete = transaction['prepared_data']['user']
                db_instance.session.delete(user_to_delete)
            
            db_instance.session.commit()
            transaction['status'] = 'COMMITTED'
            transaction['logs'].append(f'Committed at {time.time()}')
            return True, 'Transaction committed successfully'
        
        except Exception as e:
            transaction['status'] = 'FAILED'
            transaction['logs'].append(f'Commit failed: {str(e)}')
            db_instance.session.rollback()
            return False, str(e)
    
    def abort_transaction(self, transaction_id):
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        transaction['status'] = 'ABORTED'
        transaction['logs'].append(f'Aborted at {time.time()}')
        return True, 'Transaction aborted'
    
    def get_transaction_status(self, transaction_id):
        transaction = self.transactions.get(transaction_id)
        if not transaction:
            raise ValueError('Transaction not found')
        
        return {
            'id': transaction['id'],
            'operation': transaction['operation'],
            'status': transaction['status'],
            'logs': transaction['logs'],
            'created_at': transaction['created_at']
        }

# Initialize Transaction Manager
transaction_manager = TransactionManager()

# Two-Phase Commit Transaction Endpoints
@app_instance.route('/api/transactions/register', methods=['POST'])
def initiate_registration_transaction():
    details = request.get_json()
    
    # Validate input
    username = details.get('username')
    email = details.get('email')
    password = details.get('password')
    confirm_password = details.get('confirm_password')
    
    if not all([username, email, password, confirm_password]):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400
    
    # Create transaction
    transaction_id = transaction_manager.create_transaction('register', details)
    
    return jsonify({
        'message': 'Registration transaction initiated',
        'transaction_id': transaction_id
    }), 201

@app_instance.route('/api/transactions/prepare', methods=['POST'])
def prepare_transaction():
    transaction_id = request.json.get('transaction_id')
    
    if not transaction_id:
        return jsonify({'message': 'Transaction ID required'}), 400
    
    try:
        success, message = transaction_manager.prepare_transaction(transaction_id)
        return jsonify({
            'transaction_id': transaction_id,
            'prepared': success,
            'message': message
        }), 200 if success else 400
    
    except ValueError as e:
        return jsonify({
            'message': str(e)
        }), 404

@app_instance.route('/api/transactions/commit', methods=['POST'])
def commit_transaction():
    transaction_id = request.json.get('transaction_id')
    
    if not transaction_id:
        return jsonify({'message': 'Transaction ID required'}), 400
    
    try:
        success, message = transaction_manager.commit_transaction(transaction_id)
        return jsonify({
            'transaction_id': transaction_id,
            'committed': success,
            'message': message
        }), 200 if success else 400
    
    except ValueError as e:
        return jsonify({
            'message': str(e)
        }), 404

@app_instance.route('/api/transactions/abort', methods=['POST'])
def abort_transaction():
    transaction_id = request.json.get('transaction_id')
    
    if not transaction_id:
        return jsonify({'message': 'Transaction ID required'}), 400
    
    try:
        success, message = transaction_manager.abort_transaction(transaction_id)
        return jsonify({
            'transaction_id': transaction_id,
            'aborted': success,
            'message': message
        }), 200
    
    except ValueError as e:
        return jsonify({
            'message': str(e)
        }), 404

@app_instance.route('/api/transactions/<transaction_id>/status', methods=['GET'])
def get_transaction_status(transaction_id):
    try:
        status = transaction_manager.get_transaction_status(transaction_id)
        return jsonify(status), 200
    except ValueError as e:
        return jsonify({
            'message': str(e)
        }), 404

# Existing Authentication Endpoints (slightly modified)
@app_instance.route('/api/auth/register', methods=['POST'])
def user_registration():
    details = request.get_json()
    username = details.get('username')
    email = details.get('email')
    password = details.get('password')
    confirm_password = details.get('confirm_password')

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    # Create a transaction for registration
    transaction_id = transaction_manager.create_transaction('register', details)
    
    # Automatically prepare and commit if not in distributed transaction context
    success_prepare, prepare_msg = transaction_manager.prepare_transaction(transaction_id)
    if not success_prepare:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': prepare_msg}), 400
    
    success_commit, commit_msg = transaction_manager.commit_transaction(transaction_id)
    if not success_commit:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': commit_msg}), 400

    return jsonify({'message': 'User successfully registered', 'transaction_id': transaction_id}), 201

@app_instance.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_info(user_id):
    payload = request.get_json()
    payload['user_id'] = user_id

    # Create a transaction for update
    transaction_id = transaction_manager.create_transaction('update', payload)
    
    # Prepare the transaction
    success_prepare, prepare_msg = transaction_manager.prepare_transaction(transaction_id)
    if not success_prepare:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': prepare_msg}), 400
    
    # Commit the transaction
    success_commit, commit_msg = transaction_manager.commit_transaction(transaction_id)
    if not success_commit:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': commit_msg}), 400

    return jsonify({
        'message': 'User information updated successfully', 
        'transaction_id': transaction_id
    }), 200

@app_instance.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user_account(user_id):
    # Create a transaction for deletion
    transaction_id = transaction_manager.create_transaction('delete', {'user_id': user_id})
    
    # Prepare the transaction
    success_prepare, prepare_msg = transaction_manager.prepare_transaction(transaction_id)
    if not success_prepare:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': prepare_msg}), 400
    
    # Commit the transaction
    success_commit, commit_msg = transaction_manager.commit_transaction(transaction_id)
    if not success_commit:
        transaction_manager.abort_transaction(transaction_id)
        return jsonify({'message': commit_msg}), 400

    return jsonify({
        'message': 'User account deleted successfully', 
        'transaction_id': transaction_id
    }), 200
