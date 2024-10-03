const express = require('express');
const router = express.Router();
const axios = require('axios');

const API_URL = 'http://login-service:5000/api';

const getAuthHeader = (req) => req.headers.authorization ? { Authorization: req.headers.authorization } : {};

const handleRequest = async (req, res, method, endpoint, data = {}) => {
    try {
        const config = { method, url: `${API_URL}${endpoint}`, data, headers: getAuthHeader(req) };
        const response = await axios(config);
        res.json(response.data);
    } catch (error) {
        res.status(error.response?.status || 500).json(error.response?.data || { message: 'Request failed' });
    }
};

// Authentication Routes
router.post('/auth/login', (req, res) => handleRequest(req, res, 'post', '/auth/login', req.body));
router.post('/auth/register', (req, res) => handleRequest(req, res, 'post', '/auth/register', req.body));
router.post('/auth/logout', (req, res) => handleRequest(req, res, 'post', '/auth/logout'));
router.get('/auth/protected', (req, res) => handleRequest(req, res, 'get', '/auth/protected'));
router.get('/auth/status', (req, res) => handleRequest(req, res, 'get', '/auth/status'));
router.get('/auth/timeout', (req, res) => handleRequest(req, res, 'get', '/auth/timeout'));

// User Routes
router.route('/users/:id')
    .get((req, res) => handleRequest(req, res, 'get', `/users/${req.params.id}`))
    .put((req, res) => handleRequest(req, res, 'put', `/users/${req.params.id}`, req.body))
    .delete((req, res) => handleRequest(req, res, 'delete', `/users/${req.params.id}`));

module.exports = router;
