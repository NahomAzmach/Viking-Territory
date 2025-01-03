from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import mysql.connector
import time
import json

# Function to insert scraped data into MySQL
def save_to_mysql(data, source):
    try:
        # Connect to the MySQL database
        mydb = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME', 'rental_properties')
        )

        # Check if the connection was successful
        if mydb.is_connected():
            print("Connection successful!")
        else:
            print("Failed to connect to the database.")

        # Create a cursor object to execute SQL queries
        cursor = mydb.cursor(buffered=True)
        cursor.execute("SELECT link FROM properties WHERE source = %s", (source,))
        existing_links = {row[0] for row in cursor.fetchall()}

        # Extract new links from the current data
        new_links = {property['link'] for property in data}

        # Identify outdated properties for this source only
        outdated_links = existing_links - new_links

        # Remove outdated properties from this source
        if outdated_links:
            print(f"Removing {len(outdated_links)} outdated {source} properties...")
            delete_query = "DELETE FROM properties WHERE link = %s AND source = %s"
            for link in outdated_links:
                cursor.execute(delete_query, (link, source))
            mydb.commit()
            print(f"Outdated {source} properties removed.")

        # SQL query to insert data into the properties table
        add_property = ("""
            INSERT INTO properties (title, price, image_url, link, address, latitude, longitude, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                title = VALUES(title),
                price = VALUES(price),
                image_url = VALUES(image_url),
                address = VALUES(address),
                latitude = VALUES(latitude),
                longitude = VALUES(longitude),
                source = VALUES(source),
                last_updated = NOW()
        """)

        # Loop through the scraped data and insert it into the MySQL table
        for property in data:
            property_data = (
                property['title'], 
                property['price'], 
                property['image_url'], 
                property['link'], 
                property['address'],
                property.get('latitude'),  # Added these lines
                property.get('longitude'), # Added these lines
                source
            )
            print(f"Attempting to insert: {property_data}")  # Print each property before inserting
            cursor.execute(add_property, property_data)

        # Commit the transaction to save the data
        mydb.commit()

        print(f"Inserted {cursor.rowcount} rows successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    
    finally:
        # Close the cursor and the connection
        if 'cursor' in locals():
            cursor.close()
        if 'mydb' in locals() and mydb.is_connected():
            mydb.close()

# Function to scrape properties
def scrape_showmojo_properties():
    # Path to your downloaded ChromeDriver
    driver_path = '/Users/Nahom/Desktop/chromedriver-win32/chromedriver.exe'
    service = Service(driver_path)

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(service=service)

    # Load the ShowMojo page
    url = 'https://showmojo.com/c0e82d50b2/listings/mapsearch'
    driver.get(url)

    # Scroll down to the bottom of the page and wait for more listings to load
    SCROLL_PAUSE_TIME = 3
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom
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

if __name__ == "__main__":
    # Scrape properties
    properties = scrape_showmojo_properties()

    # Print the scraped properties to check if the data is correct
    if properties:
        for prop in properties:
            print(prop)  # This will print out each scraped property to the console
        
        # Save to MySQL if properties exist
        save_to_mysql(properties, source="ShowMojo")
        print(f"Scraped {len(properties)} properties.")
