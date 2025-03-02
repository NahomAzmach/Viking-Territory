from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os

def scrape_showmojo_properties():
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

        # Load the ShowMojo page
        url = 'https://showmojo.com/c0e82d50b2/listings/mapsearch'
        driver.get(url)

        # Scroll down to the bottom of the page and wait for more listings to load
        SCROLL_PAUSE_TIME = 3
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to allow new content to load
            time.sleep(SCROLL_PAUSE_TIME)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # If the scroll height hasn't changed, we've reached the end of the page
                break
            last_height = new_height

        # After scrolling, get the final HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Close the browser
        driver.quit()

        # Find all property listings inside the iframe
        properties = soup.find_all('div', class_='cnt_box')
        property_list = []

        for property in properties:
            title = property.find('div', class_='title').text.strip() if property.find('div', class_='title') else 'N/A'
            price = property.find('li', class_='rent').text.strip() if property.find('li', class_='rent') else 'N/A'
            image_url = property.find('img')['src'] if property.find('img') else 'N/A'
            link = property.find('a')['href'] if property.find('a') else 'N/A'
            address = property.find('div', class_='address').text.strip() if property.find('div', class_='address') else 'N/A'
            
            property_list.append({
                'title': title,
                'price': price,
                'image_url': image_url,
                'link': f"https://showmojo.com{link}",
                'address': address,
                'image_urls': [image_url] if image_url != 'N/A' else []
            })

        return property_list

    except Exception as e:
        print(f"Error in ShowMojo scraper: {e}")
        return []

if __name__ == "__main__":
    # Scrape properties
    properties = scrape_showmojo_properties()

    #Print the scraped properties to check if the data is correct
    if properties:
        for prop in properties:
            print(prop)  # This will print out each scraped property to the console
        
        print(f"Scraped {len(properties)} properties.")
    else:
        print("No properties were scraped.")
