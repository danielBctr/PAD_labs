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

// Two-Phase Commit Transaction Manager
class TransactionManager {
  constructor() {
    this.transactions = new Map();
  }

  createTransaction(transactionId, participants) {
    this.transactions.set(transactionId, {
      id: transactionId,
      participants,
      status: 'PENDING',
      votes: new Map(),
      createdAt: Date.now(),
      logs: []
    });
    return transactionId;
  }

  async preparePhase(transactionId) {
    const transaction = this.transactions.get(transactionId);
    if (!transaction) {
      throw new Error('Transaction not found');
    }

    transaction.logs.push(`Prepare Phase Started at ${new Date().toISOString()}`);

    // Parallel prepare requests to all participants
    const preparePromises = transaction.participants.map(async (participant) => {
      try {
        const response = await axios.post(`${participant}/prepare`, { 
          transactionId,
          timestamp: Date.now()
        });
        return { 
          participant, 
          vote: response.data.vote, 
          reason: response.data.reason || null 
        };
      } catch (error) {
        return { 
          participant, 
          vote: 'ABORT', 
          reason: error.message 
        };
      }
    });

    const votes = await Promise.all(preparePromises);
    
    // Check if all participants vote COMMIT
    const canCommit = votes.every(vote => vote.vote === 'COMMIT');
    
    transaction.votes = new Map(votes.map(v => [v.participant, v]));
    transaction.status = canCommit ? 'READY_TO_COMMIT' : 'ABORTED';
    
    transaction.logs.push(`Prepare Phase Completed. Commit Possible: ${canCommit}`);
    
    return {
      transactionId,
      status: transaction.status,
      votes
    };
  }

  async commitPhase(transactionId) {
    const transaction = this.transactions.get(transactionId);
    if (!transaction || transaction.status !== 'READY_TO_COMMIT') {
      throw new Error('Cannot commit transaction');
    }

    transaction.logs.push(`Commit Phase Started at ${new Date().toISOString()}`);

    // Parallel commit requests
    const commitPromises = transaction.participants.map(async (participant) => {
      try {
        const response = await axios.post(`${participant}/commit`, { 
          transactionId,
          timestamp: Date.now()
        });
        return { 
          participant, 
          status: 'COMMITTED', 
          details: response.data 
        };
      } catch (error) {
        return { 
          participant, 
          status: 'COMMIT_FAILED', 
          reason: error.message 
        };
      }
    });

    const commitResults = await Promise.all(commitPromises);
    
    // Check if all participants successfully committed
    const allCommitted = commitResults.every(result => result.status === 'COMMITTED');
    
    transaction.status = allCommitted ? 'COMMITTED' : 'PARTIALLY_COMMITTED';
    transaction.logs.push(`Commit Phase Completed. All Committed: ${allCommitted}`);

    return {
      transactionId,
      status: transaction.status,
      commitResults
    };
  }

  async abortTransaction(transactionId) {
    const transaction = this.transactions.get(transactionId);
    if (!transaction) {
      throw new Error('Transaction not found');
    }

    transaction.logs.push(`Abort Phase Started at ${new Date().toISOString()}`);

    // Parallel abort requests
    const abortPromises = transaction.participants.map(async (participant) => {
      try {
        const response = await axios.post(`${participant}/abort`, { 
          transactionId,
          timestamp: Date.now()
        });
        return { 
          participant, 
          status: 'ABORTED', 
          details: response.data 
        };
      } catch (error) {
        return { 
          participant, 
          status: 'ABORT_FAILED', 
          reason: error.message 
        };
      }
    });

    const abortResults = await Promise.all(abortPromises);
    
    transaction.status = 'ABORTED';
    transaction.logs.push('Abort Phase Completed');

    return {
      transactionId,
      status: transaction.status,
      abortResults
    };
  }

  getTransactionStatus(transactionId) {
    const transaction = this.transactions.get(transactionId);
    if (!transaction) {
      throw new Error('Transaction not found');
    }
    return {
      id: transaction.id,
      status: transaction.status,
      createdAt: transaction.createdAt,
      participants: transaction.participants,
      logs: transaction.logs,
      votes: Array.from(transaction.votes.entries())
    };
  }

  cleanupOldTransactions(maxAge = 24 * 60 * 60 * 1000) { // 24 hours
    const now = Date.now();
    for (const [transactionId, transaction] of this.transactions.entries()) {
      if (now - transaction.createdAt > maxAge) {
        this.transactions.delete(transactionId);
      }
    }
  }
}

const transactionManager = new TransactionManager();

// Existing ServiceRegistry and other code remains the same as in the previous implementation

// Add 2PC Transaction Routes
app.post('/api/transactions/start', (req, res) => {
  const { participants } = req.body;
  if (!participants || !Array.isArray(participants) || participants.length < 2) {
    return res.status(400).json({ 
      message: 'At least two participants required',
      status: 'INVALID_REQUEST'
    });
  }

  const transactionId = `txn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  
  try {
    transactionManager.createTransaction(transactionId, participants);
    res.status(201).json({ 
      transactionId, 
      message: 'Transaction initialized',
      status: 'PENDING'
    });
  } catch (error) {
    res.status(500).json({ 
      message: 'Failed to create transaction',
      error: error.message,
      status: 'ERROR'
    });
  }
});

app.post('/api/transactions/:transactionId/prepare', async (req, res) => {
  const { transactionId } = req.params;
  
  try {
    const prepareResult = await transactionManager.preparePhase(transactionId);
    res.json(prepareResult);
  } catch (error) {
    res.status(500).json({ 
      message: 'Prepare phase failed',
      error: error.message,
      status: 'ERROR'
    });
  }
});

app.post('/api/transactions/:transactionId/commit', async (req, res) => {
  const { transactionId } = req.params;
  
  try {
    const commitResult = await transactionManager.commitPhase(transactionId);
    res.json(commitResult);
  } catch (error) {
    res.status(500).json({ 
      message: 'Commit phase failed',
      error: error.message,
      status: 'ERROR'
    });
  }
});

app.post('/api/transactions/:transactionId/abort', async (req, res) => {
  const { transactionId } = req.params;
  
  try {
    const abortResult = await transactionManager.abortTransaction(transactionId);
    res.json(abortResult);
  } catch (error) {
    res.status(500).json({ 
      message: 'Abort phase failed',
      error: error.message,
      status: 'ERROR'
    });
  }
});

app.get('/api/transactions/:transactionId', (req, res) => {
  const { transactionId } = req.params;
  
  try {
    const transactionStatus = transactionManager.getTransactionStatus(transactionId);
    res.json(transactionStatus);
  } catch (error) {
    res.status(404).json({ 
      message: 'Transaction not found',
      error: error.message,
      status: 'NOT_FOUND'
    });
  }
});

// Periodically clean up old transactions
setInterval(() => {
  transactionManager.cleanupOldTransactions();
}, 24 * 60 * 60 * 1000); // Run daily

// Existing service discovery, proxy, and other routes remain the same...

module.exports = {
  app,
  serviceRegistry,
  transactionManager
};