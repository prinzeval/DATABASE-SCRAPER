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
import json


chrome_driver_path = r'C:\Users\valen\Desktop\chromedriver-win64\chromedriver.exe'

with open('missing_url.json','r') as f:
    missing_urls = json.load(f)
print(f"Missing URLs to scrape: {missing_urls}")

# Function to scrape data
def scrape_data(link):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.page_load_strategy = 'eager'  # Only load essential HTML

    # Block images and CSS
    prefs = {'profile.managed_default_content_settings.images': 2, 
             'profile.managed_default_content_settings.stylesheets': 2}
    chrome_options.add_experimental_option('prefs', prefs)

    service = Service(executable_path=chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    data = []

    try:
        driver.get(link)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//div[@class="film-detail-right"]'))
        )

        details_cards = driver.find_elements(By.XPATH, '//div[@class="film-detail-right"]')
        print(f"Found {len(details_cards)} details cards on {link}")

        if not details_cards:
            logging.error(f"No detail cards found on {link}")
            return data  

        for d_card in details_cards:
            elementHTML = d_card.get_attribute('outerHTML')
            elementsoup = BeautifulSoup(elementHTML, 'html5lib')
            details = elementsoup.find('div', class_='poster')

            img_tag = details.find('img') if details else None
            poster_url = img_tag.get('src') if img_tag else 'No Poster URL'

            title_div = elementsoup.find('div', class_='about')
            h1_tag = title_div.find('h1') if title_div else None
            title = h1_tag.text if h1_tag else 'No Title Found'

            def extract_text(label):
                item = elementsoup.find('li', class_='label', string=lambda t: t.startswith(label))
                return item.text.replace(f'{label}: ', '') if item else f'No {label.split(":")[0]} Found'

            data.append({
                'Poster URL': poster_url,
                'Title': title,
                'Genres': extract_text('Genres'),
                'Country': extract_text('Country'),
                'Director': extract_text('Director'),
                'Duration': extract_text('Duration'),
                'Year': extract_text('Year'),
                'Actors': extract_text('Actors'),
                'Description': elementsoup.find('div', class_='textSpoiler', attrs={'data-height': '60'}).text.strip()
            })

    except Exception as e:
        logging.error(f"Error occurred while processing {link}: {e}")
        logging.debug(traceback.format_exc())
    
    finally:
        driver.quit()

    return data

# Use ThreadPoolExecutor for concurrent scraping with increased workers
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(scrape_data, link) for link in missing_urls]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

# Flatten results and save to CSV
flattened_results = [item for sublist in results if sublist for item in sublist]
if flattened_results:
    df = pd.DataFrame(flattened_results)
    df.to_csv('out.csv', index=False)
    print("Data has been successfully scraped and saved to 'out.csv'.")
else:
    print("No data was scraped.")
