const express = require('express');
const cors = require('cors');
const { exec } = require('child_process');
const path = require('path');
const AWS = require('aws-sdk');

// Configure AWS SDK
AWS.config.update({
  region: process.env.AWS_REGION || 'us-west-2'
});

// Create DynamoDB client
const dynamoDB = new AWS.DynamoDB.DocumentClient();
const tableName = process.env.DYNAMODB_TABLE || 'Properties';

const app = express();
app.use(cors({ origin: '*' }));
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'healthy' });
});

// Get all properties endpoint
app.get('/properties', async (req, res) => {
  try {
    const params = {
      TableName: tableName
    };

    const result = await dynamoDB.scan(params).promise();
    console.log(`Found ${result.Items.length} properties`);
    res.json(result.Items);
  } catch (error) {
    console.error('DynamoDB query error:', error);
    res.status(500).json({ 
      error: 'Error retrieving properties',
      details: error.message
    });
  }
});

// Add endpoint to manually trigger scraper
app.post('/trigger-scraper', async (req, res) => {
  try {
    exec('python3 combinedScraper.py', (error, stdout, stderr) => {
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

//serve static files from the React app
app.use(express.static(path.join(__dirname, 'client/build')));

//for any requests not handled by other routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
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
  process.exit(0);
});

const port = process.env.PORT || 5000;
app.listen(port, '0.0.0.0', () => {
  console.log(`Server running on port ${port}`);
});
