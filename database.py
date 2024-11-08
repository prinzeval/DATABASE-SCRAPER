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

engine.say("NAHIDA TELL VALENTINE THE CODE HAS FINISHED SUCCESSFULLY   PLEASE NAHIDA TELL VALENTINE THE CODE HAS FINISHED ")

# Wait for the speech to complete
engine.runAndWait()

