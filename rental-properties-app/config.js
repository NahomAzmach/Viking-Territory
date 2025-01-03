require('dotenv').config();

module.exports = {
  database: {
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME || 'rental_properties',
  },
  server: {
    port: process.env.PORT || 5000,
    environment: process.env.NODE_ENV || 'development',
  },
  scraper: {
    schedule: process.env.SCRAPER_SCHEDULE || '0 */3 * * *',
    path: process.env.SCRAPER_PATH || 'combinedScraper.py'
  }
};