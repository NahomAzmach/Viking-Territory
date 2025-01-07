
import schedule
import time
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    filename='scraper_server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def run_scraper():
    try:
        logging.info(f"Starting scraper at {datetime.now()}")
        # Run the combined scraper
        os.system('python combinedScraper.py')
        logging.info("Scraper finished successfully")
    except Exception as e:
        logging.error(f"Scraper failed with error: {e}")

def main():
    logging.info("Starting scraper server...")
    
    # Schedule scraper to run every 3 hours
    schedule.every(3).hours.do(run_scraper)
    
    # right on startup
    run_scraper()
    
    logging.info("Scheduler running. Ctrl+C to exit.")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logging.error(f"Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes if there's an error

if __name__ == "__main__":
    main()
