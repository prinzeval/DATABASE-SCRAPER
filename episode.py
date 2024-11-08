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
import os
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


# Extract season links from a given season page URL
def extract_season_links(season_link):
    driver = init_driver()
    season_list = []
    try:
        driver.get(season_link)
        sleep(random.uniform(1, 3))

        season_card = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="player-wrap"]'))
        )
        seasonHTML = season_card.get_attribute('outerHTML')
        seasonsoup = BeautifulSoup(seasonHTML, 'html5lib')
        episode_container = seasonsoup.find('div', {'id': 'details', 'class': 'section-box'})

        if episode_container:
            active_links = episode_container.find_all('a', class_='episode episode_series_link active esp-circle', href=True)
            non_active_links = episode_container.find_all('a', class_='episode episode_series_link esp-circle', href=True)
            all_links = active_links + non_active_links
            season_list.extend(link['href'] for link in all_links)

    except Exception as e:
        logging.error(f"Error extracting season links from {season_link}: {e}")
        logging.debug(traceback.format_exc())

    finally:
        driver.quit()

    return season_list

# Extract episode details from an episode page URL
def extract_episode_details(episode_link):
    driver = init_driver()
    episodes = []
    try:
        driver.get(episode_link)
        sleep(random.uniform(1, 3))

        episode_cards = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@class="player-wrap"]'))
        )

        for card in episode_cards:
            ElementHTML = card.get_attribute('outerHTML')
            Elementsoup = BeautifulSoup(ElementHTML, 'html5lib')
            tit = Elementsoup.find('div', class_='about')
            movie_title = tit.find('h1').text.strip() if tit else 'No Title Found'

            players_iframe = Elementsoup.find('div', class_='player-iframe animation')
            iframe_src = players_iframe.find('iframe').get('src') if players_iframe else None

            if iframe_src:
                episodes.append({'Title': movie_title, 'Iframe_src': iframe_src})
            else:
                logging.warning(f"No iframe source found on {episode_link}.")

    except Exception as e:
        logging.error(f"Error extracting episode details from {episode_link}: {e}")
        logging.debug(traceback.format_exc())

    finally:
        driver.quit()

    return episodes

# Extract season links concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(extract_season_links, link) for link in missing_urls]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Flatten the list of season links
season_list = [link for sublist in results for link in sublist]

# Extract episode details concurrently
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(extract_episode_details, link) for link in season_list]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Flatten and save episode details to CSV
episodes = [episode for sublist in results for episode in sublist]
df = pd.DataFrame(episodes, columns=['Title', 'Iframe_src'])

# Save data to CSV
csv_file_path = 'episode_data.csv'
df.to_csv(csv_file_path, index=False)
print(f"Data has been successfully scraped and saved to '{csv_file_path}'.")
