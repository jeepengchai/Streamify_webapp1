# movie_webapp/api.py
import requests
from flask import current_app

# Helper function to make TMDB API requests
def _make_tmdb_request(endpoint, params=None):
    base_url = current_app.config['TMDB_API_BASE_URL']
    api_key = current_app.config['TMDB_API_KEY']

    if not api_key:
        current_app.logger.error("TMDB_API_KEY is not set in config!")
        return None # Or raise an error

    url = f"{base_url}/{endpoint}"
    default_params = {'api_key': api_key}
    if params:
        default_params.update(params)

    try:
        response = requests.get(url, params=default_params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"TMDB API request failed for endpoint {endpoint}: {e}")
        return None

def get_top_rated_movies(page=1):
    """Fetches a list of top-rated movies from TMDB."""
    data = _make_tmdb_request('movie/top_rated', {'page': page})
    # TMDB returns results in a 'results' key
    return data.get('results', []) if data else []

def get_movie_details(movie_id):
    """Fetches details for a specific movie by its TMDB ID."""
    data = _make_tmdb_request(f'movie/{movie_id}')
    return data if data else None

# --- Function to get movie credits (cast and crew) ---
def get_movie_credits(movie_id):
    """Fetches cast and crew for a specific movie by its TMDB ID."""
    data = _make_tmdb_request(f'movie/{movie_id}/credits')
    return data if data else None

# --- Function to get movie videos ---
def get_movie_videos(movie_id):
    """Fetches videos (including trailers) for a specific movie by its TMDB ID."""
    data = _make_tmdb_request(f'movie/{movie_id}/videos')
    # The videos endpoint returns a 'results' list of video objects
    return data.get('results', []) if data else []
# ----------------------------------------

def get_upcoming_movies(page=1):
    """Fetches a list of upcoming movies from TMDB."""
    data = _make_tmdb_request('movie/upcoming', {'page': page})
    return data.get('results', []) if data else []

# --- NEW Function to search movies ---
def search_movies(query, page=1):
    """Searches for movies on TMDB based on a query."""
    if not query:
        return None # Or return {'results': [], 'total_results': 0, 'total_pages': 0}

    params = {'query': query, 'page': page}
    data = _make_tmdb_request('search/movie', params)
    # The search endpoint returns results, total_results, and total_pages
    return data if data else {'results': [], 'total_results': 0, 'total_pages': 0}
# ----------------------------------------


def get_image_url(path, size='w500'): # Added optional size parameter
    """Constructs a full image URL from a TMDB path (e.g., poster_path, profile_path)."""
    if not path:
        return None

    # Ensure the base URL ends without a size segment
    base_image_url = current_app.config.get('TMDB_IMAGE_BASE_URL')
    if base_image_url and base_image_url.endswith('/'):
         base_image_url = base_image_url[:-1] # Remove trailing slash if present
    # Handle if base is just /t/p, which doesn't have a base URL before it
    if base_image_url and base_image_url.endswith('/t/p'):
         # This path should be handled by just adding /size/path
         pass # Keep base_image_url as is if it's just the /t/p part
    elif base_image_url: # If it's a full base URL like http://image.tmdb.org/t/p
         base_image_url = base_image_url.rsplit('/t/p', 1)[0] # Get base part before /t/p


    if not base_image_url:
         current_app.logger.warning("TMDB_IMAGE_BASE_URL not set correctly in config!")
         # Fallback to hardcoded base if config is bad
         base_image_url = 'https://image.tmdb.org' # Or handle error differently


    # TMDB image paths often start with '/', but the URL construction needs it
    # Ensure the path starts with '/', otherwise the format is wrong.
    # However, the get_image_url function was built assuming the path
    # might not have a leading slash, so keep lstrip for safety based on existing code.
    # More robust: check TMDB configuration endpoint /configuration for image base_url structure.
    # For now, trust the existing logic combined with lstrip.


    # Construct URL
    # Use path.lstrip('/') to ensure path starts correctly after size
    # Corrected URL format slightly based on typical TMDB structure /t/p/size/path
    # Assuming TMDB_IMAGE_BASE_URL is 'https://image.tmdb.org/t/p/w500' (already has size)
    # If config is 'https://image.tmdb.org/t/p/w500', then this function should ideally just replace size.
    # Let's adjust the function logic slightly to handle this common case.

    config_base_url = current_app.config.get('TMDB_IMAGE_BASE_URL')
    if config_base_url:
         # Assume config_base_url is like 'https://image.tmdb.org/t/p/w500'
         # Replace the size part and append the specific path
         # Find the position of '/t/p/'
         t_p_index = config_base_url.find('/t/p/')
         if t_p_index != -1:
              base_part = config_base_url[:t_p_index + len('/t/p/')] # 'https://image.tmdb.org/t/p/'
              return f"{base_part}{size}/{path.lstrip('/')}"
         else:
              # Fallback if config_base_url doesn't contain '/t/p/'
              current_app.logger.warning(f"TMDB_IMAGE_BASE_URL config '{config_base_url}' does not contain '/t/p/'. Falling back to simpler format.")
              return f"{config_base_url}/{size}/{path.lstrip('/')}" # May or may not work depending on TMDB changes

    else:
         # Fallback if config is completely missing
         current_app.logger.warning("TMDB_IMAGE_BASE_URL not set in config! Falling back to hardcoded base.")
         return f'https://image.tmdb.org/t/p/{size}/{path.lstrip("/")}'