# movie_webapp/routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import db # Import db from the initialized instance in __init__.py
# Import models, including Rating to get rated movies
from .models import User, Movie, Rating
from .forms import SignupForm, LoginForm
# Import API functions including the one for getting movie details and SEARCH
# --- MODIFIED IMPORT (Added search_movies) ---
from .api import get_top_rated_movies, get_movie_details, get_image_url, get_upcoming_movies, get_movie_credits, get_movie_videos, search_movies
# --- END MODIFIED IMPORT ---
# Import the recommendation function
from .recommender import get_recommendations_for_user # Make sure this import is here
from datetime import datetime
from sqlalchemy import desc

# Create a Blueprint for routes
routes = Blueprint('routes', __name__)

@routes.route('/')
@routes.route('/index')
def index():
    current_endpoint = request.endpoint
    if current_user.is_authenticated:
        top_rated_preview_data = get_top_rated_movies(page=1)[:10]
        upcoming_preview_data = get_upcoming_movies(page=1)[:10]

        top_rated_preview = [{
            'id': movie.get('id'),
            'title': movie.get('title'),
            'poster_url': get_image_url(movie.get('poster_path'))
        } for movie in top_rated_preview_data]

        upcoming_preview = [{
            'id': movie.get('id'),
            'title': movie.get('title'),
            'poster_url': get_image_url(movie.get('poster_path'))
        } for movie in upcoming_preview_data]


        return render_template('index.html',
                               title='Dashboard',
                               top_rated_preview=top_rated_preview,
                               upcoming_preview=upcoming_preview,
                               current_endpoint=current_endpoint)
    else:
        # Pass request.url to the login redirect so user can return after logging in
        return redirect(url_for('routes.login', next=request.url))

@routes.route('/signup', methods=['GET', 'POST'])
def signup():
    current_endpoint = request.endpoint
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('routes.login'))
    return render_template('signup.html', title='Sign Up', form=form,
                           current_endpoint=current_endpoint)

@routes.route('/login', methods=['GET', 'POST'])
def login():
    current_endpoint = request.endpoint
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('routes.login'))

        login_user(user)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('routes.index'))

    return render_template('login.html', title='Login', form=form,
                           current_endpoint=current_endpoint)

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('routes.index'))

@routes.route('/movies')
@login_required
def movies():
    current_endpoint = request.endpoint
    page = request.args.get('page', 1, type=int)
    top_movies_data = get_top_rated_movies(page=page)

    if not top_movies_data:
        flash("Could not fetch top rated movies from TMDB.", 'warning')
        movies_list = []
    else:
        movies_list = []
        movies_to_add = []
        for movie_data in top_movies_data:
            tmdb_id = movie_data.get('id')
            title = movie_data.get('title')
            poster_path = movie_data.get('poster_path')

            if tmdb_id and title:
                existing_movie = Movie.query.get(tmdb_id)
                if not existing_movie:
                    movies_to_add.append(Movie(id=tmdb_id, title=title))

                movies_list.append({
                    'id': tmdb_id,
                    'title': title,
                    'poster_url': get_image_url(movie_data.get('poster_path'))
                })

        if movies_to_add:
             db.session.add_all(movies_to_add)
             try:
                 db.session.commit()
             except Exception as e:
                 db.session.rollback()
                 current_app.logger.error(f"Error adding new movies to DB: {e}")

    has_next = len(top_movies_data) == 20 # TMDB returns max 20 per page
    has_prev = page > 1

    return render_template('movies.html',
                           title='Top Rated Movies',
                           movies=movies_list,
                           page=page,
                           has_next=has_next,
                           has_prev=has_prev,
                           current_endpoint=current_endpoint)

@routes.route('/upcoming_movies')
@login_required
def upcoming_movies():
    current_endpoint = request.endpoint
    page = request.args.get('page', 1, type=int)
    upcoming_movies_data = get_upcoming_movies(page=page)

    if not upcoming_movies_data:
        flash("Could not fetch upcoming movies from TMDB.", 'warning')
        movies_list = []
    else:
        movies_list = []
        movies_to_add = []
        for movie_data in upcoming_movies_data:
            tmdb_id = movie_data.get('id')
            title = movie_data.get('title')
            poster_path = movie_data.get('poster_path')

            if tmdb_id and title:
                 # Check if movie exists in our DB, add if not
                existing_movie = Movie.query.get(tmdb_id)
                if not existing_movie:
                    movies_to_add.append(Movie(id=tmdb_id, title=title)) # Use TMDB ID as our primary key

                movies_list.append({
                    'id': tmdb_id,
                    'title': title,
                    'poster_url': get_image_url(movie_data.get('poster_path'))
                })

        if movies_to_add:
             db.session.add_all(movies_to_add)
             try:
                 db.session.commit() # Commit any new movies added
             except Exception as e:
                 db.session.rollback()
                 current_app.logger.error(f"Error adding new upcoming movies to DB: {e}")


    has_next = len(upcoming_movies_data) == 20 # Assuming max 20 per page
    has_prev = page > 1

    return render_template('upcoming_movies.html',
                           title='Upcoming Movies',
                           movies=movies_list, # Pass the list of upcoming movies
                           page=page,
                           has_next=has_next,
                           has_prev=has_prev,
                           current_endpoint=current_endpoint)


@routes.route('/movie/<int:tmdb_id>') # Use TMDB ID as the route parameter
@login_required
def movie_detail(tmdb_id):
    current_endpoint = request.endpoint
    movie_data = get_movie_details(tmdb_id) # Fetch details from TMDB

    if not movie_data:
        flash(f"Could not fetch details for movie ID {tmdb_id}.", 'warning')
        # Determine redirect based on referrer or just go home/movies
        referrer = request.referrer
        if referrer and url_for('routes.movies') in referrer:
             return redirect(url_for('routes.movies'))
        elif referrer and url_for('routes.upcoming_movies') in referrer:
             return redirect(url_for('routes.upcoming_movies'))
        elif referrer and url_for('routes.rated_movies') in referrer: # Check rated movies page too
             return redirect(url_for('routes.rated_movies'))
        elif referrer and url_for('routes.recommendations') in referrer: # Check recommendations page
             return redirect(url_for('routes.recommendations'))
        elif referrer and url_for('routes.search') in referrer: # Also check search results page
             # Try to preserve search query if redirecting from search results
             search_query = request.args.get('query')
             if search_query:
                 return redirect(url_for('routes.search', query=search_query))
             else:
                return redirect(url_for('routes.search')) # Redirect to search page without query
        else:
             return redirect(url_for('routes.index'))

    # Update or add the movie in our local database using TMDB ID
    movie = Movie.query.get(tmdb_id)
    if not movie:
        # If it somehow wasn't added by the /movies route
        movie = Movie(id=tmdb_id, title=movie_data.get('title', 'Unknown Title'))
        db.session.add(movie)
        # Commit the movie add if it happened here
        # This check is simple; more complex logic might batch commits
        if movie in db.session.new:
            try:
                 db.session.commit()
            except Exception as e:
                 db.session.rollback()
                 current_app.logger.error(f"Error adding movie {tmdb_id} to DB in movie_detail: {e}")


    credits_data = get_movie_credits(tmdb_id)
    cast_list = []
    if credits_data and 'cast' in credits_data:
        cast_list = credits_data['cast'][:15] # Get up to the first 15 cast members


    # --- Fetch movie videos and find trailers ---
    videos_data = get_movie_videos(tmdb_id)
    primary_trailer = None # Variable to hold the main trailer object for embedding
    other_trailers = []  # List to hold other video links

    if videos_data:
        # Filter for YouTube videos first, as we'll embed/link YouTube
        youtube_videos = [
             video for video in videos_data
             if video.get('site') == 'YouTube'
        ]

        # Prioritize official trailers
        official_trailers = [v for v in youtube_videos if v.get('type') == 'Trailer' and v.get('official') is True]
        # Fallback to unofficial trailers
        unofficial_trailers = [v for v in youtube_videos if v.get('type') == 'Trailer' and (v.get('official') is False or v.get('official') is None)]
        # Fallback to any teaser
        teasers = [v for v in youtube_videos if v.get('type') == 'Teaser']
        # Fallback to other videos like featurettes, clips, etc.
        other_videos_list = [v for v in youtube_videos if v.get('type') not in ['Trailer', 'Teaser']]


        # Select the primary trailer (first official, then first unofficial, then first teaser)
        if official_trailers:
            primary_trailer = official_trailers[0]
            # Other videos are remaining official + all unofficial + all teasers + all other
            other_videos_list = official_trailers[1:] + unofficial_trailers + teasers + other_videos_list
        elif unofficial_trailers:
            primary_trailer = unofficial_trailers[0]
            # Other videos are remaining unofficial + all teasers + all other
            other_videos_list = unofficial_trailers[1:] + teasers + other_videos_list
        elif teasers:
            primary_trailer = teasers[0]
            # Other videos are remaining teasers + all other
            other_videos_list = teasers[1:] + other_videos_list
        else:
             # No trailer or teaser found, primary_trailer remains None
             other_videos_list = youtube_videos # List all found YouTube videos as 'others'


        # Limit the number of 'other' videos listed
        other_trailers = other_videos_list[:5] # Show up to 5 other video links


        # Format the 'other' video data for the template (as links to watch page)
        formatted_other_trailers = []
        for video in other_trailers:
             # Ensure 'key' exists before constructing URL
             if video.get('key'):
                 formatted_other_trailers.append({
                     'name': video.get('name', 'Video'), # Use video name, default to 'Video'
                     'url': f"https://www.youtube.com/watch?v={video['key']}" # Construct YouTube watch URL
                 })
        other_trailers = formatted_other_trailers # Replace raw data with formatted data


    movie_details = {
        'id': movie_data.get('id'),
        'title': movie_data.get('title'),
        'overview': movie_data.get('overview'),
        'poster_url': get_image_url(movie_data.get('poster_path')), # Use default size w500
        'release_date': movie_data.get('release_date'),
        'vote_average': movie_data.get('vote_average'),
        'genres': movie_data.get('genres', []) # List of dicts: [{'id': 12, 'name': 'Adventure'}]
    }

    # --- Rating Feature ---
    # Fetch the current user's existing rating for this movie
    # This will be None if no rating exists, or the Rating object (potentially with rating=0.0)
    user_rating = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=tmdb_id
    ).first()

    return render_template('movie_detail.html',
                           title=movie_details['title'],
                           movie=movie_details,
                           user_rating=user_rating,
                           cast_list=cast_list, # Pass the cast list
                           primary_trailer=primary_trailer, # <-- Pass the primary trailer object (contains key, name, etc.)
                           other_trailers=other_trailers, # <-- Pass the list of other formatted trailers (name, url)
                           get_image_url=get_image_url, # Pass function for cast photos
                           current_endpoint=current_endpoint) # Pass current endpoint


@routes.route('/rate_movie/<int:tmdb_id>', methods=['POST'])
@login_required
def rate_movie(tmdb_id):
    current_endpoint = request.endpoint # Define current_endpoint here too if needed for redirect logic
    # Check if CSRF token is valid (assuming Flask-WTF or similar is used implicitly)
    # For forms not using Flask-WTF, manual CSRF protection is required.
    # The delete forms in templates were noted as missing CSRF.
    # Adding CSRF protection to this form request handling is highly recommended.
    # Example (pseudo-code, implementation depends on your setup):
    # from flask_wtf.csrf import validate_csrf
    # from wtforms.validators import ValidationError
    # try:
    #     validate_csrf(request.form.get('csrf_token')) # Get token name from your form setup
    # except ValidationError:
    #     flash('CSRF token missing or invalid.', 'danger')
    #     return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))
    # Note: Your current template uses a plain HTML form for rating, not a Flask-WTF form object,
    # so form.hidden_tag() is NOT used on the movie_detail.html rate form.
    # Manual CSRF protection would need to be added to the form HTML and checked here.
    # Given the template structure, the form is not protected.
    # **SECURITY WARNING: The rating form on movie_detail.html is vulnerable to CSRF attacks.**
    # The below logic proceeds assuming this is accepted for now but should be fixed.


    rating_value_str = request.form.get('rating')
    movie = Movie.query.get(tmdb_id)

    # Ensure movie exists (fallback logic)
    if not movie:
        movie_data = get_movie_details(tmdb_id)
        if movie_data:
             movie = Movie(id=tmdb_id, title=movie_data.get('title', 'Unknown Title'))
             db.session.add(movie)
             try:
                 db.session.commit()
             except Exception as e:
                 db.session.rollback()
                 current_app.logger.error(f"Error adding movie {tmdb_id} on rating submit: {e}")
                 flash("An error occurred while preparing to save your rating.", 'danger')
                 return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id)) # Redirect with ID

        else:
            flash("Cannot rate a movie that doesn't exist.", 'danger')
            return redirect(url_for('routes.movies')) # Redirect to movie list

    try:
        rating_value = float(rating_value_str)
        # Validation for rating value (0.0 to 5.0)
        if not (0.0 <= rating_value <= 5.0):
             flash('Rating must be between 0 and 5.', 'warning')
             return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))

    except (ValueError, TypeError):
        flash('Invalid rating value received.', 'danger')
        return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))

    existing_rating = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=tmdb_id
    ).first()

    if existing_rating:
        existing_rating.rating = rating_value
        existing_rating.timestamp = datetime.utcnow()
        db.session.add(existing_rating)
        success_message = f'Your rating has been updated to {rating_value}.'
    else:
        new_rating = Rating(
            user_id=current_user.id,
            movie_id=tmdb_id,
            rating=rating_value,
            timestamp=datetime.utcnow()
        )
        db.session.add(new_rating)
        success_message = f'You rated this movie {rating_value}.'

    try:
        db.session.commit()
        flash(success_message, 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error saving rating for user {current_user.id}, movie {tmdb_id}: {e}")
        flash('An error occurred while saving your rating.', 'danger')

    # Redirect back to the movie detail page for this movie
    return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))


@routes.route('/delete_rating_from_detail/<int:tmdb_id>', methods=['POST'])
@login_required
def delete_rating_from_detail(tmdb_id):
     current_endpoint = request.endpoint # Define current_endpoint here too if needed for redirect logic
     # **SECURITY WARNING: This form does NOT use CSRF protection.**
     # Manual CSRF protection would be needed here if the form on movie_detail.html
     # is not using Flask-WTF and form.hidden_tag().
     # The below logic proceeds assuming this is accepted for now but should be fixed.


     movie = Movie.query.get(tmdb_id)
     if not movie:
         flash("Cannot delete rating for a movie that doesn't exist.", 'danger')
         return redirect(url_for('routes.movies'))

     rating_to_delete = Rating.query.filter_by(
         user_id=current_user.id,
         movie_id=tmdb_id
     ).first()

     if rating_to_delete:
         if rating_to_delete.user_id != current_user.id:
             # Should ideally not happen if filtered by current_user.id above,
             # but good defensive check.
             flash("You do not have permission to delete this rating.", 'danger')
             return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))

         try:
             db.session.delete(rating_to_delete)
             db.session.commit()
             flash('Your rating has been deleted.', 'success')
         except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Error deleting rating for user {current_user.id}, movie {tmdb_id}: {e}")
             flash('An error occurred while deleting your rating.', 'danger')
     else:
         flash('No rating found to delete for this movie.', 'info')

     # Redirect back to the movie detail page for this movie
     return redirect(url_for('routes.movie_detail', tmdb_id=tmdb_id))

@routes.route('/rated_movies')
@login_required
def rated_movies():
    current_endpoint = request.endpoint
    user_ratings_db = Rating.query.filter_by(user_id=current_user.id).order_by(desc(Rating.timestamp)).all()
    rated_movies_list = []

    for rating_obj in user_ratings_db:
        local_movie = rating_obj.movie
        if local_movie:
            # Fetch TMDB details to get current title and poster URL
            movie_data = get_movie_details(local_movie.id)

            if movie_data:
                rated_movies_list.append({
                    'rating_id': rating_obj.id,
                    'movie_id': local_movie.id,
                    'title': movie_data.get('title', local_movie.title), # Prefer TMDB title if available
                    'user_rating': rating_obj.rating,
                    'timestamp': rating_obj.timestamp,
                    'poster_url': get_image_url(movie_data.get('poster_path'))
                })
            else:
                 current_app.logger.warning(f"Could not fetch TMDB details for movie ID {local_movie.id} rated by user {current_user.id}. Using local title.")
                 # Fallback to using the local movie title if TMDB details fail
                 rated_movies_list.append({
                     'rating_id': rating_obj.id,
                     'movie_id': local_movie.id,
                     'title': local_movie.title + " (Details N/A)", # Indicate details couldn't be fetched
                     'user_rating': rating_obj.rating,
                     'timestamp': rating_obj.timestamp,
                     'poster_url': None # No poster if details failed
                 })

        else:
             # This case indicates an inconsistency where a Rating exists but the linked Movie does not.
             current_app.logger.error(f"Local Movie record missing for rating ID {rating_obj.id} (TMDB ID: {rating_obj.movie_id}). Skipping or showing minimal info.")
             rated_movies_list.append({
                 'rating_id': rating_obj.id,
                 'movie_id': rating_obj.movie_id,
                 'title': f"Unknown Movie (ID: {rating_obj.movie_id})", # Show ID as title fallback
                 'user_rating': rating_obj.rating,
                 'timestamp': rating_obj.timestamp,
                 'poster_url': None
             })

    return render_template('rated_movies.html',
                           title='Your Rated Movies',
                           rated_movies=rated_movies_list,
                           get_image_url=get_image_url, # Pass function if needed in template (though not used above)
                           current_endpoint=current_endpoint)

@routes.route('/delete_rating_by_id/<int:rating_id>', methods=['POST'])
@login_required
def delete_rating_by_id(rating_id):
     # **SECURITY WARNING: This form does NOT use CSRF protection.**
     # Manual CSRF protection would be needed here if the form on rated_movies.html
     # is not using Flask-WTF and form.hidden_tag().
     # The below logic proceeds assuming this is accepted for now but should be fixed.


     rating_to_delete = Rating.query.get(rating_id)

     if rating_to_delete:
         # Double check ownership even if filtered by current_user.id in query,
         # as get(rating_id) doesn't implicitly filter by user.
         if rating_to_delete.user_id != current_user.id:
             flash("You do not have permission to delete this rating.", 'danger')
             return redirect(url_for('routes.rated_movies')) # Redirect back to list

         try:
             db.session.delete(rating_to_delete)
             db.session.commit()
             flash('Your rating has been deleted.', 'success')
         except Exception as e:
             db.session.rollback()
             current_app.logger.error(f"Error deleting rating ID {rating_id} for user {current_user.id}: {e}")
             flash('An error occurred while deleting your rating.', 'danger')
     else:
         flash('Rating not found.', 'info')

     return redirect(url_for('routes.rated_movies'))

# --- Recommendations Route (Modified to split into Top 5 and Others based on has_ratings) ---
@routes.route('/recommendations')
@login_required
def recommendations():
    current_endpoint = request.endpoint
    user_db_id = current_user.id

    # Fetch rated movies from the database to determine if user has ratings
    # AND to pass rated movie IDs to the recommender if needed
    rated_movies_from_db = Rating.query.filter_by(user_id=user_db_id).all()
    rated_movie_tmdb_ids = [rating.movie_id for rating in rated_movies_from_db]

    # Flag to indicate if the user has any ratings
    has_ratings = len(rated_movies_from_db) > 0

    top5_recommendations = []
    other_recommendations = []
    total_recommendations_requested = current_app.config.get('RECOMMENDER_TOP_N', 20)
    num_top5 = 5
    # Ensure num_top5 is not more than the total requested
    num_top5 = min(num_top5, total_recommendations_requested)

    # --- Conditional logic based on whether the user has ratings ---
    if has_ratings:
        # User has ratings, attempt to get personalized recommendations
        recommended_items_with_scores = get_recommendations_for_user(
            user_db_id,
            rated_movie_tmdb_ids,
            num_recommendations=total_recommendations_requested
        )

        # Process personalized recommendations if any were returned by the recommender
        if recommended_items_with_scores:
            all_formatted_recommendations = []
            for item_data in recommended_items_with_scores:
                tmdb_id = item_data.get('tmdb_id')
                score = item_data.get('score')

                if tmdb_id:
                     # Fetch full details from TMDB for display
                     movie_data = get_movie_details(tmdb_id)
                     if movie_data:
                         # Append the formatted movie details including the predicted score
                         all_formatted_recommendations.append({
                             'id': movie_data.get('id'), # Use TMDB ID
                             'title': movie_data.get('title'),
                             'poster_url': get_image_url(movie_data.get('poster_path')),
                             'predicted_score': score # Include the predicted score
                         })
                     else:
                         current_app.logger.warning(f"Could not fetch TMDB details for recommended movie ID {tmdb_id}")
                else:
                     current_app.logger.warning("Recommended item_data missing tmdb_id.")

            # Split into Top 5 and Others *only if* we got and processed recommendations
            top5_recommendations = all_formatted_recommendations[:num_top5]
            other_recommendations = all_formatted_recommendations[num_top5:total_recommendations_requested]

        else:
            # User has ratings, but the recommender returned an empty list or encountered an error.
            # top5_recommendations and other_recommendations remain empty lists (as initialized).
            current_app.logger.warning(f"Recommender returned no results for user {user_db_id} despite having ratings.")
            # The template will now explicitly check the `has_ratings` flag first.
            # If has_ratings is True but lists are empty, the final 'else' block in the template handles it.

    else:
        # User has no ratings. top5_recommendations and other_recommendations remain empty lists.
        # We explicitly do NOT call the recommender or fetch any movies.
        current_app.logger.info(f"User {user_db_id} has no ratings. Skipping recommendation generation.")
        pass # has_ratings is already False, and lists are empty

    # Pass the lists (which might be empty) and the has_ratings flag to the template
    return render_template('recommendations.html',
                           title='Recommended Movies',
                           top5_recommendations=top5_recommendations,
                           other_recommendations=other_recommendations,
                           has_ratings=has_ratings, # Pass the flag
                           current_endpoint=current_endpoint)


# --- Search Route ---
@routes.route('/search')
@login_required # Only authenticated users can search
def search():
    current_endpoint = request.endpoint
    query = request.args.get('query') # Get the search query from the URL parameter
    page = request.args.get('page', 1, type=int) # Get the page number

    # Check if a query was actually provided
    if not query or query.strip() == "":
        flash("Please enter a movie title to search for.", 'warning')
        # Redirect back to the previous page or a default page like index or movies
        # Using request.referrer might be complex, simpler to redirect to a known page.
        return redirect(url_for('routes.movies')) # Or routes.index

    # Fetch search results from TMDB API
    search_results_data = search_movies(query.strip(), page=page) # Use strip() to remove leading/trailing whitespace

    movies_list = []
    total_results = 0
    total_pages = 0

    if search_results_data and search_results_data.get('results') is not None: # Check for 'results' key existence
        # Process the list of movie results
        movies_list = []
        movies_to_add = [] # Keep track of movies to add to local DB

        for movie_data in search_results_data.get('results'):
            tmdb_id = movie_data.get('id')
            title = movie_data.get('title')

            # Ensure we have essential data before processing
            if tmdb_id and title:
                # Check if movie exists in our DB, add if not
                existing_movie = Movie.query.get(tmdb_id)
                if not existing_movie:
                    movies_to_add.append(Movie(id=tmdb_id, title=title)) # Use TMDB ID as our primary key

                # Format movie data for the template
                movies_list.append({
                    'id': tmdb_id,
                    'title': title,
                    'poster_url': get_image_url(movie_data.get('poster_path')),
                    # Add other potentially useful search result info if needed, e.g., release_date
                    # 'release_date': movie_data.get('release_date'),
                    # 'vote_average': movie_data.get('vote_average'),
                })

        # Add any new movies found in search results to the local DB
        if movies_to_add:
            db.session.add_all(movies_to_add)
            try:
                db.session.commit() # Commit any new movies added
                current_app.logger.info(f"Added {len(movies_to_add)} new movies to DB from search results.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error adding new movies from search results to DB: {e}")


        # Get total results and pages for pagination
        total_results = search_results_data.get('total_results', 0)
        total_pages = search_results_data.get('total_pages', 0)

        if not movies_list and total_results > 0:
             # This case is unlikely if total_results > 0 and results key exists,
             # but good defensive check.
             flash(f"Found {total_results} matches, but could not process the results.", 'warning')
        elif not movies_list and total_results == 0:
             flash(f"No movies found for your search query '{query}'.", 'info')
        # If search_results_data is None (API error), the initial check handles the flash message.


    # Pagination logic based on total_pages from API
    has_next = page < total_pages
    has_prev = page > 1

    return render_template('search_results.html',
                           title=f'Search Results for "{query}"',
                           movies=movies_list,
                           query=query, # Pass the original query back for links and display
                           page=page,
                           has_next=has_next,
                           has_prev=has_prev,
                           current_endpoint=current_endpoint)

# Helper route for testing database setup/viewing data (Optional)
# @routes.route('/db_check')
# def db_check():
#     users = User.query.all()
#     movies = Movie.query.all()
#     ratings = Rating.query.all()
#     # Format timestamps for display
#     formatted_ratings = [
#         f'<Rating User {r.user_id} Movie {r.movie_id} Value {r.rating} Time {r.timestamp.strftime("%Y-%m-%d %H:%M:%S")}>' if r.timestamp else f'<Rating User {r.user_id} Movie {r.movie_id} Value {r.rating}>'
#         for r in ratings
#     ]
#     return f"Users: {users}<br>Movies: {movies}<br>Ratings: {formatted_ratings}"""