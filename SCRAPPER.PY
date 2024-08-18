from time import sleep
import random
import requests
from bs4 import BeautifulSoup
import html5lib
from supabase import create_client, Client
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

import concurrent.futures
import logging
import traceback
import time
import pandas as pd
import os






# Path to your ChromeDriver
chrome_driver_path = '/home/valentine/Desktop/chromedriver-linux64/chromedriver'

# Supabase URL and Key
url = "https://gqsobrbengdkxgfwzfcd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdxc29icmJlbmdka3hnZnd6ZmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjI3MDEwNjYsImV4cCI6MjAzODI3NzA2Nn0.NkopgE1S4MIYK8ZLa_yGN09AFvZfzZJgjy2ufbP5_C8"

# Create Supabase client
supabase: Client = create_client(url, key)

# Function to get the URL
def get_url(index, page_num):
    TEMPLATES = "https://upmovies.net/search-movies/{}/page-{}.html"
    url = TEMPLATES.format(index, page_num)
    return url

# Define the range of alphabets and pages
alphabets = ['V','Z']  # Add more alphabets as needed
num_pages = 8 # Define the number of pages to scrape

# Process each alphabet
for alphabet in alphabets:
    print(f"Scraping Alphabet {alphabet} - Pages")
    
    for page in range(1, num_pages + 1):
        url = get_url(alphabet, page)
        sleep(random.randint(1, 4))  # Random delay to avoid getting blocked
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html5lib')
        
        MOVIE_CON = soup.find_all('div', class_="shortItem listItem")
        my_list_UNFILTERED = []
        
        for tag in MOVIE_CON:
            tag_a = tag.find('a', href=True)
            if tag_a:
                movie_link = tag_a['href']
                my_list_UNFILTERED.append(movie_link)
            else:
                print(f"DANGER retrieve data from {url}.")
        


        # Supabase link check
        # List to store URLs not found in the database
        my_list = []

        # Check each URL in my_list_UNFILTERED
        for url in my_list_UNFILTERED:
            limit = 1000  # Number of records per page
            offset = 0    # Starting point for pagination

            while True:
                # Fetch a page of URLs from the action_link column
                response = supabase.table('movies').select('action_link').range(offset, offset + limit - 1).execute()
                
                # Check if the specific URL is in the current page of results
                db_urls = [item['action_link'] for item in response.data]
                if url in db_urls:
                    break
                
                # If less than the limit of results are returned, we are at the end of the dataset
                if len(response.data) < limit:
                    my_list.append(url)
                    break
                
                # Move to the next page
                offset += limit

        # Output results for the current page
        # if my_list:
        #     print(f"\nThe following URLs from Page {page} are NOT in the database:")
        #     for url in my_list:
        #         print(url)
        else:
            print(f"\nAll URLs from Page {page} are found in the database.")
        
        print(f"Total URLs not in the database for Page {page}: {len(my_list)}")
        print(my_list)

        #out.csv   production  
        

        # Setup logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        def scrape_data(link):
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
            chrome_options.add_argument('--log-level=3')  # Suppress logs

            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            data = []

            try:
                driver.get(link)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//div[@class="film-detail-right"]')))
                
                time.sleep(random.randint(1, 4))  # Mimic human behavior

                # Initialize lists to store scraped data
                jpg_list, genres_list, country_list = [], [], []
                director_list, duration_list, year_list = [], [], []
                actors_list, descript_list = [], []

                details_cards = driver.find_elements(By.XPATH, '//div[@class="film-detail-right"]')

                for d_card in details_cards:
                    elementHTML = d_card.get_attribute('outerHTML')
                    elementsoup = BeautifulSoup(elementHTML, 'html5lib')
                    details = elementsoup.find('div', class_='poster')

                    # Extract poster URL
                    img_tag = details.find('img') if details else None
                    jpg_list.append(img_tag.get('src') if img_tag else 'No Poster URL')

                    # Extract title
                    title_div = elementsoup.find('div', class_='about')
                    h1_tag = title_div.find('h1') if title_div else None
                    my_title = h1_tag.text if h1_tag else 'No Title Found'

                    # Extract other details
                    def extract_text(label):
                        item = elementsoup.find('li', class_='label', string=lambda t: t.startswith(label))
                        return item.text.replace(f'{label}: ', '') if item else f'No {label.split(":")[0]} Found'

                    # Correctly append the extracted values
                    genres_list.append(extract_text('Genres'))
                    country_list.append(extract_text('Country'))
                    director_list.append(extract_text('Director'))
                    duration_list.append(extract_text('Duration'))
                    year_list.append(extract_text('Year'))
                    actors_list.append(extract_text('Actors'))

                    descript_div = elementsoup.find('div', class_='textSpoiler', attrs={'data-height': '60'})
                    descript_list.append(descript_div.text.strip() if descript_div else 'No Description Found')

                # Ensure data is consistent and append to list
                data.append({
                    'Poster URL': jpg_list[0] if jpg_list else 'No Poster URL',
                    'Title': my_title,
                    'Genres': genres_list[0] if genres_list else 'No Genres',
                    'Country': country_list[0] if country_list else 'No Country',
                    'Director': director_list[0] if director_list else 'No Director',
                    'Duration': duration_list[0] if duration_list else 'No Duration',
                    'Year': year_list[0] if year_list else 'No Year',
                    'Actors': actors_list[0] if actors_list else 'No Actors',
                    'Description': descript_list[0] if descript_list else 'No Description'
                })
            
            except Exception as e:
                logging.error(f"Error occurred while processing {link}: {e}")
                logging.debug(traceback.format_exc())  # Print stack trace for debugging
            
            finally:
                driver.quit()

            return data

        # List of URLs to scrape


        # Use ThreadPoolExecutor to run multiple instances concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scrape_data, link) for link in my_list]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Flatten the results
        flattened_results = [item for sublist in results for item in sublist]

        # Convert to DataFrame and save to CSV
        df = pd.DataFrame(flattened_results)
        df.to_csv('out.csv', index=False)

        print("Data has been successfully scraped and saved to 'out.csv'.")


        #episode_data.csv
        
        # Path to your ChromeDriver
        chrome_driver_path = '/home/valentine/Desktop/chromedriver-linux64/chromedriver'

        def init_driver():
            options = Options()
            options.add_argument("--headless")  # Run headless Chrome
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
            options.add_argument("--log-level=3")  # Suppress logs
            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver

        def extract_season_links(season_link):
            driver = init_driver()
            season_list = []
            try:
                driver.get(season_link)
                sleep(random.randint(1, 4))
                
                # Extract season links
                season_card = WebDriverWait(driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="player-wrap"]'))
                )
                seasonHTML = season_card.get_attribute('outerHTML')
                seasonsoup = BeautifulSoup(seasonHTML, 'html5lib')
                episode_container = seasonsoup.find('div', {'id': 'details', 'class': 'section-box'})

                if episode_container:
                    active_links = episode_container.find_all('a', class_='episode episode_series_link active esp-circle', href=True)
                    non_active_links = episode_container.find_all('a', class_='episode episode_series_link esp-circle', href=True)

                    all_links = active_links + non_active_links
                    for link in all_links:
                        season_list.append(link['href'])

            except Exception as e:
                print(f"Error extracting season links from {season_link}: {str(e)}")

            finally:
                driver.quit()

            return season_list

        def extract_episode_details(episode_link):
            driver = init_driver()
            episodes = []
            try:
                driver.get(episode_link)
                sleep(random.randint(1, 4))

                episode_cards = WebDriverWait(driver, 60).until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@class="player-wrap"]'))
                )

                for card in episode_cards:
                    ElementHTML = card.get_attribute('outerHTML')
                    Elementsoup = BeautifulSoup(ElementHTML, 'html5lib')
                    tit = Elementsoup.find('div', class_='about')

                    if tit:
                        movie_title = tit.find('h1').text.strip()
                    else:
                        movie_title = 'No Title Found'

                    players_iframe = Elementsoup.find('div', class_='player-iframe animation')

                    # If the div is found, extract the src attribute from the iframe
                    if players_iframe:
                        iframe_src = players_iframe.find('iframe').get('src')
                        episodes.append({'Title': movie_title, 'Iframe_src': iframe_src})
                    else:
                        print(f"No player iframe found on {episode_link}.")

            except Exception as e:
                print(f"Error extracting episode details from {episode_link}: {str(e)}")

            finally:
                driver.quit()

            return episodes

        # Extract season links concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            futures = [executor.submit(extract_season_links, link) for link in my_list]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Flatten the list of season links
        season_list = [link for sublist in results for link in sublist]

        # Extract episode details concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
            futures = [executor.submit(extract_episode_details, link) for link in season_list]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Flatten the list of episodes
        episodes = [episode for sublist in results for episode in sublist]

        # Convert episodes list to DataFrame
        df = pd.DataFrame(episodes)

        # Ensure DataFrame has the correct columns
        if 'Title' not in df.columns:
            df['Title'] = pd.Series(dtype='str')
        if 'Iframe_src' not in df.columns:
            df['Iframe_src'] = pd.Series(dtype='str')

        # Save to CSV with headers
        csv_file_path = 'episode_data.csv'
        df.to_csv(csv_file_path, index=False, columns=['Title', 'Iframe_src'])

        print(f"Data has been successfully scraped and saved to '{csv_file_path}'.")
















        #movies_with_action_link production 

        

        # Path to your ChromeDriver
        chrome_driver_path = '/home/valentine/Desktop/chromedriver-linux64/chromedriver'

        def init_driver():
            options = Options()
            options.add_argument("--headless")  # Run headless Chrome
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
            options.add_argument("--log-level=3")  # Suppress logs
            service = Service(executable_path=chrome_driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver

        def extract_movie_info(season_link):
            driver = init_driver()
            movie_info = {}
            try:
                driver.get(season_link)
                sleep(random.randint(6, 10))

                # Extract movie information
                season_card = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@class="player-wrap"]'))
                )
                seasonHTML = season_card.get_attribute('outerHTML')
                seasonsoup = BeautifulSoup(seasonHTML, 'html5lib')

                # Extract the title of the movie
                tit = seasonsoup.find('div', class_='about')
                movie_title = tit.find('h1').text.strip() if tit else "Title not found"

                # Extract the iframe source URL
                movie_container = seasonsoup.find('div', {'class': 'player-iframe animation'})
                iframe_src = movie_container.find('iframe').get('src') if movie_container else "Iframe source not found"

                movie_info = {
                    'Action_link': season_link,  # Include the link
                    'Movie Title': movie_title,
                    'Movie Link': iframe_src
                }

            except Exception as e:
                print(f"Error extracting movie info from {season_link}: {str(e)}")
                movie_info = {'Action_link': season_link, 'Movie Title': 'Error', 'Movie Link': 'Error'}

            finally:
                driver.quit()

            return movie_info

        # List of movie links (example)


        # Extract movie info concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(extract_movie_info, link) for link in my_list]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Print results to check the structure
        print(results)

        # Convert results to DataFrame
        df = pd.DataFrame(results)
        df.to_csv('movies_with_action_links.csv', index=False)

        print("Data has been successfully scraped and saved to 'movies_with_action_links.csv'.")









        #csv combination  
        import pandas as pd
        import os
        try:
            # Function to read CSV safely
            def read_csv_safely(file_path):
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    return pd.read_csv(file_path)
                else:
                    print(f"File {file_path} is missing or empty.")
                    return pd.DataFrame()  # Return an empty DataFrame if the file is missing or empty

            # Read CSV files safely
            episodes_df = read_csv_safely('episode_data.csv')
            action_links_df = pd.read_csv('movies_with_action_links.csv')
            out_df = pd.read_csv('out.csv')

            # Rename columns in action_links_df to match those in out_df
            action_links_df = action_links_df.rename(columns={'Movie Title': 'Title', 'Movie Link': 'movie_link'})

            # Merge out_df with action_links_df based on 'Title'
            combined_df = pd.merge(out_df, action_links_df, left_on='Title', right_on='Title', how='left')

            # Merge combined_df with episodes_df based on 'Title'
            if not episodes_df.empty:
                combined_df = pd.merge(combined_df, episodes_df, left_on='Title', right_on='Title', how='left')

            # Print column names to check which columns exist
            print("Columns in combined_df:", combined_df.columns)

            # Aggregate episode links into a comma-separated string
            if 'Iframe_src' in combined_df.columns:
                combined_df['episode_links'] = combined_df.groupby('Title')['Iframe_src'].transform(lambda x: ', '.join(x.dropna()))

            # Drop duplicate rows (since episode links are now aggregated)
            columns_to_check = ['Title', 'Action_link', 'movie_link', 'Genres', 'Country', 'Duration', 'Year', 'Description', 'Poster URL', 'Director', 'Actors']
            existing_columns = [col for col in columns_to_check if col in combined_df.columns]
            print("Existing columns used for dropping duplicates:", existing_columns)

            combined_df = combined_df.drop_duplicates(subset=existing_columns)

            # Drop unnecessary columns
            combined_df = combined_df.drop(columns=['Iframe_src'], errors='ignore')

            # Rename columns to match the desired output format
            combined_df = combined_df.rename(columns={
                'Title': 'movie_title',
                'movie_link': 'movie_link',
                'Action_link': 'action_link',  # Rename to match final output
                'Genres': 'genres',
                'Country': 'country',
                'Duration': 'duration',
                'Year': 'movie_year',
                'Description': 'description',
                'Poster URL': 'movie_image',
                'Director': 'director',
                'Actors': 'actors'
            })

            # Add movie_id column
            combined_df.insert(0, 'movie_id', range(1, len(combined_df) + 1))

            # Save to a new CSV file
            combined_df.to_csv('combined_movie_details.csv', index=False)

            print("CSV files combined and saved as 'combined_movie_details.csv'.")
        except:
            print("empty files")









        #csv to database  
        import pandas as pd
        from supabase import create_client, Client
        import os

        # Supabase credentials
        url = "https://gqsobrbengdkxgfwzfcd.supabase.co"  # Replace with your Supabase URL
        key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdxc29icmJlbmdka3hnZnd6ZmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjI3MDEwNjYsImV4cCI6MjAzODI3NzA2Nn0.NkopgE1S4MIYK8ZLa_yGN09AFvZfzZJgjy2ufbP5_C8"  # Replace with your Supabase key

        # Initialize Supabase client
        supabase: Client = create_client(url, key)

        # Path to CSV file
        csv_file_path = 'combined_movie_details.csv'  # Replace with your CSV file path

        # Check if the file exists
        if not os.path.isfile(csv_file_path):
            print(f"Error: The file '{csv_file_path}' does not exist.")
        else:
            try:
                # Read CSV file
                df = pd.read_csv(csv_file_path)

                # Check if the DataFrame is empty
                if df.empty:
                    print("Error: The CSV file is empty.")
                else:
                    # Drop the 'movie_id' column
                    df = df.drop(columns=['movie_id'], errors='ignore')

                    # Convert all DataFrame values to strings and handle NaN
                    df = df.astype(str).replace('nan', '')

                    # Print the first few rows and column names for debugging
                    print("DataFrame columns:", df.columns)
                    print("First few rows of the DataFrame:")
                    print(df.head())

                    # Table name in Supabase
                    table_name = 'movies'

                    # Convert DataFrame to dictionary and insert into Supabase
                    records = df.to_dict(orient='records')

                    try:
                        # Perform insert operation
                        response = supabase.table(table_name).insert(records).execute()
                        print("Insert response:", response.data)
                    except Exception as e:
                        print("Error inserting records:", e)
            except pd.errors.EmptyDataError:
                print("Error: The CSV file is empty or cannot be read.")
            except Exception as e:
                print("Error reading the CSV file:", e)






        #alarm for work done 
        import pyttsx3

        # Initialize the text-to-speech engine
        engine = pyttsx3.init()

        # List available voices
        voices = engine.getProperty('voices')

        # Print available voices to choose from
        for voice in voices:
            print(f"ID: {voice.id}, Name: {voice.name}, Lang: {voice.languages}")

        # Set properties for a clearer and dramatic effect
        engine.setProperty('rate', 150)  # Speed percent (can go over 100)
        engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

        # Select a voice (change 'english-us' to another ID from your list if needed)
        selected_voice_id = 'english-us'  # Use a suitable voice ID from your list
        for voice in voices:
            if voice.id == selected_voice_id:
                engine.setProperty('voice', voice.id)
                break

        # Speak the text

        engine.say("CODE EXECUTION SUCCESSFUL,  CHECK THE DATABASE FOR MORE INFORMATION ")

        # Wait for the speech to complete
        engine.runAndWait()




    print(f"Completed scraping and checking for Alphabet {alphabet}")
#alarm for work done 
import pyttsx3

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# List available voices
voices = engine.getProperty('voices')

# Print available voices to choose from
for voice in voices:
    print(f"ID: {voice.id}, Name: {voice.name}, Lang: {voice.languages}")

# Set properties for a clearer and dramatic effect
engine.setProperty('rate', 150)  # Speed percent (can go over 100)
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

# Select a voice (change 'english-us' to another ID from your list if needed)
selected_voice_id = 'english-us'  # Use a suitable voice ID from your list
for voice in voices:
    if voice.id == selected_voice_id:
        engine.setProperty('voice', voice.id)
        break

# Speak the text

engine.say("VALENTINE FINISH OTILOR FINISH FINISH, ")

# Wait for the speech to complete
engine.runAndWait()

