from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Movie, Review, SavedMovie
from .services.tmdb import TMDbConfigurationError, search_movies


MOVIE_DATA = {
    "tmdb_id": 550,
    "title": "Fight Club",
    "overview": "A disaffected man forms an underground club.",
    "poster_path": "/poster.jpg",
    "release_date": date(1999, 10, 15),
}


class AuthTests(TestCase):
    def test_register_logs_user_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "mhyko",
                "email": "mhyko@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("saved_movies"))
        self.assertTrue(get_user_model().objects.filter(username="mhyko").exists())

    def test_saved_movies_requires_login(self):
        response = self.client.get(reverse("saved_movies"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])


class TMDbServiceTests(TestCase):
    @override_settings(TMDB_ACCESS_TOKEN="")
    def test_missing_token_raises_configuration_error(self):
        with self.assertRaises(TMDbConfigurationError):
            search_movies("dune")

    @override_settings(TMDB_ACCESS_TOKEN="token")
    @patch("movies.services.tmdb.requests.get")
    def test_search_movies_normalizes_results(self, mock_get):
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "results": [
                {
                    "id": 1,
                    "title": "Dune",
                    "overview": "Desert politics.",
                    "poster_path": "/dune.jpg",
                    "release_date": "2021-10-22",
                }
            ]
        }

        results = search_movies("dune")

        self.assertEqual(results[0]["tmdb_id"], 1)
        self.assertEqual(results[0]["release_date"], date(2021, 10, 22))


class MovieFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer",
            password="StrongPass123!",
        )

    @patch("movies.views.get_movie", return_value=MOVIE_DATA)
    def test_user_can_save_movie_once(self, _mock_get_movie):
        self.client.login(username="viewer", password="StrongPass123!")

        url = reverse("save_movie", args=[MOVIE_DATA["tmdb_id"]])
        self.client.post(url)
        self.client.post(url)

        self.assertEqual(Movie.objects.count(), 1)
        self.assertEqual(SavedMovie.objects.count(), 1)

    @patch("movies.views.get_movie", return_value=MOVIE_DATA)
    def test_user_can_create_and_update_review_for_saved_movie(self, _mock_get_movie):
        self.client.login(username="viewer", password="StrongPass123!")
        self.client.post(reverse("save_movie", args=[MOVIE_DATA["tmdb_id"]]))
        movie = Movie.objects.get(tmdb_id=MOVIE_DATA["tmdb_id"])

        self.client.post(reverse("review_movie", args=[movie.id]), {"body": "First review"})
        self.client.post(reverse("review_movie", args=[movie.id]), {"body": "Updated review"})

        self.assertEqual(Review.objects.count(), 1)
        self.assertEqual(Review.objects.get().body, "Updated review")

    def test_user_cannot_review_unsaved_movie(self):
        movie = Movie.objects.create(**MOVIE_DATA)
        self.client.login(username="viewer", password="StrongPass123!")

        response = self.client.get(reverse("review_movie", args=[movie.id]))

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_review(self):
        other = get_user_model().objects.create_user(username="other", password="StrongPass123!")
        movie = Movie.objects.create(**MOVIE_DATA)
        Review.objects.create(user=other, movie=movie, body="Private")

        self.client.login(username="viewer", password="StrongPass123!")
        response = self.client.post(reverse("delete_review", args=[movie.id]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Review.objects.count(), 1)
