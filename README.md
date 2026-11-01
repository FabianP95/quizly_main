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
├── .github/workflows/  # CI pipeline (lint + tests)
├── core/               # Project settings and root URL configuration
├── user_auth_app/      # Custom user model and authentication
│   ├── api/            # Serializers, views, URLs, cookie JWT authentication
│   └── tests/          # Tests for the authentication flow
├── quiz_app/           # Quiz generation and management
├── manage.py
├── pyproject.toml      # Ruff configuration
├── requirements.txt
└── .env.template       # Template for environment variables
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

The API uses JWT authentication with **HttpOnly cookies**. On login the access and refresh tokens are set as cookies (`access_token`, `refresh_token`), so the frontend never has direct access to the tokens. All endpoints require authentication by default unless stated otherwise.

| Token   | Lifetime  |
| ------- | --------- |
| Access  | 5 minutes |
| Refresh | 1 day     |

On logout the refresh token is blacklisted and both cookies are deleted.

### Endpoints

| Method | Endpoint              | Auth required | Description                                              |
| ------ | --------------------- | ------------- | -------------------------------------------------------- |
| POST   | `/api/register/`      | No            | Create a new user                                        |
| POST   | `/api/login/`         | No            | Log in and set the auth cookies                          |
| POST   | `/api/logout/`        | Yes           | Blacklist the refresh token and delete the auth cookies  |
| POST   | `/api/token/refresh/` | No (cookie)   | Issue a new access token from the `refresh_token` cookie |

**Register** – request body:

```json
{
  "username": "your_username",
  "password": "your_password",
  "confirmed_password": "your_password",
  "email": "your_email@example.com"
}
```

Returns `201` on success, `400` with validation errors otherwise (e.g. passwords do not match, email already exists).

**Login** – request body:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Returns `200` with the user data (`id`, `username`, `email`) and sets the cookies, `401` for invalid credentials.

**Logout** / **Token refresh** – no request body, the cookies are sent automatically. Both return `401` if the `refresh_token` cookie is missing or invalid.

## Testing & Linting

Run the test suite:

```bash
python manage.py test
```

Run the linter (configured in `pyproject.toml`):

```bash
ruff check .
```

## Continuous Integration

GitHub Actions (`.github/workflows/ci.yml`) runs on every push and pull request to `main`:

1. Lint with ruff
2. Django system check
3. Check for missing migrations
4. Run the test suite

## Frontend Connection

Allowed frontend origins are configured in `CORS_ALLOWED_ORIGINS` in `core/settings.py`. Add the address your frontend is served from (e.g. `http://127.0.0.1:5500` for VS Code Live Server).
