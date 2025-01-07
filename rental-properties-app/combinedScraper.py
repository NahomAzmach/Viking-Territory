import time
from hammerScraper import scrape_hammer_properties, save_to_mysql
from landmarkScraper import scrape_showmojo_properties
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def should_skip_address(address):
    """Check if this is a listing we should skip."""
    skip_phrases = [
        "General Application",
        "Change of Tenancy",
        "Lease Takeover",
        "Application"
    ]
    return any(phrase.lower() in address.lower() for phrase in skip_phrases)

def clean_address(address):
    """Remove apartment numbers and clean up address for geocoding."""
    # Remove everything after a hyphen (usually unit numbers)
    
    if should_skip_address(address):
        return None

    base_address = address.split('-')[0].strip()
    
    # Remove unit numbers that come after a hash or space
    base_address = base_address.split('#')[0].strip()
    
    # Remove anything that looks like an apartment number (e.g., "Apt 123", "Unit 4B")
    words = base_address.split()
    cleaned_words = []
    skip_next = False
    for i, word in enumerate(words):
        if skip_next:
            skip_next = False
            continue
        if any(pattern in word.lower() for pattern in ['apt', 'unit', 'suite', '#']):
            skip_next = True
            continue
        cleaned_words.append(word)
    
    return ' '.join(cleaned_words)

def get_coordinates(address, max_attempts=3):
    try:

        if should_skip_address(address):
            return None, None
        # Clean the address first
        clean_addr = clean_address(address)
        
        # Extract city from the original address
        if "Lynden, WA" in address:
            city = "Lynden"
        elif "Blaine, WA" in address:
            city = "Blaine"
        else:
            city = "Bellingham"
        
        for attempt in range(max_attempts):
            try:
                geolocator = Nominatim(user_agent=f"rental_properties_app_{attempt}")
                full_address = f"{clean_addr}, {city}, WA"
                
                print(f"Trying to geocode: {full_address}")
                
                location = geolocator.geocode(full_address, timeout=10)
                if location:
                    return location.latitude, location.longitude
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Attempt {attempt + 1} failed for {clean_addr}: {e}")
                time.sleep(2)  # Wait before retry
        
        # If all attempts fail, try without street number
        words = clean_addr.split()
        if len(words) > 1 and words[0].isdigit():
            street_only = ' '.join(words[1:])
            location = geolocator.geocode(f"{street_only}, {city}, WA", timeout=10)
            if location:
                return location.latitude, location.longitude
        
        # If still no result, try with county
        if not location:
            location = geolocator.geocode(f"{clean_addr}, Whatcom County, WA", timeout=10)
            if location:
                return location.latitude, location.longitude
                
        return None, None
    except Exception as e:
        print(f"Error in get_coordinates: {e}")
        return None, None

def process_properties(properties):
    processed = []
    total = len(properties)
    
    print(f"Processing {total} properties for geocoding...")
    
    for index, prop in enumerate(properties, 1):
        try:
            if should_skip_address(prop['address']):
                print(f"Skipping non-property listing {index}/{total}: {prop['address']}")
                continue

            if 'latitude' not in prop or 'longitude' not in prop or not prop['latitude'] or not prop['longitude']:
                lat, lon = get_coordinates(prop['address'])
                if lat and lon:
                    prop['latitude'] = lat
                    prop['longitude'] = lon
                    print(f"Successfully geocoded {index}/{total}: {prop['address']}")
                else:
                    # Try with a simpler version of the address
                    simple_address = prop['address'].split(',')[0].strip()
                    lat, lon = get_coordinates(simple_address)
                    if lat and lon:
                        prop['latitude'] = lat
                        prop['longitude'] = lon
                        print(f"Successfully geocoded simplified {index}/{total}: {simple_address}")
                    else:
                        print(f"Could not geocode {index}/{total}: {prop['address']}")
            processed.append(prop)
            
        except Exception as e:
            print(f"Error processing property {index}/{total}: {e}")
            processed.append(prop)
    
    return processed

def run_all_scrapers():
    try:
        print("Starting Landmark scraper...")
        landmark_properties = scrape_showmojo_properties()
        if landmark_properties:
            print("Processing Landmark properties...")
            processed_landmark = process_properties(landmark_properties)
            save_to_mysql(processed_landmark, source="Landmark")
            print(f"Landmark: Processed {len(processed_landmark)} properties.")
        else:
            print("Landmark: No properties were scraped.")

        print("\nStarting Hammer scraper...")
        hammer_properties = scrape_hammer_properties()
        if hammer_properties:
            print("Processing Hammer properties...")
            processed_hammer = process_properties(hammer_properties)
            save_to_mysql(processed_hammer, source="Hammer")
            print(f"Hammer: Processed {len(processed_hammer)} properties.")
        else:
            print("Hammer: No properties were scraped.")

    except Exception as e:
        print(f"Error in scraper execution: {str(e)}")

if __name__ == "__main__":
    print("Running combined scrapers...")
    run_all_scrapers()