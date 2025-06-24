# run.py
from movie_webapp import create_app # Import the create_app function from your package

app = create_app()

#if __name__ == '__main__':
#    app.run(debug=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)