
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








