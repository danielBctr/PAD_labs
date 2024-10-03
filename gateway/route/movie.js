const express = require('express');
const router = express.Router();
const axios = require('axios');

const MOVIE_SERVICE_URL = 'http://movie-management-service:5001/api';
const getAuthHeader = (req) => req.headers.authorization ? { Authorization: req.headers.authorization } : {};

const handleRequest = async (req, res, method, endpoint, data = {}) => {
    try {
        const config = { method, url: `${MOVIE_SERVICE_URL}${endpoint}`, data, headers: getAuthHeader(req) };
        const response = await axios(config);
        res.status(method === 'post' ? 201 : 200).json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).send(error.response?.data || 'Server error');
    }
};

// Movie Routes
router.get('/:id', (req, res) => handleRequest(req, res, 'get', `/movies/${req.params.id}`));
router.get('/', (req, res) => handleRequest(req, res, 'get', '/movies'));
router.get('/popular', (req, res) => handleRequest(req, res, 'get', '/movies/popular'));
router.get('/search', (req, res) => handleRequest(req, res, 'get', '/movies/search', req.query));
router.post('/', (req, res) => handleRequest(req, res, 'post', '/movies', req.body));
router.put('/:id', (req, res) => handleRequest(req, res, 'put', `/movies/${req.params.id}`, req.body));
router.delete('/:id', (req, res) => handleRequest(req, res, 'delete', `/movies/${req.params.id}`));

// Review Routes
router.route('/reviews/:id')
    .get((req, res) => handleRequest(req, res, 'get', `/reviews/${req.params.id}`))
    .put((req, res) => handleRequest(req, res, 'put', `/reviews/${req.params.id}`, req.body))
    .delete((req, res) => handleRequest(req, res, 'delete', `/reviews/${req.params.id}`));
router.get('/:movieId/reviews', (req, res) => handleRequest(req, res, 'get', `/movies/${req.params.movieId}/reviews`));
router.post('/reviews', (req, res) => handleRequest(req, res, 'post', '/reviews', req.body));

// Profile Routes
router.route('/profile')
    .get((req, res) => handleRequest(req, res, 'get', '/movies/profile'))
    .put((req, res) => handleRequest(req, res, 'put', '/movies/profile', req.body))
    .delete((req, res) => handleRequest(req, res, 'delete', '/movies/profile'));

// Login
router.post('/login', (req, res) => handleRequest(req, res, 'post', '/movies/login', req.body));

module.exports = router;
