from datetime import date

import requests
from django.conf import settings


class TMDbConfigurationError(RuntimeError):
    pass


class TMDbRequestError(RuntimeError):
    pass


def _headers():
    if not settings.TMDB_ACCESS_TOKEN:
        raise TMDbConfigurationError("TMDB_ACCESS_TOKEN is not configured.")
    return {
        "Authorization": f"Bearer {settings.TMDB_ACCESS_TOKEN}",
        "Accept": "application/json",
    }


def _get(path, params=None):
    url = f"{settings.TMDB_API_BASE_URL}{path}"
    try:
        response = requests.get(url, headers=_headers(), params=params, timeout=8)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TMDbRequestError("Could not load movies from TMDb right now.") from exc
    return response.json()


def search_movies(query="", genre="", year="", category=""):
    query = query.strip()
    params = {
        "include_adult": "false",
        "language": "en-US",
        "page": 1,
    }
    if year:
        params["primary_release_year"] = year

    if query:
        params["query"] = query
        data = _get("/search/movie", params)
        movies = [_normalize_movie(item) for item in data.get("results", [])]
        if genre:
            movies = [movie for movie in movies if int(genre) in movie["genre_ids"]]
        return movies

    if genre:
        params["with_genres"] = genre

    endpoint = {
        "top_rated": "/movie/top_rated",
        "upcoming": "/movie/upcoming",
        "now_playing": "/movie/now_playing",
    }.get(category, "/discover/movie")
    if endpoint == "/discover/movie":
        params["sort_by"] = "popularity.desc"

    data = _get(endpoint, params)
    return [_normalize_movie(item) for item in data.get("results", [])]


def get_movie(tmdb_id):
    data = _get(f"/movie/{tmdb_id}", {"language": "en-US"})
    return _normalize_movie(data)


def get_genres():
    data = _get("/genre/movie/list", {"language": "en-US"})
    return data.get("genres", [])


def get_similar_movies(tmdb_id):
    data = _get(
        f"/movie/{tmdb_id}/similar",
        {"language": "en-US", "page": 1},
    )
    return [_normalize_movie(item) for item in data.get("results", [])[:8]]


def _normalize_movie(item):
    return {
        "tmdb_id": item.get("id"),
        "title": item.get("title") or item.get("name") or "Untitled",
        "overview": item.get("overview") or "",
        "poster_path": item.get("poster_path") or "",
        "release_date": _parse_date(item.get("release_date")),
        "genre_ids": item.get("genre_ids") or [],
    }


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None
