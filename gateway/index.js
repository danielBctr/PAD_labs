const express = require('express');
const axios = require('axios');
const loginRoutes = require('./routes/login');
const movieRoutes = require('./routes/art');
const app = express();

// Configuration
const BASE_PORT = parseInt(process.env.BASE_PORT, 10) || 3000;
const AUTH_BASE_PORT = parseInt(process.env.AUTH_BASE_PORT, 10) || 4000;
const INSTANCE_COUNT = 3; // Number of replicas per service
const SERVICES_CONFIG = [
  {
    name: 'movie-service',
    basePort: BASE_PORT,
    host: process.env.MOVIE_SERVICE_HOST || 'localhost'
  },
  {
    name: 'auth-service',
    basePort: AUTH_BASE_PORT,
    host: process.env.AUTH_SERVICE_HOST || 'localhost'
  }
];

const GATEWAY_URL = process.env.GATEWAY_URL || `http://localhost:${BASE_PORT}`;
const TIMEOUT_LIMIT = 5000;
const ERROR_THRESHOLD = 3;
const ERROR_TIMEOUT = TIMEOUT_LIMIT * 3.5;

// Enhanced Service Registry with improved circuit breaker
class ServiceRegistry {
  constructor() {
    this.services = new Map();
    this.currentIndex = new Map();
    this.errorCount = new Map();
    this.circuitState = new Map();
    this.lastErrorTime = new Map();
    this.halfOpenAttempts = new Map();
  }

  register(name, host, port) {
    if (!this.services.has(name)) {
      this.services.set(name, []);
      this.currentIndex.set(name, 0);
      this.errorCount.set(name, 0);
      this.circuitState.set(name, 'CLOSED');
      this.lastErrorTime.set(name, null);
      this.halfOpenAttempts.set(name, 0);
    }
    
    const instances = this.services.get(name);
    instances.push({ 
      host, 
      port, 
      health: 'UP',
      lastChecked: new Date().toISOString(),
      startTime: new Date().toISOString(),
      lastError: null
    });
  }

  deregister(name) {
    const success = this.services.delete(name);
    if (success) {
      this.currentIndex.delete(name);
      this.errorCount.delete(name);
      this.circuitState.delete(name);
      this.lastErrorTime.delete(name);
      this.halfOpenAttempts.delete(name);
    }
    return success;
  }

  updateInstanceHealth(serviceName, instanceIndex, status, error = null) {
    const instances = this.services.get(serviceName);
    if (instances && instances[instanceIndex]) {
      instances[instanceIndex].health = status;
      instances[instanceIndex].lastChecked = new Date().toISOString();
      instances[instanceIndex].lastError = error;
    }
  }

  calculateUptime(startTime) {
    const uptime = new Date() - new Date(startTime);
    const seconds = Math.floor(uptime / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    return {
      hours,
      minutes: minutes % 60,
      seconds: seconds % 60
    };
  }

  shouldAttemptRequest(serviceName) {
    const state = this.circuitState.get(serviceName);
    const lastError = this.lastErrorTime.get(serviceName);
    
    if (state === 'OPEN') {
      // Check if enough time has passed to try half-open state
      if (lastError && (Date.now() - lastError) > ERROR_TIMEOUT) {
        this.circuitState.set(serviceName, 'HALF-OPEN');
        this.halfOpenAttempts.set(serviceName, 0);
        return true;
      }
      return false;
    }
    
    if (state === 'HALF-OPEN') {
      const attempts = this.halfOpenAttempts.get(serviceName);
      if (attempts >= 2) { // Allow only limited requests in HALF-OPEN state
        return false;
      }
      this.halfOpenAttempts.set(serviceName, attempts + 1);
    }
    
    return true;
  }

  getHealthyInstance(serviceName) {
    const instances = this.services.get(serviceName);
    if (!instances || instances.length === 0) {
      return null;
    }

    // Try to find a healthy instance starting from the current index
    const startIndex = this.currentIndex.get(serviceName);
    const totalInstances = instances.length;
    
    for (let i = 0; i < totalInstances; i++) {
      const index = (startIndex + i) % totalInstances;
      if (instances[index].health === 'UP') {
        this.currentIndex.set(serviceName, (index + 1) % totalInstances);
        return { instance: instances[index], index };
      }
    }

    return null;
  }

  async handleRequest(serviceName, request) {
    if (!this.shouldAttemptRequest(serviceName)) {
      throw new Error(`Circuit breaker is ${this.circuitState.get(serviceName)}`);
    }

    const healthyInstance = this.getHealthyInstance(serviceName);
    if (!healthyInstance) {
      throw new Error(`No healthy instances available for service: ${serviceName}`);
    }

    const { instance, index } = healthyInstance;
    
    try {
      const response = await Promise.race([
        request(instance),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), TIMEOUT_LIMIT)
        )
      ]);

      // Success handling
      this.handleSuccess(serviceName);
      this.updateInstanceHealth(serviceName, index, 'UP');
      
      return response;
    } catch (error) {
      this.handleFailure(serviceName, error, index);
      throw error;
    }
  }

  handleSuccess(serviceName) {
    const state = this.circuitState.get(serviceName);
    
    if (state === 'HALF-OPEN') {
      this.circuitState.set(serviceName, 'CLOSED');
      this.errorCount.set(serviceName, 0);
      this.lastErrorTime.set(serviceName, null);
      console.log(`Circuit breaker restored to CLOSED for ${serviceName}`);
    }
  }

  handleFailure(serviceName, error, instanceIndex) {
    const currentErrors = this.errorCount.get(serviceName) + 1;
    this.errorCount.set(serviceName, currentErrors);
    this.lastErrorTime.set(serviceName, Date.now());
    
    this.updateInstanceHealth(
      serviceName, 
      instanceIndex, 
      'DOWN', 
      error.message
    );

    const state = this.circuitState.get(serviceName);
    
    if (state === 'HALF-OPEN') {
      this.circuitState.set(serviceName, 'OPEN');
      console.log(`Circuit breaker returned to OPEN for ${serviceName} - failed during HALF-OPEN state`);
    } else if (currentErrors >= ERROR_THRESHOLD) {
      this.circuitState.set(serviceName, 'OPEN');
      console.log(`Circuit breaker OPENED for ${serviceName} - error threshold reached`);
    }
  }

  getAllServices() {
    const servicesInfo = {};
    
    for (const [serviceName, instances] of this.services.entries()) {
      servicesInfo[serviceName] = {
        instances: instances.map(instance => ({
          host: instance.host,
          port: instance.port,
          health: instance.health,
          lastChecked: instance.lastChecked,
          lastError: instance.lastError,
          uptime: this.calculateUptime(instance.startTime)
        })),
        totalInstances: instances.length,
        healthyInstances: instances.filter(i => i.health === 'UP').length,
        circuitBreakerStatus: this.circuitState.get(serviceName),
        errorCount: this.errorCount.get(serviceName),
        lastErrorTime: this.lastErrorTime.get(serviceName),
        currentLoadBalancerIndex: this.currentIndex.get(serviceName)
      };
    }
    
    return servicesInfo;
  }
}

const serviceRegistry = new ServiceRegistry();

// Middleware
app.use(express.json());

// Timeout middleware
app.use((req, res, next) => {
  const timeout = setTimeout(() => {
    if (!res.headersSent) {
      return res.status(408).json({ 
        message: 'Request timed out',
        status: 'TIMEOUT'
      });
    }
  }, TIMEOUT_LIMIT);

  res.on('finish', () => {
    clearTimeout(timeout);
  });
  next();
});

// Enhanced proxy middleware with better error handling
const proxyRequest = async (req, res, serviceName) => {
  try {
    const response = await serviceRegistry.handleRequest(serviceName, async (instance) => {
      const url = `http://${instance.host}:${instance.port}${req.path}`;
      return await axios({
        method: req.method,
        url,
        data: req.body,
        headers: {
          ...req.headers,
          'x-forwarded-for': req.ip,
          'x-forwarded-host': req.hostname,
          'x-forwarded-proto': req.protocol
        }
      });
    });
    
    res.status(response.status).json(response.data);
  } catch (error) {
    if (error.message.includes('Circuit breaker is')) {
      res.status(503).json({ 
        message: 'Service temporarily unavailable',
        status: error.message,
        retryAfter: Math.ceil(ERROR_TIMEOUT / 1000)
      });
    } else if (error.message.includes('No healthy instances available')) {
      res.status(503).json({ 
        message: 'No healthy instances available',
        status: 'SERVICE_UNAVAILABLE'
      });
    } else if (error.message === 'Request timeout') {
      res.status(504).json({ 
        message: 'Service request timed out',
        status: 'TIMEOUT'
      });
    } else {
      console.error('Proxy error:', error);
      res.status(500).json({ 
        message: 'Internal server error',
        error: error.message
      });
    }
  }
};

// Routes
app.use('/api/auth', async (req, res) => {
  await proxyRequest(req, res, 'auth-service');
});

app.use('/api/movies', async (req, res) => {
  await proxyRequest(req, res, 'movie-service');
});

// Service Discovery endpoints
app.post('/api/service-discovery/register', (req, res) => {
  const { name, host, port } = req.body;
  if (!name || !host || !port) {
    return res.status(400).json({ message: 'Missing required fields' });
  }
  serviceRegistry.register(name, host, port);
  res.status(201).json({ message: 'Service registered successfully' });
});

app.post('/api/service-discovery/deregister', (req, res) => {
  const { name } = req.body;
  if (!name) {
    return res.status(400).json({ message: 'Missing service name' });
  }
  if (serviceRegistry.deregister(name)) {
    res.json({ message: 'Service deregistered successfully' });
  } else {
    res.status(404).json({ message: 'Service not found' });
  }
});

app.get('/api/service-discovery/services', (req, res) => {
  const services = serviceRegistry.getAllServices();
  res.json({
    totalServices: Object.keys(services).length,
    gatewayUptime: process.uptime(),
    timestamp: new Date().toISOString(),
    services
  });
});

app.get('/api/service-discovery/service/:name', (req, res) => {
  const services = serviceRegistry.getAllServices();
  const service = services[req.params.name];
  
  if (service) {
    res.json(service);
  } else {
    res.status(404).json({ message: 'Service not found' });
  }
});

app.get('/api/service-discovery/health', (req, res) => {
  const services = serviceRegistry.getAllServices();
  const healthStatus = {
    status: 'UP',
    timestamp: new Date().toISOString(),
    gatewayUptime: process.uptime(),
    services: Object.entries(services).map(([name, info]) => ({
      name,
      status: info.healthyInstances > 0 ? 'UP' : 'DOWN',
      circuitBreakerStatus: info.circuitBreakerStatus,
      activeInstances: info.healthyInstances,
      totalInstances: info.totalInstances,
      lastError: info.lastErrorTime ? {
        time: new Date(info.lastErrorTime).toISOString(),
        timeSince: Math.floor((Date.now() - info.lastErrorTime) / 1000) + ' seconds ago'
      } : null
    }))
  };
  
  healthStatus.status = healthStatus.services.every(s => s.status === 'UP') ? 'UP' : 'DEGRADED';
  res.json(healthStatus);
});

// Start all service instances
const startServiceInstances = async () => {
  for (const serviceConfig of SERVICES_CONFIG) {
    for (let i = 0; i < INSTANCE_COUNT; i++) {
      const port = serviceConfig.basePort + i;
      const instanceName = `${serviceConfig.name}-${i + 1}`;
      
      app.listen(port, () => {
        console.log(`Instance ${i + 1} of ${serviceConfig.name} running on port ${port}`);
        serviceRegistry.register(instanceName, serviceConfig.host, port);
        console.log(`${instanceName} registered with Gateway on port ${port}`);
      });
    }
    console.log(`${INSTANCE_COUNT} instances of ${serviceConfig.name} started and registered.`);
  }
};

startServiceInstances();

module.exports = app;