from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import mysql.connector
import time
import json

def save_to_mysql(data, source):
    try:
        # Connect to the database
        mydb = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'rental_properties')
        )
        cursor = mydb.cursor(buffered=True)

        # Fetch all existing property links from the database
        cursor.execute("SELECT link FROM properties WHERE source = %s", (source,))
        existing_links = {row[0] for row in cursor.fetchall()}

        # Extract new links from the current data
        new_links = {property['link'] for property in data}

        # Identify outdated properties (present in the database but not in the new scrape)
        # Only for this specific source
        outdated_links = existing_links - new_links

        # Remove outdated properties from this source only
        if outdated_links:
            print(f"Removing {len(outdated_links)} outdated {source} properties...")
            delete_query = "DELETE FROM properties WHERE link = %s AND source = %s"
            for link in outdated_links:
                cursor.execute(delete_query, (link, source))
            mydb.commit()
            print(f"Outdated {source} properties removed.")

        # Insert or update properties in the database
        add_property_query = (
            "INSERT INTO properties "
            "(title, price, image_url, link, address, image_urls, latitude, longitude, source) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "title = VALUES(title), price = VALUES(price), "
            "image_url = VALUES(image_url), address = VALUES(address), "
            "image_urls = VALUES(image_urls), latitude = VALUES(latitude), "
            "longitude = VALUES(longitude), source = VALUES(source), "
            "last_updated = NOW()"
        )

        inserted_count = 0
        updated_count = 0

        for property in data:
            try:
                property_data = (
                    property['title'],
                    property['price'],
                    property['image_url'],
                    property['link'],
                    property['address'],
                    json.dumps(property['image_urls']),
                    property.get('latitude'),
                    property.get('longitude'),
                    source  # Convert image URLs to JSON
                )
                cursor.execute(add_property_query, property_data)

                # Check if the query was an insert or update
                if cursor.rowcount == 1:
                    inserted_count += 1
                elif cursor.rowcount == 2:
                    updated_count += 1

            except mysql.connector.Error as err:
                print(f"Error processing property {property['title']}: {err}")
                mydb.rollback() # eeeerrrorrrrrr

        
        mydb.commit()

        print(f"Inserted {inserted_count} new properties.")
        print(f"Updated {updated_count} existing properties.")

    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
    finally:
        
        if 'cursor' in locals():
            cursor.close()
        if 'mydb' in locals() and mydb.is_connected():
            mydb.close()

def scrape_hammer_properties():
    driver_path = '/Users/Nahom/Desktop/chromedriver-win32/chromedriver.exe'
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    
    try:
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
        driver.quit()

if __name__ == "__main__":
    print("Starting property scraper...")
    properties = scrape_hammer_properties()
    
    if properties:
        print(f"\nSuccessfully scraped {len(properties)} properties")
        save_to_mysql(properties, source="Hammer")
    else:
        print("No properties were scraped")