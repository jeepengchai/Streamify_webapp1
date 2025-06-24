import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env')) # Load variables from .env

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
    # Base URL for TMDB API
    TMDB_API_BASE_URL = 'https://api.themoviedb.org/3'
    # Base URL for TMDB images (change size 'w500' as needed)
    TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w500'

    # --- Recommender Model Configuration ---
    # **VERIFY THESE PATHS**
    MODEL_PATH = os.path.join(basedir, 'model.pth')
    USER_MAP_PATH = os.path.join(basedir, 'user_map.pkl')
    ITEM_MAP_PATH = os.path.join(basedir, 'item_map.pkl') # This should map ML_ID <-> Model Index
    ML_LINKS_PATH = os.path.join(basedir, 'links.csv') # Path to MovieLens links.csv (ML_ID <-> TMDB_ID)

    # **VERIFY THESE PARAMETERS**
    RECOMMENDER_NUM_USERS = 6041
    RECOMMENDER_NUM_ITEMS = 193610
    RECOMMENDER_EMBEDDING_SIZE = 32
    RECOMMENDER_LAYER_DIMS = [64, 32, 16]
    RECOMMENDER_TOP_N = 20 # Number of recommendations to show