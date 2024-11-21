from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from datetime import timedelta
from prometheus_flask_exporter import PrometheusMetrics

# Define token lifespan
TOKEN_VALIDITY = timedelta(minutes=5)

def initialize_app():
    # Create the Flask instance
    application = Flask(__name__)
    metrics = PrometheusMetrics(application)

    # Configure settings for the app
    config_values = {
        'SQLALCHEMY_DATABASE_URI': 'postgresql://admin:password@login-database:5432/logindb',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'JWT_SECRET_KEY': "top-secret-key",
        'JWT_ACCESS_TOKEN_EXPIRES': TOKEN_VALIDITY
    }
    application.config.update(config_values)

    # Set up JWT manager and SQLAlchemy database
    jwt_setup = JWTManager(application)
    database = SQLAlchemy(application)

    # Configure rate limiting
    rate_limiter = Limiter(
        key_func=get_remote_address,
        app=application,
        default_limits=[""]
    )

    # Load routes within the app context
    with application.app_context():
        import routes

    return application

if __name__ == "__main__":
    # Initialize and run the application
    app_instance = initialize_app()
    app_instance.run(host='0.0.0.0', port=5000)
