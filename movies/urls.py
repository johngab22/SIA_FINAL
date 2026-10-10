from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("movies/<int:tmdb_id>/", views.movie_detail, name="movie_detail"),
    path("movies/<int:tmdb_id>/save/", views.save_movie, name="save_movie"),
    path("my-movies/", views.saved_movies, name="saved_movies"),
    path("my-movies/<int:movie_id>/remove/", views.remove_saved_movie, name="remove_saved_movie"),
    path("my-movies/<int:movie_id>/review/", views.review_movie, name="review_movie"),
    path("my-movies/<int:movie_id>/review/delete/", views.delete_review, name="delete_review"),
]
