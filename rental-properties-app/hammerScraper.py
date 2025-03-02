from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import json
import os

def scrape_hammer_properties():
    # Set up headless Chrome for EC2
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Path to ChromeDriver - EC2 Amazon Linux 2 location
    driver_path = '/usr/bin/chromedriver'
    
    try:
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        url = 'https://www.hammerpropertiesnw.com/availability'
        driver.get(url)
        
        # Wait for listings and give extra time for slider images to load
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listing-item")))
        time.sleep(2)  # Allow dynamic content to load
        
        property_list = []
        
        # Process each listing
        listings = driver.find_elements(By.CLASS_NAME, "listing-item")
        
        for listing in listings:
            try:
                # Click through all slides to ensure all images are loaded
                next_button = listing.find_elements(By.CLASS_NAME, "slider-right-arrow")
                if next_button:
                    max_clicks = 10  # Safety limit
                    clicks = 0
                    while clicks < max_clicks:
                        try:
                            next_button[0].click()
                            time.sleep(0.5)  # Brief pause between clicks
                            clicks += 1
                        except:
                            break

                # Now get the updated HTML after clicking through slides
                listing_html = listing.get_attribute('outerHTML')
                soup = BeautifulSoup(listing_html, 'html.parser')
                
                # Extract basic info
                title = soup.find('h2', class_='address')
                title = title.text.strip() if title else 'N/A'
                
                price_elem = soup.find('h3', class_='rent')
                if price_elem:
                    for div in price_elem.find_all('div'):
                        div.decompose()
                    price = price_elem.get_text(strip=True)
                else:
                    price = 'N/A'
                
                link_elem = soup.find('a', class_='slider-link')
                link = f"https://www.hammerpropertiesnw.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else 'N/A'
                
                # Extract ALL slider images
                image_urls = []
                slider_images = soup.find_all('div', class_='slider-image')
                
                for slider in slider_images:
                    # Get background-image URL
                    style = slider.get('style', '')
                    data_background = slider.get('data-background-image', '')
                    
                    # Try style attribute first
                    if 'background-image' in style:
                        url_start = style.find('url(') + 4
                        url_end = style.find(')', url_start)
                        image_url = style[url_start:url_end].strip('"\'')
                    # Then try data-background-image
                    elif data_background:
                        image_url = data_background
                    else:
                        continue
                        
                    # Clean up URL
                    if image_url:
                        if image_url.startswith('//'):
                            image_url = f"https:{image_url}"
                        elif not image_url.startswith('http'):
                            image_url = f"https://www.hammerpropertiesnw.com{image_url}"
                        if image_url not in image_urls:  # Avoid duplicates
                            image_urls.append(image_url)
                
                # Get total number of slides from slider-total if available
                slider_total = soup.find('div', class_='slider-total')
                if slider_total:
                    print(f"Total slides for {title}: {slider_total.text}")
                
                # Debug print
                print(f"Found {len(image_urls)} images for {title}")
                
                property_data = {
                    'title': title,
                    'price': price,
                    'image_url': image_urls[0] if image_urls else 'N/A',
                    'link': link,
                    'address': title,
                    'image_urls': image_urls
                }
                
                property_list.append(property_data)
                print(f"Scraped property: {title}")
                
            except Exception as e:
                print(f"Error processing listing: {e}")
                continue
        
        return property_list
        
    except Exception as e:
        print(f"Scraping error: {e}")
        return []
        
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    print("Starting property scraper...")
    properties = scrape_hammer_properties()
    
    if properties:
        print(f"\nSuccessfully scraped {len(properties)} properties")
        # I would save the properties onto dynamo here id it was the standalone version
        # But in the combined version, this is handled by combinedScraper.py
    else:
        print("No properties were scraped")
