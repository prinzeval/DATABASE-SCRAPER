from time import sleep
import random
import requests
from bs4 import BeautifulSoup
import html5lib
from supabase import create_client, Client
import os
import json

# Supabase URL and Key
url = "https://gqsobrbengdkxgfwzfcd.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdxc29icmJlbmdka3hnZnd6ZmNkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjI3MDEwNjYsImV4cCI6MjAzODI3NzA2Nn0.NkopgE1S4MIYK8ZLa_yGN09AFvZfzZJgjy2ufbP5_C8"

# Create Supabase client
supabase: Client = create_client(url, key)

def get_movie_urls_not_in_db(alphabet, num_pages=1):
    """
    Scrapes movie URLs and returns those not found in the Supabase database.

    Args:
        alphabet (str): The movie title or alphabet to search.
        num_pages (int): Number of pages to scrape for each alphabet.

    Returns:
        list: URLs that were not found in the database.
    """
    
    # Helper function to construct the URL for each page
    def get_url(index, page_num):
        TEMPLATES = "https://upmovies.net/search-movies/{}/page-{}.html"
        return TEMPLATES.format(index, page_num)

    my_list = []  # List to store URLs not found in the database

    for page in range(1, num_pages + 1):
        url = get_url(alphabet, page)
        sleep(random.randint(1, 4))  # Random delay to avoid getting blocked
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html5lib')

        MOVIE_CON = soup.find_all('div', class_="shortItem listItem")
        my_list_UNFILTERED = [tag.find('a', href=True)['href'] for tag in MOVIE_CON if tag.find('a', href=True)]

        # Check each URL in my_list_UNFILTERED against the database
        for movie_url in my_list_UNFILTERED:
            limit = 1000  # Number of records per page in the database query
            offset = 0    # Starting point for pagination

            while True:
                # Fetch a page of URLs from the 'action_link' column in the database
                response = supabase.table('movies').select('action_link').range(offset, offset + limit - 1).execute()

                # Extract URLs from the current page of results
                db_urls = [item['action_link'] for item in response.data]
                if movie_url in db_urls:
                    break  # URL found in the database; no need to add to my_list
                
                # If less than limit results are returned, end of dataset reached
                if len(response.data) < limit:
                    my_list.append(movie_url)
                    break

                # Move to the next page in database results
                offset += limit

    return my_list  # Return list of URLs not found in the database


# Example usage
if __name__ == "__main__":
    alphabet = 'Avengers'  # You can change this to the desired search term or alphabet
    num_pages = 1  # Number of pages to search
    missing_urls = get_movie_urls_not_in_db(alphabet, num_pages)
    # Output results and populate MISSING_URL
    if missing_urls:
        print("The following URLs are NOT in the database:", missing_urls)
        with open("missing_url.json", "w") as f:
            json.dump(missing_urls, f)

               
    else:
        print("All URLs were found in the database.")
