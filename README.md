# 🎬 Movie Review Platform
An online platform for users to review movies.

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

![Diagram](/img/diagram.jpg "System diagram")

 ## Communication Patterns

### Synchronous
 - **gRPC:**
    - ***Advantages*** : Fast, low-latency, efficient, and platform-agnostic.
    - ***Use cases*** : Internal communication between microservices, e.g., fetching movie details, updating ratings.
- **REST (HTTP):**
    - ***Advantages*** : Widely adopted, easy to understand, and supports a wide range of clients.
    - ***Use cases*** : External communication with clients, e.g., API endpoints for movie search.

### Asynchronous
- **WebSockets:**
    - ***Advantages*** : Real-time communication, low latency, and efficient for real-time updates.
    - ***Use cases*** : new review notifications, updates movies, recommendations.
 
## Tech Stack
- 🐍 Flask (Python): REST API microservices.
- 🟩 NodeJS (JavaScript): API gateway 
 - 🔄 Redis: Caching popular movies, reviews.
- 🐘 PostgreSQL: Primary database for storing user profiles, movie details, reviews.
- 🔐 JWT: Secure token-based authentication.
- 🐋 Docker: Containerization for scalable deployment.

## Data Management
Both microservices use PostgreSQL for data storage. Additional services like Redis can be used for caching popular movies and reviews.

### Tables
- **User table**:
```json
{
    "id": "int",
    "username": "string",
    "email": "string",
    "password": "hashed_string"
}
```
- **Movie table**:
```json
{
    "id": "int",
    "title": "string",
    "description": "string",
    "release_date": "date",
    "genre": "string"
}
```
- **Review table**:
```json
{
    "id": "int",
    "movie_id": "int",
    "user_id": "int",
    "rating": "int",
    "review_text": "string",
    "created_at": "datetime"
}
```

### Authentication Endpoints
- **POST /api/auth/login**<br>
 *Login a user and return a JWT token.*
- **Request:**
 ```json
 {
  "email": "movielover@mail.com",
  "password": "somePass"
}
```
- **Response:**
    - **200 OK**
    ```json
    {
  "message": "Login successful",
  "token": "JWT"
    }
    ```
    - **401 Unauthorized**
    ```json
    {
  "message": "Invalid email or password"
    }
    ```
    - **500 Internal Server Error**
    ```json
    {
  "message": "Something went wrong. Please try again later."
    }
    ```

- **POST /api/auth/register**<br>
 *Register a new user*
- **Request:**
```json
{
  "username": "MovieMan",
  "email": "movieman21@mail.com",
  "password": "anotherPass"
}
```
- **Responses:**
    - **201 Created**
    ```json
    {
  "message": "User registered successfully"
    }
    ```
    - **409 Conflict**
    ```json
    {
  "message": "Email already in use."
    }
    ```   
### Movie Management Endpoints
- **GET /api/movies/{id}**<br>
 *Get movie details by ID.*

- **Response:**
    - **200 OK**
    ```json
    {
  "title": "Inception",
  "description": "A mind-bending thriller...",
  "release_date": "2010-07-16",
  "genre": "Sci-Fi"
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "Movie not found."
    }
    ```

- **POST /api/movies**<br>
 *create a new movie.*
 - **Request:**
 ```json
 {
  "title": "New Movie",
  "description": "Movie description...",
  "release_date": "2024-01-01",
  "genre": "Action"
}
```
- **Response:**
    - **201 Created**
    ```json
    {
  "message": "Movie added successfully"
    }
    ```
    - **400 Bad Request**
    ```json
    {
  "message": "Invalid movie data."
    }
    ```
- **PUT /api/movies/{id}**<br>
 *Update movie details by ID.*

 - **Request:**
 ```json
 {
  "title": "Updated Movie Title",
  "description": "Updated movie description",
  "release_date": "2025-01-01",
  "genre": "Action"
}
```
- **Response:**
    - **200 OK**
    ```json
    {
  "message": "Movie updated successfully"
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "Movie not found."
    }
    ```

- **DELETE /api/movies/{id}**<br>
 *Delete a movie by ID.*
- **Response:**
    - **200 OK**
    ```json
    {
  "message": "Movie deleted successfully"
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "Movie not found."
    }
    ```

### Review Endpoints
- **POST /api/reviews**<br>
*Add a review to a movie.*
- **Request:**
    ```json
    {
  "movie_id": 1,
  "rating": 5,
  "review_text": "Amazing movie!"
    }
    ```
- **Response:**
    - **201 Created**
    ```json
    {
    "message": "Review submitted!"
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "Movie not found."
    }
    ```
    - **500 Internal Server Error**
    ```json
    {
  "message": "Error submitting review."
    }
    ```

- **PUT /api/reviews/{id}**<br>
*Update a review by ID.*
- **Request:**
    ```json
    {
  "rating": 4,
  "review_text": "Updated review text"
    }
    ```
- **Response:**
    - **200 OK**
    ```json
    {
  "message": "Review updated successfully"
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "Review not found."
    }
    ```
    - **400 Bad Request**
    ```json
    {
  "message": "Invalid review data."
    }
    ```
- **DELETE /api/reviews/{id}**<br>
*Delete a review by ID.*
- **Response:**
    - **200 OK**
    ```json
    {
  "message": "Review deleted successfully"
    }
    ```

    - **404 Not Found**
    ```json
    {
  "message": "Review not found."
    }
    ```
    - **500 Internal Server Error**
    ```json
    {
  "message": "Error deleting review."
    }
    ```
- **GET /api/reviews/{movie_id}**<br>
*Get all reviews for a movie.*
- **Response:**
    - **200 OK**
    ```json
    [
  {
    "review_id": 1,
    "movie_id": 123,
    "user": "MovieMan1",
    "rating": 5,
    "review_text": "Amazing movie!",
    "created_at": "date1"
  },
  {
    "review_id": 2,
    "movie_id": 123,
    "user": "MovieMan2",
    "rating": 4,
    "review_text": "It s*cks.",
    "created_at": "date2"
  }
    ]
    ```
    - **400 Bad Request**
    ```json
    {
  "message": "Invalid movie ID."
    }
    ```
    - **404 Not Found**
    ```json
    {
  "message": "No reviews found for this movie."
    }
    ```
- **GET /api/reviews/user/{user_id}**<br>
*Get all reviews posted by a specific user.*
- **Response:**
    - **200 OK**
    ```json
    [
  {
    "review_id": 1,
    "movie_id": 123,
    "movie_title": "Inception",
    "rating": 5,
    "review_text": "F*cking good!",
    "created_at": "date3"
  },
  {
    "review_id": 3,
    "movie_id": 456,
    "movie_title": "The Matrix",
    "rating": 4,
    "review_text": "Red or Blue?",
    "created_at": "date4"
  }
    ]
    ```
    - **404 Not Found**
    ```json
    {
  "message": "No reviews found for this user."
    }
    ```
### Other Endpoints
  - **GET /api/reviews**<br>
  *Users connect to the WebSocket to receive live updates for new reviews in real-time.*
  - **Successful Connection**
    - **101 Switching Protocols (WebSocket handshake)**
    ```json
    {
    "message": "Connection established. You are now subscribed to live review updates."
    }
    ```
  - **Live Notification**
    ```json
    {
    "event": "new_review",
    "data": {
      "review_id": 1234,
      "movie_title": "Inception",
      "rating": 5,
      "review_text": "Amazing movie!",
      "created_at": "date5",
      "user": "JMovieMan39"
    }
    }
    ```
- **Post /api/subscribe**<br>
*This allows users to subscribe to live updates for reviews of a specific movie.*
- **Body**
    ```json
    {
    "user_id": 42,
    "movie_id": 123
    }
    ```
- **Response:**
    - 200 OK
    ```json
    {
  "message": "Successfully subscribed to movie review updates."
    }
    ```
    - 404 Not Found
    ```json
    {
  "message": "Movie not found."
    }
    ```
- **Post /api/unsubscribe**<br>
*This allows users to unsubscribe from live updates for reviews of a specific movie.*
- **Body**
    ```json
    {
    "user_id": 42,
    "movie_id": 123
    }
    ```
- **Response:**
    - 200 OK
    ```json
    {
  "message": "Successfully unsubscribed from movie review updates."
    }
    ```
    - 404 Not Found
    ```json
    {
  "message": "Subscription not found."
    }
    ```
## Deployment and Scaling
- Each microservice will be containerized in separate **Docker** containers, ensuring isolation, consistent environments, and compatibility across different machines. 
- Using **Docker Compose**, the deployment process will coordinate multi-container configurations, making it simpler to set up networking, volumes, and scalability for each service. A default network will be configured to allow services to communicate via service names.
- For scalability, **horizontal scaling** will be employed, where more instances of a service are added to handle increased traffic. This distributes the load across multiple containers, improving performance, reliability, and resource efficiency. Docker will manage the build, start, and status checks for each microservice, making sure they can run seamlessly across various environments.
