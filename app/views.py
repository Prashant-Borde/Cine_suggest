from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from cine_suggest.settings import STATIC_URL

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

from .models import Movie
from .serializers import MovieSerializer, UserSerializer

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.decorators import login_required
from .forms import FeedbackForm
import requests
from requests.exceptions import ConnectionError
import time

import random
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.shortcuts import render, get_object_or_404
  





@login_required
def home_page(request):
    return render(request, 'app/home.html')


def register_view(request):
    if request.method == 'POST':
        form_data = {
            'email': request.POST.get('email'),
            'username': request.POST.get('username'),
            'password': request.POST.get('password')
        }
        serializer = UserSerializer(data=form_data)
        
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('home')
        else:
            messages.error(request, serializer.errors)
    return render(request, 'app/register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password.")
    
    return render(request, 'app/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def create_sim():
    # Fetch all movies from the database
    movies = Movie.objects.all()
    data = pd.DataFrame([{
        'movie_title': movie.movie_title,
        'comb': movie.comb
    } for movie in movies])
    
    # Creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    
    # Creating a similarity score matrix
    sim = cosine_similarity(count_matrix)
    return data, sim

def rcmd(movie_title):
    movie_title = movie_title.lower()
    data, sim = create_sim()

    if movie_title not in data['movie_title'].str.lower().values:
        return 'This movie is not in our database.\nPlease check if you spelled it correctly.'
    else:
        i = data.loc[data['movie_title'].str.lower() == movie_title].index[0]
        lst = list(enumerate(sim[i]))
        lst = sorted(lst, key=lambda x: x[1], reverse=True)
        lst = lst[1:31]  # Get top 10 recommendations

        # Prepare lists for recommended movies and their posters
        recommendations = []
        recommended_movies_posters = []

        for index, _ in lst:
            movie_title = data['movie_title'][index]
            recommendations.append(movie_title)
            poster = fetch_poster_by_title(movie_title)  # Fetch the poster using the title
            recommended_movies_posters.append(poster)

        return recommendations, recommended_movies_posters








#working code
# def rcmd(movie_title):
#     movie_title = movie_title.lower()
#     data, sim = create_sim()

#     if movie_title not in data['movie_title'].str.lower().values:
#         return 'This movie is not in our database.\nPlease check if you spelled it correctly.'
#     else:
#         i = data.loc[data['movie_title'].str.lower() == movie_title].index[0]
#         lst = list(enumerate(sim[i]))
#         lst = sorted(lst, key=lambda x: x[1], reverse=True)
#         lst = lst[1:11]  # Get top 10 recommendations

#         # Prepare lists for recommended movies and posters
#         recommendations = []
#         recommended_movies_posters = []

#         for index, _ in lst:
#             movie_title = data['movie_title'][index]
#             recommendations.append(movie_title)
#             poster = fetch_poster(index)  # Fetch the poster for each recommended movie
#             recommended_movies_posters.append(poster)

#         return recommendations, recommended_movies_posters










# def rcmd(movie_title):
#     movie_title = movie_title.lower()
#     data, sim = create_sim()
    
#     if movie_title not in data['movie_title'].str.lower().values:
#         return 'This movie is not in our database.\nPlease check if you spelled it correctly.'
#     else:
#         i = data.loc[data['movie_title'].str.lower() == movie_title].index[0]
#         lst = list(enumerate(sim[i]))
#         lst = sorted(lst, key=lambda x: x[1], reverse=True)
#         lst = lst[1:11]  # Get top 10 recommendations

#         # Making an empty list that will contain all 10 movie recommendations
#         recommendations = []
#         for index, _ in lst:
#             recommendations.append(data['movie_title'][index])
#             recomended_movies_posters.append(fetch_poster(i[0]))
#         return recommendations,recomended_movies_posters

# @login_required
# def recommend(request):
#     movie = request.GET.get('movie')
#     recommendations = rcmd(movie)
#     movie_display = movie.upper()
    
#     if isinstance(recommendations, str):
#         return render(request, 'app/recommend.html', {'movie': movie_display, 'r': recommendations, 't': 's'})
#     else:
#         return render(request, 'app/recommend.html', {'movie': movie_display, 'r': recommendations, 't': 'l'})

# app/views.py

@login_required
def recommend(request):
    movie = request.GET.get('movie')
    recommendations, posters = rcmd(movie)  # Get both movie titles and posters
    movie_display = movie.upper()
    
    if request.method == 'POST':
        feedback_form = FeedbackForm(request.POST)
        if feedback_form.is_valid():
            feedback = feedback_form.save(commit=False)
            feedback.user = request.user  # Set the user to the currently logged-in user
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            return redirect('recommend', movie=movie)  # Redirect to the same page
    else:
        feedback_form = FeedbackForm()

    # Check if the recommendations returned an error message
    if isinstance(recommendations, str):
        return render(request, 'app/recommend.html', {
            'movie': movie_display,
            'r': recommendations,
            't': 's',
            'feedback_form': feedback_form
        })
    else:
        # Pass both recommendations and posters to the template
        return render(request, 'app/recommend.html', {
            'movie': movie_display,
            'r': zip(recommendations, posters),  # Zip movie titles with posters
            't': 'l',
            'feedback_form': feedback_form
        })


# @login_required
# def recommend(request):
#     movie = request.GET.get('movie')
#     recommendations = rcmd(movie)
#     movie_display = movie.upper()
    
#     if request.method == 'POST':
#         feedback_form = FeedbackForm(request.POST)
#         if feedback_form.is_valid():
#             feedback = feedback_form.save(commit=False)
#             feedback.user = request.user  # Set the user to the currently logged-in user
#             feedback.save()
#             messages.success(request, "Thank you for your feedback!")
#             return redirect('recommend', movie=movie)  # Redirect to the same page
#     else:
#         feedback_form = FeedbackForm()

#     # Pass the feedback_form to the template regardless of POST method
#     if isinstance(recommendations, str):
#         return render(request, 'app/recommend.html', {
#             'movie': movie_display,
#             'r': recommendations,
#             't': 's',
#             'feedback_form': feedback_form
#         })
#     else:
#         return render(request, 'app/recommend.html', {
#             'movie': movie_display,
#             'r': recommendations,
#             't': 'l',
#             'feedback_form': feedback_form
#         })


# @login_required
# def recommend(request):
#     movie = request.GET.get('movie')
#     recommendations = rcmd(movie)
#     movie_display = movie.upper()
    
#     if request.method == 'POST':
#         feedback_form = FeedbackForm(request.POST)
#         if feedback_form.is_valid():
#             feedback = feedback_form.save(commit=False)
#             feedback.user = request.user  # Set the user to the currently logged-in user
#             feedback.save()
#             messages.success(request, "Thank you for your feedback!")
#             return redirect('recommend', movie=movie)  # Redirect to the same page

#     else:
#         feedback_form = FeedbackForm()

#     if isinstance(recommendations, str):
#         return render(request, 'app/recommend.html', {
#             'movie': movie_display,
#             'r': recommendations,
#             't': 's',
#             'feedback_form': feedback_form
#         })
#     else:
#         return render(request, 'app/recommend.html', {
#             'movie': movie_display,
#             'r': recommendations,
#             't': 'l',
#             'feedback_form': feedback_form
#         })


@login_required
def get_movies(request):
    try:
        movies = Movie.objects.all()
        movie_titles = [movie.movie_title for movie in movies]
        return JsonResponse(movie_titles, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def import_csv_to_db(request):
    csv_file = STATIC_URL + 'app/others/data.csv'  # Change this to the actual path
    data = pd.read_csv(csv_file)

    # Ensure that the columns match the database table columns
    data = data.rename(columns={
        'actor_1_name': 'actor_1_name',
        'actor_2_name': 'actor_2_name',
        'actor_3_name': 'actor_3_name',
        'director_name': 'director_name',
        'genres': 'genres',
        'movie_title': 'movie_title',
        'comb': 'comb'
    })

    errors = []
    for index, row in data.iterrows():
        # Use the serializer to validate and save data
        serializer = MovieSerializer(data={
            'actor_1_name': row['actor_1_name'],
            'actor_2_name': row['actor_2_name'],
            'actor_3_name': row['actor_3_name'],
            'director_name': row['director_name'],
            'genres': row['genres'],
            'movie_title': row['movie_title'],
            'comb': row['comb']
        })
        
        if serializer.is_valid():
            serializer.save()
        else:
            errors.append(f"Row {index}: {serializer.errors}")
    
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"message": "Data successfully migrated from CSV to database."}, status=status.HTTP_201_CREATED)

# def fetch_poster(id):
#      response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key=db3b42ad8b49e299ecc879fc2539fc90&language=en-US').format(movie)
#      data = response.json()
#      return "https://image.tmdb.org/t/p/w500/"+ data['poster_path']

# def fetch_poster(movie_id):
#     # Format the URL with the movie ID
#     url = 'https://api.themoviedb.org/3/movie/{}?api_key=db3b42ad8b49e299ecc879fc2539fc90&language=en-US'.format(movie_id)
    
#     # Fetch the poster from the API
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         data = response.json()
#         poster_path = data.get('poster_path')
        
#         # Return the full URL of the poster if available
#         if poster_path:
#             return f'https://image.tmdb.org/t/p/w500{poster_path}'
#         else:
#             return None
#     else:
#         return None

#working code
# def fetch_poster(movie_id):
#     url = 'https://api.themoviedb.org/3/movie/{}?api_key=db3b42ad8b49e299ecc879fc2539fc90&language=en-US'.format(movie_id)
    
#     # Retry mechanism for transient connection issues
#     retries = 3  # Number of retry attempts
#     delay = 2  # Delay in seconds between retries

#     for attempt in range(retries):
#         try:
#             response = requests.get(url)
            
#             # Check if the request was successful
#             if response.status_code == 200:
#                 data = response.json()
#                 poster_path = data.get('poster_path')
                
#                 # Return the full poster URL if available
#                 if poster_path:
#                     return f'https://image.tmdb.org/t/p/w500{poster_path}'
#                 else:
#                     return None
#             else:
#                 # Handle cases where the API responds but no poster is found
#                 print(f"Error: Received status code {response.status_code}")
#                 return None

#         except ConnectionError as e:
#             print(f"Attempt {attempt + 1} failed with error: {e}. Retrying...")
#             time.sleep(delay)  # Wait before retrying
    
#     # If all retries fail
#     print("All retries failed. Unable to fetch poster.")
#     return None


# def fetch_poster_by_title(movie_title):
#     api_key = 'YOUR_API_KEY'  # Replace with your actual TMDb API key
#     url = f'https://api.themoviedb.org/3/search/movie?api_key=db3b42ad8b49e299ecc879fc2539fc90&query={movie_title}'

#     try:
#         response = requests.get(url)
        
#         if response.status_code == 200:
#             data = response.json()
#             if data['results']:
#                 poster_path = data['results'][0].get('poster_path')
#                 if poster_path:
#                     return f'https://image.tmdb.org/t/p/w500{poster_path}'
#                 else:
#                     return None
#             else:
#                 return None
#         else:
#             print(f"Error: Received status code {response.status_code}")
#             return None
#     except Exception as e:
#         print(f"Error fetching poster: {e}")
#         return None

import requests

def fetch_poster_by_title(movie_title):
    # Function to fetch the poster from TMDb
    def fetch_from_tmdb():
        api_key = 'YOUR_TMDB_API_KEY'  # Replace with your actual TMDb API key
        url = f'https://api.themoviedb.org/3/search/movie?api_key=db3b42ad8b49e299ecc879fc2539fc90&query={movie_title}'

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    poster_path = data['results'][0].get('poster_path')
                    if poster_path:
                        return f'https://image.tmdb.org/t/p/w500{poster_path}'
            return None
        except Exception as e:
            print(f"Error fetching from TMDb: {e}")
            return None

    # Function to fetch the poster from OMDb
    # http://www.omdbapi.com/?i=tt3896198&apikey=82e3bf68
    def fetch_from_omdb():
        api_key = 'YOUR_OMDB_API_KEY'  # Replace with your actual OMDb API key
        url = f"http://www.omdbapi.com/?t={movie_title}&apikey=82e3bf68"

        try:
            response = requests.get(url)
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

def your_view(request):
    # List of header images
    header_images = [
        'static/images/header1.jpg',
        'static/images/header2.jpg',
        'static/images/header3.jpg',
        'static/images/header4.jpg',
    ]

    # Shuffle the images to randomize their order
    random.shuffle(header_images)

    context = {
        'header_images': header_images,  # Pass the list of images to the template
        't': 'some_value',  # Include other context variables as needed
        'movie': 'Some Movie Title',  # Replace with actual movie title
        'r': [('Movie 1', 'poster1.jpg'), ('Movie 2', 'poster2.jpg')]  # Replace with actual movie data
    }
    return render(request, 'recommend.html', context)



def movie_details(request, movie_title):
    # Fetch the movie details from the database
    movie = get_object_or_404(Movie, movie_title=movie_title)

    # Pass the movie details to the template
    context = {
        'movie': movie,
    }
    return render(request, 'app/movie_details.html', context)
