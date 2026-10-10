from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import RegisterForm, ReviewForm
from .models import Movie, Review, SavedMovie
from .services.tmdb import (
    TMDbConfigurationError,
    TMDbRequestError,
    get_genres,
    get_movie,
    get_similar_movies,
    search_movies,
)


def home(request):
    query = request.GET.get("q", "").strip()
    genre = request.GET.get("genre", "").strip()
    year = request.GET.get("year", "").strip()
    category = request.GET.get("category", "").strip()
    movies = []
    genres = []
    has_filters = any([query, genre, year, category])
    try:
        genres = get_genres()
    except (TMDbConfigurationError, TMDbRequestError) as exc:
        messages.error(request, str(exc))

    if has_filters:
        try:
            movies = search_movies(query=query, genre=genre, year=year, category=category)
        except (TMDbConfigurationError, TMDbRequestError) as exc:
            messages.error(request, str(exc))
    return render(
        request,
        "movies/home.html",
        {
            "query": query,
            "movies": movies,
            "genres": genres,
            "selected_genre": genre,
            "selected_year": year,
            "selected_category": category,
            "has_filters": has_filters,
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("saved_movies")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account is ready.")
            return redirect("saved_movies")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


def movie_detail(request, tmdb_id):
    movie_data = None
    saved_movie = None
    review = None
    similar_movies = []
    try:
        movie_data = get_movie(tmdb_id)
        similar_movies = get_similar_movies(tmdb_id)
    except (TMDbConfigurationError, TMDbRequestError) as exc:
        local_movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
        if not local_movie:
            messages.error(request, str(exc))
            return redirect("home")
        movie_data = _movie_to_dict(local_movie)

    if request.user.is_authenticated:
        saved_movie = SavedMovie.objects.filter(
            user=request.user,
            movie__tmdb_id=tmdb_id,
        ).select_related("movie").first()
        if saved_movie:
            review = Review.objects.filter(user=request.user, movie=saved_movie.movie).first()

    return render(
        request,
        "movies/detail.html",
        {
            "movie": movie_data,
            "saved_movie": saved_movie,
            "review": review,
            "similar_movies": similar_movies,
        },
    )


@login_required
@require_POST
def save_movie(request, tmdb_id):
    try:
        movie_data = get_movie(tmdb_id)
    except (TMDbConfigurationError, TMDbRequestError) as exc:
        messages.error(request, str(exc))
        return redirect("movie_detail", tmdb_id=tmdb_id)

    movie = upsert_movie(movie_data)
    _, created = SavedMovie.objects.get_or_create(user=request.user, movie=movie)
    if created:
        messages.success(request, f"Saved {movie.title}.")
    else:
        messages.info(request, f"{movie.title} is already in your list.")
    return redirect("saved_movies")


@login_required
def saved_movies(request):
    saved = (
        SavedMovie.objects.filter(user=request.user)
        .select_related("movie")
        .prefetch_related("movie__reviews")
    )
    reviews = {
        review.movie_id: review
        for review in Review.objects.filter(user=request.user, movie__saved_by__user=request.user)
    }
    return render(request, "movies/saved.html", {"saved_movies": saved, "reviews": reviews})


@login_required
@require_POST
def remove_saved_movie(request, movie_id):
    saved_movie = get_object_or_404(SavedMovie, user=request.user, movie_id=movie_id)
    title = saved_movie.movie.title
    saved_movie.delete()
    messages.success(request, f"Removed {title} from your list.")
    return redirect("saved_movies")


@login_required
def review_movie(request, movie_id):
    saved_movie = get_object_or_404(
        SavedMovie.objects.select_related("movie"),
        user=request.user,
        movie_id=movie_id,
    )
    review = Review.objects.filter(user=request.user, movie=saved_movie.movie).first()

    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.movie = saved_movie.movie
            try:
                review.save()
            except IntegrityError:
                messages.error(request, "You already reviewed this movie.")
            else:
                messages.success(request, "Review saved.")
                return redirect("saved_movies")
    else:
        form = ReviewForm(instance=review)

    return render(
        request,
        "movies/review_form.html",
        {"form": form, "saved_movie": saved_movie, "review": review},
    )


@login_required
@require_POST
def delete_review(request, movie_id):
    review = get_object_or_404(Review, user=request.user, movie_id=movie_id)
    review.delete()
    messages.success(request, "Review deleted.")
    return redirect("saved_movies")


@transaction.atomic
def upsert_movie(movie_data):
    movie, _ = Movie.objects.update_or_create(
        tmdb_id=movie_data["tmdb_id"],
        defaults={
            "title": movie_data["title"],
            "overview": movie_data["overview"],
            "poster_path": movie_data["poster_path"],
            "release_date": movie_data["release_date"],
        },
    )
    return movie


def _movie_to_dict(movie):
    return {
        "tmdb_id": movie.tmdb_id,
        "title": movie.title,
        "overview": movie.overview,
        "poster_path": movie.poster_path,
        "poster_url": movie.poster_url,
        "release_date": movie.release_date,
        "genre_ids": [],
    }
