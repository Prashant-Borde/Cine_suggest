import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from .models import Movie
import requests


# Path to store the trained model
MODEL_FILE_PATH = '/Users/prashantborde/Desktop/projects/cine_suggest/app/similarity_model.pkl'

def create_and_save_model():
    # Fetch all movies from the database
    movies = Movie.objects.all()
    data = pd.DataFrame([{
        'movie_title': movie.movie_title,
        'comb': movie.comb
    } for movie in movies])

    # Create a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])

    # Create a similarity score matrix
    sim = cosine_similarity(count_matrix)

    # Save the data and similarity matrix using pickle
    with open(MODEL_FILE_PATH, 'wb') as model_file:
        pickle.dump((data, sim), model_file)

    print("Model saved successfully!")

# Load the saved model
def load_model():
    with open(MODEL_FILE_PATH, 'rb') as model_file:
        data, sim = pickle.load(model_file)
    return data, sim

def fetch_poster_by_title(movie_title):
    # Function to fetch the poster from TMDb
    def fetch_from_tmdb():
        api_key = 'YOUR_TMDB_API_KEY'  # Replace with your actual TMDb API key
        # url = f'https://api.themoviedb.org/3/search/movie?api_key=db3b42ad8b49e299ecc879fc2539fc90&query={movie_title}'
        url = f'https://api.themoviedb.org/3/search/movie?api_key=cebcaf3f979a920e1ea776ce5c06cbc7&query={movie_title}'
        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    poster_path = data['results'][0].get('poster_path')
                    if poster_path:
                        return f'https://image.tmdb.org/t/p/w500{poster_path}'
            return None
        except Exception as e:
            print(f"Error fetching from TMDb: {e}")
            response = requests.get(url, timeout=60)

            return None



    # Function to fetch the poster from OMDb
    # http://www.omdbapi.com/?i=tt3896198&apikey=82e3bf68
    def fetch_from_omdb():
        api_key = 'YOUR_OMDB_API_KEY'  # Replace with your actual OMDb API key
        url = f"http://www.omdbapi.com/?t={movie_title}&apikey=82e3bf68"

        try:
            response = requests.get(url,timeout=60)
            if response.status_code == 200:
                data = response.json()
                if 'Poster' in data and data['Poster'] != 'N/A':
                    return data['Poster']
            return None
        except Exception as e:
            print(f"Error fetching from OMDb: {e}")
            return None

    # Try to fetch from TMDb first, then fallback to OMDb
    poster = fetch_from_tmdb()
    if not poster:
        poster = fetch_from_omdb()

    return poster

def recommend_movie(movie_title):
    # Load the trained model
    data, sim = load_model()

    movie_title = movie_title.lower()
    if movie_title not in data['movie_title'].str.lower().values:
        return 'This movie is not in our database.\nPlease check if you spelled it correctly.'
    else:
        i = data.loc[data['movie_title'].str.lower() == movie_title].index[0]
        lst = list(enumerate(sim[i]))
        lst = sorted(lst, key=lambda x: x[1], reverse=True)
        lst = lst[1:13]  # Get top 30 recommendations

        recommendations = []
        recommended_movies_posters = []

        for index, _ in lst:
            movie_title = data['movie_title'][index]
            recommendations.append(movie_title)
            poster = fetch_poster_by_title(movie_title)  # Fetch the poster
            recommended_movies_posters.append(poster)

        return recommendations, recommended_movies_posters
