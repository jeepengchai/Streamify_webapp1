# create_mappings.py
import pandas as pd
import pickle
import os

# --- Configuration ---
# Adjust these paths relative to where you run this script
# Assuming you place ratings.csv, links.csv, and this script
# in the directory ABOVE your movie_webapp package.
# If you place ratings.csv/links.csv INSIDE movie_webapp, adjust paths accordingly.
MOVIEWEBAPP_DIR = 'movie_webapp' # Name of your Flask package directory
RATINGS_CSV_PATH = os.path.join(MOVIEWEBAPP_DIR, 'ratings_preprocessed_D4.csv') # Path to your training ratings.csv
LINKS_CSV_PATH = os.path.join(MOVIEWEBAPP_DIR, 'links.csv') # Path to your training links.csv

# Output paths for the mapping files (will be saved INSIDE movie_webapp)
USER_MAP_PKL_PATH = os.path.join(MOVIEWEBAPP_DIR, 'user_map.pkl')
ITEM_MAP_PKL_PATH = os.path.join(MOVIEWEBAPP_DIR, 'item_map.pkl')
# ---------------------

def create_and_save_mappings(ratings_csv_path, links_csv_path, user_map_output_path, item_map_output_path):
    """
    Creates user and item mapping files from MovieLens data.

    Args:
        ratings_csv_path (str): Path to the MovieLens ratings.csv file.
        links_csv_path (str): Path to the MovieLens links.csv file.
        user_map_output_path (str): Path to save the user_map.pkl file.
        item_map_output_path (str): Path to save the item_map.pkl file.
    """
    print(f"Loading data from {ratings_csv_path} and {links_csv_path}...")

    try:
        ratings_df = pd.read_csv(ratings_csv_path)
        links_df = pd.read_csv(links_csv_path)
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}")
        print("Please ensure ratings.csv and links.csv from your training dataset are in the correct directory.")
        return
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return

    print("Data loaded successfully.")

    # --- Create User Map ---
    print("Creating user map...")
    unique_users = ratings_df['userId'].unique()
    unique_users.sort() # Optional: Sort for consistent mapping order
    user_map = {original_id: contiguous_index for contiguous_index, original_id in enumerate(unique_users)}
    print(f"Created map for {len(user_map)} unique users.")

    # --- Create Item Maps (MovieLens ID <-> Model Index) ---
    print("Creating item maps (MovieLens ID <-> Model Index)...")
    unique_ml_movies = ratings_df['movieId'].unique()
    unique_ml_movies.sort() # Optional: Sort for consistent mapping order
    item_map_ml_to_model = {original_ml_id: contiguous_index for contiguous_index, original_ml_id in enumerate(unique_ml_movies)}
    item_map_model_to_ml = {contiguous_index: original_ml_id for original_ml_id, contiguous_index in item_map_ml_to_model.items()}
    print(f"Created maps for {len(item_map_ml_to_model)} unique MovieLens movies from ratings.")

    # --- Create MovieLens <-> TMDB ID Maps (using links.csv) ---
    print("Creating MovieLens <-> TMDB maps...")
    # Drop rows where tmdbId is missing or NaN
    links_df = links_df.dropna(subset=['tmdbId'])
    # Ensure tmdbId is integer type (might be float if there were NaNs)
    links_df['tmdbId'] = links_df['tmdbId'].astype(int)

    # Create the dictionaries
    ml_to_tmdb_map = pd.Series(links_df.tmdbId.values, index=links_df.movieId).to_dict()
    tmdb_to_ml_map = pd.Series(links_df.movieId.values, index=links_df.tmdbId).to_dict()
    print(f"Created {len(ml_to_tmdb_map)} ML_ID <-> TMDB_ID mappings from links.csv.")


    # --- Save Mappings ---
    print("Saving mappings...")

    # Save user map to user_map.pkl
    try:
        with open(user_map_output_path, 'wb') as f:
            pickle.dump(user_map, f)
        print(f"User map saved to {user_map_output_path}")
    except Exception as e:
        print(f"Error saving user map: {e}")

    # Save all item-related maps to item_map.pkl
    # Saving all related maps in one file is convenient
    item_mappings = {
        'ml_to_model': item_map_ml_to_model, # MovieLens ID -> Model Index
        'model_to_ml': item_map_model_to_ml, # Model Index -> MovieLens ID
        'ml_to_tmdb': ml_to_tmdb_map,       # MovieLens ID -> TMDB ID
        'tmdb_to_ml': tmdb_to_ml_map         # TMDB ID -> MovieLens ID
    }
    try:
        with open(item_map_output_path, 'wb') as f:
            pickle.dump(item_mappings, f)
        print(f"Item maps saved to {item_map_output_path}")
    except Exception as e:
        print(f"Error saving item maps: {e}")

    print("Mapping generation complete.")


# --- Run the script ---
if __name__ == "__main__":
    create_and_save_mappings(RATINGS_CSV_PATH, LINKS_CSV_PATH, USER_MAP_PKL_PATH, ITEM_MAP_PKL_PATH)