const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
const { exec } = require('child_process');
const cron = require('node-cron');
const path = require('path');

//  connection pool instead of single connection
const pool = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: process.env.DB_NAME,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

pool.getConnection((err, connection) => {
  if (err) {
    console.error('Database connection failed:', err);
  } else {
    console.log('Database connected successfully');
    connection.release();
  }
});

const app = express();
app.use(cors({ origin: '*' }));
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// Improved error handling for properties endpoint
app.get('/properties', async (req, res) => {
  try {
    const [results] = await pool.promise().query('SELECT * FROM properties');
    console.log(`Found ${results.length} properties`);
    res.json(results);
  } catch (error) {
    console.error('Database query error:', error);
    res.status(500).json({ 
      error: 'Error retrieving properties',
      details: error.message
    });
  }
});

// Add endpoint to manually trigger scraper
app.post('/trigger-scraper', async (req, res) => {
  try {
    exec('python combinedScraper.py', (error, stdout, stderr) => {
      if (error) {
        console.error(`Scraper execution error: ${error}`);
        return res.status(500).json({ error: 'Failed to run scraper' });
      }
      console.log(`Scraper output: ${stdout}`);
      res.json({ message: 'Scraper executed successfully' });
    });
  } catch (error) {
    res.status(500).json({ error: 'Failed to trigger scraper' });
  }
});
app.use(express.static(path.join(__dirname, 'client/build')));

// Catch-all handler for any requests not handled by other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
});

// Schedule scraper to run every 3 hours
cron.schedule('0 */3 * * *', () => {
  console.log('Running scheduled scraper...');
  exec('python combinedScraper.py', (error, stdout, stderr) => {
    if (error) {
      console.error(`Scheduled scraper error: ${error}`);
      return;
    }
    console.log(`Scheduled scraper output: ${stdout}`);
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Something broke!',
    details: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received. Shutting down gracefully...');
  pool.end(() => {
    console.log('Database pool closed.');
    process.exit(0);
  });
});

const port = process.env.PORT || 5000;
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
