# Cabaluna Movie List

A server-rendered Django app where users can search movies from TMDb, save movies to their local account, and write private reviews.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set `TMDB_ACCESS_TOKEN` to your TMDb API read access token.

## Run locally

```powershell
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Tests

```powershell
python manage.py test
```
