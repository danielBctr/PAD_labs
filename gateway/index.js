const express = require('express');
const loginRoutes = require('./routes/auth');
const movieRoutes = require('./routes/movie');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Timeout middleware
app.use((req, res, next) => {
    const timeout = setTimeout(() => !res.headersSent && res.status(408).json({ message: 'Request timed out' }), 5000);
    res.on('finish', () => clearTimeout(timeout));
    next();
});

// Define routes
app.use('/api/auth', loginRoutes);
app.use('/api/movie', movieRoutes);

// Error handling
app.use((err, req, res, next) => res.status(500).json({ message: 'Server error' }));

// Handle 404
app.use((req, res) => res.status(404).json({ message: 'Not found' }));

// Start server
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
