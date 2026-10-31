# Quizly Backend

REST API for **Quizly**, a quiz application that generates multiple-choice quizzes from YouTube videos. Users can register, log in, generate quizzes, take them and manage their quiz library.

The frontend is maintained separately and is not part of this repository.

## Tech Stack

- Python 3.14
- Django 6.1
- Django REST Framework
- Simple JWT (authentication via HttpOnly cookies)
- django-cors-headers
- SQLite (development)

## Project Structure

```
quizly_main/
├── core/             # Project settings and root URL configuration
├── user_auth_app/    # Custom user model, registration, login, logout
├── quiz_app/         # Quiz generation and management
├── manage.py
├── requirements.txt
└── .env.template     # Template for environment variables
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd quizly_main
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.template` to `.env` and fill in the values:

```bash
cp .env.template .env
```

| Variable            | Description                     |
| ------------------- | ------------------------------- |
| `DJANGO_SECRET_KEY` | Django secret key               |
| `DJANGO_DEBUG`      | `True` for local development    |

A new secret key can be generated with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Set up the database

Migrations are not included in the repository and have to be created locally:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 7. Start the development server

```bash
python manage.py runserver
```

The API is now available at `http://127.0.0.1:8000/`, the admin panel at `http://127.0.0.1:8000/admin/`.

## Authentication

The API uses JWT authentication with **HttpOnly cookies**. On login the access token is set as a cookie, so the frontend never has direct access to the token. All endpoints require authentication by default unless stated otherwise.

## Frontend Connection

Allowed frontend origins are configured in `CORS_ALLOWED_ORIGINS` in `core/settings.py`. Add the address your frontend is served from (e.g. `http://127.0.0.1:5500` for VS Code Live Server).
