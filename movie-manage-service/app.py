from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['CORS_ALLOWED_ORIGINS'] = "*"

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8
)

# Dummy database of existing movie IDs
existing_movie_ids = {'1', '2', '3'}

# Error handling decorator
def handle_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error in {func.__name__}: {str(e)}")
            emit('error', {'error': str(e)}, room=request.sid)
    return wrapper

# Handle WebSocket connection
@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")
    emit('connection_response', {'status': 'connected', 'sid': request.sid})

# Handle WebSocket disconnection
@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

# Handle sending a message to the lobby
@socketio.on('send_message')
@handle_error
def handle_send_message(data):
    data = json.loads(data) if isinstance(data, str) else data
    
    user_id = data.get('user_id')
    lobby_id = str(data.get('lobby_id'))
    message = data.get('message')

    if user_id and lobby_id and message:
        print(f"Received message from user {user_id} in lobby {lobby_id}: {message}")
        emit('receive_message', {
            'user_id': user_id,
            'message': message,
            'lobby_id': lobby_id
        }, room=lobby_id)
    else:
        error_message = "Failed to send message: Missing user ID, lobby ID, or message."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)

# Handle joining a lobby
@socketio.on('join_lobby')
@handle_error
def on_join_lobby(data):
    data = json.loads(data) if isinstance(data, str) else data

    user_id = data.get('user_id')
    lobby_id = str(data.get('lobby_id'))

    if user_id and lobby_id:
        join_room(lobby_id)
        message = f"User '{user_id}' joined lobby '{lobby_id}'."
        print(message)

        emit('lobby_response', {
            'status': 'joined',
            'user_id': user_id,
            'lobby_id': lobby_id,
            'message': message
        }, room=request.sid)

        emit('lobby_announcement', {
            'user_id': user_id,
            'lobby_id': lobby_id,
            'message': f"{user_id} has joined the lobby."
        }, room=lobby_id)
    else:
        error_message = "Failed to join lobby: Missing user ID or lobby ID."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)

# Handle leaving a lobby
@socketio.on('leave_lobby')
@handle_error
def on_leave_lobby(data):
    data = json.loads(data) if isinstance(data, str) else data

    user_id = data.get('user_id')
    lobby_id = str(data.get('lobby_id'))

    if user_id and lobby_id:
        leave_room(lobby_id)
        message = f"User '{user_id}' left lobby '{lobby_id}'."
        print(message)

        emit('lobby_response', {
            'status': 'left',
            'user_id': user_id,
            'lobby_id': lobby_id,
            'message': message
        }, room=request.sid)

        emit('lobby_announcement', {
            'user_id': user_id,
            'lobby_id': lobby_id,
            'message': f"{user_id} has left the lobby."
        }, room=lobby_id)
    else:
        error_message = "Failed to leave lobby: Missing user ID or lobby ID."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)

# Handle creating a movie
@socketio.on('create_movie')
@handle_error
def handle_create_movie(data):
    data = json.loads(data) if isinstance(data, str) else data

    user_id = data.get('user_id')
    movie_title = data.get('movie_title')
    movie_id = str(len(existing_movie_ids) + 1)

    if user_id and movie_title:
        existing_movie_ids.add(movie_id)
        message = f"User '{user_id}' added a new movie: '{movie_title}'."
        print(message)

        emit('movie_notification', {
            'type': 'new',
            'user_id': user_id,
            'movie_id': movie_id,
            'movie_title': movie_title,
            'message': message
        }, broadcast=True)
    else:
        error_message = "Failed to add new movie: Missing user ID or movie title."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)

# Handle updating a movie
@socketio.on('update_movie')
@handle_error
def handle_update_movie(data):
    data = json.loads(data) if isinstance(data, str) else data

    user_id = data.get('user_id')
    movie_id = str(data.get('movie_id'))
    movie_title = data.get('movie_title')

    if movie_id not in existing_movie_ids:
        error_message = f"Movie ID {movie_id} does not exist."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)
        return

    if all([user_id, movie_id, movie_title]):
        message = f"User '{user_id}' updated movie ID '{movie_id}' to '{movie_title}'."
        print(message)

        emit('movie_notification', {
            'type': 'update',
            'user_id': user_id,
            'movie_id': movie_id,
            'movie_title': movie_title,
            'message': message
        }, broadcast=True)
    else:
        error_message = "Failed to update movie: Missing user ID, movie ID, or movie title."
        print(error_message)
        emit('error', {'message': error_message}, room=request.sid)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True, allow_unsafe_werkzeug=True)
