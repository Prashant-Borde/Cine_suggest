from django.urls import path
from . import views


urlpatterns = [
    path('', views.home_page, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('recommend/', views.recommend, name='recommend'),
    path('get-movies/', views.get_movies, name='get_movies'),

    path('migrate-from-csv/', views.import_csv_to_db, name='migrate-from-csv'),
    # path('movie/<int:movie_id>/', views.movie_details, name='movie_details'),
    # urls.py
    path('movie-details/<str:movie_title>/', views.movie_details, name='movie_details'),

    

]



