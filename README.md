# 🎬 Movie Review Platform
An online platform for users to review movies.


## Runnind and Deploying the project
This project is containerized with Docker for easy deployment and scaling. The architecture consists of multiple microservices including authentication, movie management, and real-time notifications via WebSocket.

### Prerequisites

- Docker (20.10.0 or higher)
- Docker Compose (2.0.0 or higher)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/movie-review-platform.git
cd movie-review-platform
```

### Step 2: Build and Run

Build and start all services using Docker Compose:

```bash
docker-compose up --build
```

To run in detached mode:
```bash
docker-compose up -d --build
```

### Service Health Checks

Verify the services are running properly:

- Authentication Service: `http://localhost:8000/api/auth/status`
- Movie Service: `http://localhost:8000/api/movies/status`
- WebSocket Server: `ws://localhost:8001`

### Container Management

List running containers:
```bash
docker ps
```

View service logs:
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs auth-service
docker-compose logs movie-service
```

Stop and remove containers:
```bash
docker-compose down
```

Remove containers and volumes:
```bash
docker-compose down -v
```

### Cache Management

Clear Redis cache:
```bash
docker-compose exec redis redis-cli FLUSHALL
```

### Scaling Services

Scale specific services:
```bash
docker-compose up -d --scale movie-service=3
```

### Production Deployment

For production deployment, use the production configuration:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Postman Collection

[Postman Collection for the Movie-Review-Platform](Movie-Review-Platform.postman_collection.json)



## Application Suitability

### Why this app ? 
With the rise of streaming services, user-driven reviews help viewers find hidden gems while contributing to the film community. 

### Why Microservices ?
 - **Scalability**: Handle increasing user loads without losing performance.
 - **Flexibility**: Experiment with new technologies and frameworks to improve the platform.
 - **User Experience**: faster response times and reduced downtime.

 ### Real World Examples:
 - ** ⭐ IMDb:**
    - Microservices for user profiles, movie data, ratings, reviews, and recommendations.
    - Independent services for search, notifications, and community features.
    - Integration with third-party data providers like The Numbers and Box Office Mojo.
- ** 🍅 Rotten Tomatoes:**
    - Microservices for movie reviews, ratings, consensus, and trailers.
    - Independent services for user accounts, search, and recommendations.
    - Integration with third-party data providers like Metacritic and The New York Times.

## Service Boundaries
1.  ***Authentication Service***:
    - Manages user registration, login, and JWT-based authentication.
2. ***Movie/Review Management Service:***
    - Handles the storage and retrieval of movies/TVshows.
    - Manage real-time users reviews and posts.
    - Notification managemment
    

### System Architecture

![Diagram](/img/Diagram1.jpg "System diagram")
 
## Tech Stack
- 🐍 Flask (Python): REST API microservices.
- 🟩 NodeJS (JavaScript): API gateway 
 - 🔄 Redis: Caching popular movies, reviews.
- 🐘 PostgreSQL: Primary database for storing user profiles, movie details, reviews.
- 🔐 JWT: Secure token-based authentication.
- 🐋 Docker: Containerization for scalable deployment.

## Data Management Design

### Tables

- **User Model**
  ```json
  {
    "userId": "int",
    "username": "string",
    "email": "string",
    "password": "string"
  }
  ```

- **Movie Model**
  ```json
  {
    "id": "int",
    "title": "string",
    "description": "string",
    "rating": "float",
    "genre": "string",
    "poster_url": "string",
    "release_date": "date"
  }
  ```

## Status Endpoints

`GET /api/auth/status` - Check if the authentication service is running.

**Response:**

- 200 OK
  ```json
  {
    "status": "OK",
    "database": "Connected"
  }
  ```

- 500 Server Internal Error
  ```json
  {
    "status": "ERROR",
    "database": "Not connected",
    "error": "str(e)"
  }
  ```

`GET /api/movies/status` - Check if the movie service is running.

**Response:**

- 200 OK
  ```json
  {
    "status": "OK",
    "database": "Connected"
  }
  ```

- 500 Server Internal Error
  ```json
  {
    "status": "ERROR",
    "database": "Not connected",
    "error": "str(e)"
  }
  ```

## Authentication Service Endpoints

`POST /api/auth/register` - Register a new user.

**Request:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirm_password": "string"
}
```

**Response:**

- 201 Created
  ```json
  {
    "message": "User registered successfully"
  }
  ```

- 400 Bad Request
  ```json
  {
    "message": "Username already exists"
  }
  ```

`POST /api/auth/login` - Log in a user.

**Request:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**

- 200 OK
  ```json
  {
    "message": "Login successful",
    "access_token": "string",
    "user": "string"
  }
  ```

- 401 Unauthorized
  ```json
  {
    "message": "Invalid email or password"
  }
  ```

`POST /api/auth/logout` - Log out a user.

**Header:**
```
Authorization: Bearer <token>
```

**Response:**

- 200 OK
  ```json
  {
    "message": "User logged out"
  }
  ```

## Movie Service Endpoints

`GET /api/movies` - Get all movies.

**Response:**

- 200 OK
  ```json
  [
    {
      "id": "int",
      "title": "string",
      "description": "string",
      "rating": "float",
      "genre": "string",
      "poster_url": "string",
      "release_date": "date"
    }
  ]
  ```

`GET /api/movies/{id}` - Get a specific movie.

**Response:**

- 200 OK
  ```json
  {
    "id": "int",
    "title": "string",
    "description": "string",
    "rating": "float",
    "genre": "string",
    "poster_url": "string",
    "release_date": "date"
  }
  ```

- 404 Not Found
  ```json
  {
    "message": "Movie not found"
  }
  ```

`GET /api/movies/popular` - Get popular movies (cached).

**Response:**

- 200 OK
  ```json
  {
    "message": "Results retrieved from cache",
    "data": [
      {
        "id": "int",
        "title": "string",
        "description": "string",
        "rating": "float",
        "genre": "string",
        "poster_url": "string",
        "release_date": "date"
      }
    ]
  }
  ```

`GET /api/movies/search` - Search movies with filters.

**Query Parameters:**
- title (optional)
- genre (optional)
- min_rating (optional)
- max_rating (optional)

**Response:**

- 200 OK
  ```json
  {
    "message": "Results retrieved from cache",
    "data": [
      {
        "id": "int",
        "title": "string",
        "description": "string",
        "rating": "float",
        "genre": "string",
        "poster_url": "string",
        "release_date": "date"
      }
    ]
  }
  ```

`POST /api/movies` - Create a new movie.

**Header:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "title": "string",
  "description": "string",
  "rating": "float",
  "genre": "string",
  "poster_url": "string",
  "release_date": "date"
}
```

**Response:**

- 201 Created
  ```json
  {
    "message": "Movie created",
    "id": "int"
  }
  ```

`PUT /api/movies/{id}` - Update a movie.

**Header:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "title": "string",
  "description": "string",
  "rating": "float",
  "genre": "string",
  "poster_url": "string",
  "release_date": "date"
}
```

**Response:**

- 200 OK
  ```json
  {
    "message": "Movie updated successfully"
  }
  ```

`DELETE /api/movies/{id}` - Delete a movie.

**Header:**
```
Authorization: Bearer <token>
```

**Response:**

- 200 OK
  ```json
  {
    "message": "Movie deleted successfully"
  }
  ```

## WebSocket Implementation

`ws://localhost:PORT` - WebSocket connection endpoint

### Events

- message
- join_notification
- leave_notification
- new_review

### Subscription

`join_notification` - Join a movie review room

**Request:**
```json
{
  "user_id": "string",
  "room_id": "string"
}
```

**Response:**
```json
{
  "message": "User <user_id> has joined the room <room_id>"
}
```

### Updates

`new_review` - Send a new review notification

**Request:**
```json
{
  "user_id": "string",
  "room_id": "string",
  "review_title": "string"
}
```

**Response:**
```json
{
  "message": "User <user_id> added a new review: <review_title>"
}
```

### Unsubscription

`leave_notification` - Leave a movie review room

**Request:**
```json
{
  "user_id": "string",
  "room_id": "string"
}
```

**Response:**
```json
{
  "message": "User <user_id> has left the room <room_id>"
}
```

## Cache Management

`DELETE /api/movies/cache/clear` - Clear all cache

**Response:**

- 200 OK
  ```json
  {
    "message": "All cache cleared successfully"
  }
  ```
## Deployment and Scaling
- Each microservice will be containerized in separate **Docker** containers, ensuring isolation, consistent environments, and compatibility across different machines. 
- Using **Docker Compose**, the deployment process will coordinate multi-container configurations, making it simpler to set up networking, volumes, and scalability for each service. A default network will be configured to allow services to communicate via service names.
- For scalability, **horizontal scaling** will be employed, where more instances of a service are added to handle increased traffic. This distributes the load across multiple containers, improving performance, reliability, and resource efficiency. Docker will manage the build, start, and status checks for each microservice, making sure they can run seamlessly across various environments.
