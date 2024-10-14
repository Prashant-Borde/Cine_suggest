from django.contrib import admin
from app.models import Movie
from django.contrib.auth import get_user_model

admin.site.register(Movie)
admin.site.register(get_user_model())

