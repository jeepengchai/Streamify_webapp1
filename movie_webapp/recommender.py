# movie_webapp/recommender.py
import torch
import torch.nn as nn
import pickle
import os
import csv
from flask import current_app

# --- 1. Define the MLP model architecture ---
class MLP(nn.Module):
    def __init__(self, num_users, num_items, embedding_size, layer_dims):
        super(MLP, self).__init__()
        self.user_embedding = nn.Embedding(num_users, embedding_size)
        self.item_embedding = nn.Embedding(num_items, embedding_size)

        first_layer_input = embedding_size * 2

        layers = []
        input_dim = first_layer_input
        for output_dim in layer_dims:
            layers.append(nn.Linear(input_dim, output_dim))
            layers.append(nn.ReLU())
            input_dim = output_dim

        self.mlp_layers = nn.Sequential(*layers)
        self.output_layer = nn.Linear(layer_dims[-1], 1)
        self.sigmoid = nn.Sigmoid() # Using Sigmoid to output a score between 0 and 1
        self._init_weights()

    def _init_weights(self):
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.item_embedding.weight, std=0.01)
        for layer in self.mlp_layers:
            if isinstance(layer, nn.Linear):
                nn.init.xavier_uniform_(layer.weight)
        nn.init.xavier_uniform_(self.output_layer.weight)

    def forward(self, user, item):
        user_emb = self.user_embedding(user)
        item_emb = self.item_embedding(item)
        x = torch.cat([user_emb, item_emb], dim=-1)
        x = self.mlp_layers(x)
        x = self.output_layer(x)
        return self.sigmoid(x).view(-1) # Return a 1D tensor of scores


# --- 2. Function to load the trained model and mappings ---
def load_recommender_model(app):
    """Loads the trained NCF model and mapping files."""
    model_path = app.config.get('MODEL_PATH')
    user_map_path = app.config.get('USER_MAP_PATH')
    item_map_path = app.config.get('ITEM_MAP_PATH') # ML_ID <-> Model Index + ML_ID <-> TMDB_ID maps here

    num_users = app.config.get('RECOMMENDER_NUM_USERS')
    num_items = app.config.get('RECOMMENDER_NUM_ITEMS')
    embedding_size = app.config.get('RECOMMENDER_EMBEDDING_SIZE')
    layer_dims = app.config.get('RECOMMENDER_LAYER_DIMS')

    model = None
    user_map = None
    item_map_ml_to_model = None
    item_map_model_to_ml = None
    tmdb_to_ml_map = {}
    ml_to_tmdb_map = {}

    # --- Check if core files exist before attempting to load ---
    core_files = {'Model file': model_path, 'User map': user_map_path, 'Item map': item_map_path}
    missing_core_files = [name for name, path in core_files.items() if not path or not os.path.exists(path)]

    if missing_core_files:
        app.logger.error(f"Missing core recommender files: {', '.join(missing_core_files)}. Recommendations will not be available.")
        return { 'model': None, 'user_map': None, 'item_map_ml_to_model': {},
                 'item_map_model_to_ml': {}, 'tmdb_to_ml_map': {}, 'ml_to_tmdb_map': {} }

    try:
        # Load user map (Flask DB User ID -> Model Index)
        with open(user_map_path, 'rb') as f:
            user_map = pickle.load(f)
        app.logger.info(f"Loaded user map from {user_map_path} with {len(user_map)} entries.")

        # Load item map (ML_ID <-> Model Index + ML_ID <-> TMDB_ID)
        with open(item_map_path, 'rb') as f:
             item_maps = pickle.load(f)
             item_map_ml_to_model = item_maps.get('ml_to_model', {})
             item_map_model_to_ml = item_maps.get('model_to_ml', {})
             ml_to_tmdb_map = item_maps.get('ml_to_tmdb', {})
             tmdb_to_ml_map = item_maps.get('tmdb_to_ml', {})

        # Check if essential item maps were loaded
        if not item_map_ml_to_model or not item_map_model_to_ml or len(item_map_ml_to_model) != len(item_map_model_to_ml) or not ml_to_tmdb_map or not tmdb_to_ml_map:
             app.logger.error(f"Incomplete or incorrect item maps loaded from {item_map_path}. Ensure it contains 'ml_to_model', 'model_to_ml', 'ml_to_tmdb', and 'tmdb_to_ml'. Recommendations may be limited or unavailable.")
             item_map_ml_to_model = {}
             item_map_model_to_ml = {}
             ml_to_tmdb_map = {}
             tmdb_to_ml_map = {}
        else:
             app.logger.info(f"Loaded item maps from {item_map_path}. Model has {len(item_map_ml_to_model)} items, {len(tmdb_to_ml_map)} ML<->TMDB links.")


        # Instantiate model
        model = MLP(num_users, num_items, embedding_size, layer_dims)

        # Load the trained state dictionary
        app.logger.warning("Loading model with weights_only=False due to potential compatibility issues. Ensure you trust the source of model.pth.")
        # Use map_location='cpu' for loading on machines without GPU
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'), weights_only=False)

        model_state_dict = checkpoint.get('model_state_dict')

        if model_state_dict is None:
             app.logger.error(f"Expected key 'model_state_dict' not found in the loaded dictionary from {model_path}.")
             raise KeyError(f"Expected key 'model_state_dict' not found in checkpoint file {model_path}")

        model.load_state_dict(model_state_dict)

        model.eval() # Set model to evaluation mode
        app.logger.info(f"Loaded model state dictionary from {model_path}.")

    except Exception as e:
        app.logger.error(f"Error loading recommender components: {e}")
        model = None

    loaded_data = {
        'model': model,
        'user_map': user_map, # Flask DB User ID -> Model Index
        'item_map_ml_to_model': item_map_ml_to_model, # ML ID -> Model Index
        'item_map_model_to_ml': item_map_model_to_ml, # Model Index -> ML ID
        'tmdb_to_ml_map': tmdb_to_ml_map, # TMDB ID -> ML ID
        'ml_to_tmdb_map': ml_to_tmdb_map # ML ID -> TMDB ID
    }

    if loaded_data['model'] is None or not loaded_data['user_map'] or not loaded_data['item_map_ml_to_model'] or not loaded_data['item_map_model_to_ml'] or not loaded_data['tmdb_to_ml_map'] or not loaded_data['ml_to_tmdb_map']:
         app.logger.warning("Recommender system is incomplete or failed to load all components. Recommendations may not function correctly.")


    return loaded_data


# --- 3. Function to get recommendations for a user ---
def get_recommendations_for_user(user_db_id, rated_movie_tmdb_ids, num_recommendations=20):
    """
    Generates personalized movie recommendations for a user using the loaded NCF (MLP) model.

    Args:
        user_db_id (int): The database ID of the user.
        rated_movie_tmdb_ids (list): A list of TMDB IDs of movies the user has already rated.
        num_recommendations (int): The desired number of recommendations.

    Returns:
        list: A list of dictionaries, where each dictionary contains 'tmdb_id' and 'score'.
              Returns empty list if recommendations cannot be generated or found.
    """
    loaded_data = current_app.config.get('recommender_loaded_data')
    if not loaded_data:
        current_app.logger.error("Recommender data not found in app config.")
        return []

    model = loaded_data.get('model')
    user_map = loaded_data.get('user_map')
    item_map_ml_to_model = loaded_data.get('item_map_ml_to_model')
    item_map_model_to_ml = loaded_data.get('item_map_model_to_ml')
    tmdb_to_ml_map = loaded_data.get('tmdb_to_ml_map')
    ml_to_tmdb_map = loaded_data.get('ml_to_tmdb_map')

    if model is None or user_map is None or item_map_ml_to_model is None or item_map_model_to_ml is None or not tmdb_to_ml_map or not ml_to_tmdb_map:
        current_app.logger.warning("Recommender components are missing or incomplete. Cannot generate recommendations.")
        return []

    user_model_id = user_map.get(user_db_id)

    if user_model_id is None:
        current_app.logger.warning(f"User ID {user_db_id} not found in user map. Returning empty recommendations.")
        return []

    all_item_model_ids = list(item_map_model_to_ml.keys())
    if not all_item_model_ids:
         current_app.logger.warning("Item map (Model Index -> ML ID) is empty. Cannot generate recommendations.")
         return []

    rated_item_model_ids = set()
    for tmdb_id in rated_movie_tmdb_ids:
         ml_id = tmdb_to_ml_map.get(tmdb_id)
         if ml_id is not None:
              model_id = item_map_ml_to_model.get(ml_id)
              if model_id is not None:
                   rated_item_model_ids.add(model_id)

    # Create tensors for prediction
    user_tensor = torch.tensor([user_model_id] * len(all_item_model_ids), dtype=torch.long)
    item_tensor = torch.tensor(all_item_model_ids, dtype=torch.long)

    # Optional: Move tensors/model to GPU if available
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # user_tensor = user_tensor.to(device)
    # item_tensor = item_tensor.to(device)
    # model.to(device)

    with torch.no_grad():
        model.eval()
        predictions = model(user_tensor, item_tensor)

    # Pair item model IDs with their scores
    item_scores = list(zip(all_item_model_ids, predictions.tolist()))

    # Sort by predicted score descending
    sorted_item_scores = sorted(item_scores, key=lambda item: item[1], reverse=True)

    recommended_items_with_scores = [] # List to hold {'tmdb_id': ..., 'score': ...} dictionaries

    for item_model_id, score in sorted_item_scores:
        # Skip if the movie has already been rated by the user
        if item_model_id not in rated_item_model_ids:
            # Translate Model Index -> ML ID -> TMDB ID
            ml_id = item_map_model_to_ml.get(item_model_id)
            if ml_id is not None:
                 tmdb_id = ml_to_tmdb_map.get(ml_id)
                 if tmdb_id is not None:
                     # Found a recommended TMDB ID, add it with its score
                     recommended_items_with_scores.append({'tmdb_id': tmdb_id, 'score': score})

                     # Stop when we have enough recommendations
                     if len(recommended_items_with_scores) >= num_recommendations:
                         break

    if len(recommended_items_with_scores) < num_recommendations:
         current_app.logger.warning(f"Only found {len(recommended_items_with_scores)} recommendations for user {user_db_id} after filtering rated and unmapped items.")

    return recommended_items_with_scores