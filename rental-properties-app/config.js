require('dotenv').config();

module.exports = {
  server: {
    port: process.env.PORT || 5000,
    environment: process.env.NODE_ENV || 'development',
  },
  scraper: {
    schedule: process.env.SCRAPER_SCHEDULE || '0 */3 * * *',
    path: process.env.SCRAPER_PATH || 'combinedScraper.py'
  }
};
