from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import mysql.connector
import time

# Function to insert scraped data into MySQL
def save_to_mysql(data):
    try:
        # Connect to the MySQL database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Nadaazm@12",
            database="rental_properties"
        )

        # Create a cursor object to execute SQL queries
        cursor = mydb.cursor()

        # SQL query to insert data into the properties table
        add_property = ("INSERT INTO properties "
                        "(title, price, image_url, link, address) "
                        "VALUES (%s, %s, %s, %s, %s)")

        # Loop through the scraped data and insert it into the MySQL table
        for property in data:
            property_data = (
                property['title'], 
                property['price'], 
                property['image_url'], 
                property['link'], 
                property['address']
            )
            cursor.execute(add_property, property_data)

        # Commit the transaction to save the data
        mydb.commit()

        print(f"Inserted {cursor.rowcount} rows successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    
    finally:
        # Close the cursor and the connection
        cursor.close()
        mydb.close()

# Function to scrape properties from Hammer Properties
def scrape_hammer_properties():
    # Path to your downloaded ChromeDriver
    driver_path = '/Users/Nahom/Desktop/chromedriver-win32/chromedriver.exe'
    service = Service(driver_path)

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(service=service)

    # Load the Hammer Properties page
    url = 'https://www.hammerpropertiesnw.com/availability'
    driver.get(url)

    # Wait for the page to load
    time.sleep(3)  # Adjust the time as needed

    # Get the page source and parse with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    # Find all property listings
    properties = soup.find_all('div', class_='listing-item')
    property_list = []

    for property in properties:
        # Extract data
        title = property.find('h2', class_='address').text.strip() if property.find('h2', class_='address') else 'N/A'
        # Locate the price by finding the h3 tag with class 'rent' and then finding the 'div' with class 'smaller' inside it
        rent_section = property.find('h3', class_='rent')
        price = rent_section.get_text(strip=True, separator=" ").replace("RENT", "").strip() if rent_section else 'N/A'
        image_tag = property.find('div', class_='slider-images').find('img') if property.find('div', class_='slider-images') else None
        image_url = image_tag['src'] if image_tag else 'N/A'
        link_tag = property.find('a', class_='slider-link')
        link = f"https://www.hammerpropertiesnw.com{link_tag['href']}" if link_tag else 'N/A'
        address = title  # Based on the structure, the title also serves as the address here

        # Append to list
        property_list.append({
            'title': title,
            'price': price,
            'image_url': image_url,
            'link': link,
            'address': address
        })

    return property_list

if __name__ == "__main__":
    # Scrape properties from Hammer Properties
    properties = scrape_hammer_properties()

    # Print the scraped properties to check if the data is correct
    if properties:
        for prop in properties:
            print(prop)  # This will print out each scraped property to the console

        # Save to MySQL if properties exist
        save_to_mysql(properties)
        print(f"Scraped {len(properties)} properties.")
