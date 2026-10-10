from django.contrib import admin

from .models import Movie, Review, SavedMovie


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "tmdb_id")
    search_fields = ("title", "tmdb_id")


@admin.register(SavedMovie)
class SavedMovieAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "movie__title")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "movie", "updated_at")
    search_fields = ("user__username", "movie__title", "body")
