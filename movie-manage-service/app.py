from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager
from datetime import timedelta
import redis

# Configure token expiry duration
TOKEN_EXPIRATION = timedelta(minutes=15)

# Initialize Flask application
application = Flask(__name__)

# Database setup
application.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:password@movie-review-db:5432/moviedb'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config["JWT_SECRET_KEY"] = "highly-confidential"
application.config["JWT_ACCESS_TOKEN_EXPIRES"] = TOKEN_EXPIRATION

# Initialize database instance
database = SQLAlchemy(application)

# Initialize JWT
jwt_manager = JWTManager(application)

# Setup Redis connection
cache = redis.StrictRedis(host='redis', port=6379)

# Configure rate limiting
rate_limiter = Limiter(
    key_func=get_remote_address,
    app=application,
    default_limits=["", "", ""]
)

# Importing routes after app initialization
import routes

# Launch the server
if __name__ == "__main__":
    application.run(host='0.0.0.0', port=5001)
