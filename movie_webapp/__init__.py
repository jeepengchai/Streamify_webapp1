# movie_webapp/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config # Import Config from your config file
from . import recommender # Make sure this import is here
import torch # Import torch (needed by recommender)
# Don't import models yet

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'routes.login' # 'routes' is the blueprint name, 'login' is the function name
login_manager.login_message_category = 'info' # Style flash messages

# Import models AFTER db and login_manager are instantiated
# This ensures the models file has access to db and allows us
# to import User specifically for the user_loader
from .models import User # <-- Import User here

# Flask-Login requirement: function to load a user from the user ID
@login_manager.user_loader
def load_user(user_id):
    # user_id is passed as a string, convert to int
    return User.query.get(int(user_id))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # --- Load Recommender Model and Maps ---
    # Call the loading function and store the returned dictionary in app.config
    # **Ensure this line is present and correct**
    app.config['recommender_loaded_data'] = recommender.load_recommender_model(app)
    # Check if model loading was successful
    if app.config['recommender_loaded_data'].get('model') is None:
        app.logger.warning("Recommender model failed to load or is incomplete. Personalized recommendations will not be available.")
    # -----------------------------------------


    # Import and register routes blueprint
    # from .routes import routes as routes_blueprint # This was the old way
    # Use absolute import within package for clarity
    from movie_webapp.routes import routes as routes_blueprint # Use absolute import here
    app.register_blueprint(routes_blueprint)

    # Ensure database tables are created within app context
    # This happens *after* models are imported above and associated with db
    with app.app_context():
        db.create_all()

    return app


# Note: The 'from . import models' is no longer needed at the very bottom
# because we explicitly imported User and implicitly load other models when
# db.create_all() is called later. The essential part is that the models
# are defined and associated with the 'db' instance when create_all runs.