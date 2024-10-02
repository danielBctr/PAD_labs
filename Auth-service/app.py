from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Set token expiration time
token_lifetime = timedelta(minutes=5)

def create_app():
    # Initialize Flask app
    app = Flask(__name__)

    # Configure app
    app_settings = {
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:password@login-database:5432/logindb',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': "super-secret",
        'JWT_ACCESS_TOKEN_EXPIRES': token_lifetime
    }
    app.config.update(app_settings)

    # Initialize JWT and Database
    JWTManager(app)
    db = SQLAlchemy(app)

    # Apply rate limits
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200/day", "50/hour", "5/minute"]
    )

    # Import routes
    with app.app_context():
        import routes

    return app

if __name__ == '__main__':
    # Create and run the app
    application = create_app()
    application.run(host='0.0.0.0', port=5000)
