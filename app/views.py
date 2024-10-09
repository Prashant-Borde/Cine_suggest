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
        lst = lst[1:11]  # Get top 10 recommendations

        # Making an empty list that will contain all 10 movie recommendations
        recommendations = []
        for index, _ in lst:
            recommendations.append(data['movie_title'][index])
        return recommendations

@login_required
def recommend(request):
    movie = request.GET.get('movie')
    recommendations = rcmd(movie)
    movie_display = movie.upper()
    
    if isinstance(recommendations, str):
        return render(request, 'app/recommend.html', {'movie': movie_display, 'r': recommendations, 't': 's'})
    else:
        return render(request, 'app/recommend.html', {'movie': movie_display, 'r': recommendations, 't': 'l'})


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


