from time import sleep
import random
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import concurrent.futures
import logging
import traceback
import pandas as pd
from bs4 import BeautifulSoup
import json


chrome_driver_path = r'C:\Users\valen\Desktop\chromedriver-win64\chromedriver.exe'
with open('missing_url.json','r') as f:
    missing_urls = json.load(f)
print(f"Missing URLs to scrape: {missing_urls}")

# Initialize Chrome driver with optimized settings
def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument('--disable-software-rasterizer')

    options.page_load_strategy = 'eager'
    prefs = {
        'profile.managed_default_content_settings.images': 2,
        'profile.managed_default_content_settings.stylesheets': 2
    }
    options.add_experimental_option('prefs', prefs)
    service = Service(executable_path=chrome_driver_path)
    return webdriver.Chrome(service=service, options=options)

# Extract movie information from a given season link
def extract_movie_info(season_link):
    driver = init_driver()
    movie_info = {}
    try:
        driver.get(season_link)
        sleep(random.uniform(1, 3))  # Reduce sleep interval for faster performance

        # Extract movie information
        season_card = WebDriverWait(driver, 10).until(
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
            'Action_link': season_link,
            'Movie Title': movie_title,
            'Movie Link': iframe_src
        }

    except Exception as e:
        logging.error(f"Error extracting movie info from {season_link}: {str(e)}")
        logging.debug(traceback.format_exc())
        movie_info = {'Action_link': season_link, 'Movie Title': 'Error', 'Movie Link': 'Error'}

    finally:
        driver.quit()

    return movie_info

# Extract movie info concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(extract_movie_info, link) for link in missing_urls]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Convert results to DataFrame and save to CSV
df = pd.DataFrame(results)
df.to_csv('movies_with_action_links.csv', index=False)

print("Data has been successfully scraped and saved to 'movies_with_action_links.csv'.")
