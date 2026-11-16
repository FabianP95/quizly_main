# Quizly Backend

REST API for **Quizly**, a quiz application that generates multiple-choice quizzes from YouTube videos. Users can register, log in, generate quizzes, take them and manage their quiz library.

The frontend is maintained separately and is not part of this repository.

## Tech Stack

- Python 3.14
- Django 6.1
- Django REST Framework
- Simple JWT (authentication via HttpOnly cookies)
- django-cors-headers
- yt-dlp (download audio from YouTube videos)
- OpenAI Whisper (local audio transcription, runs on PyTorch)
- Google Gemini via `google-genai` (quiz generation from the transcript)
- python-dotenv (loads environment variables from `.env`)
- SQLite (development)

## Requirements

Before installing the project, make sure the following is available on your machine:

| Requirement        | Why it is needed                                                        |
| ------------------ | ----------------------------------------------------------------------- |
| Python 3.14        | Runtime for the backend                                                 |
| FFmpeg             | Used by yt-dlp and Whisper to extract and decode the audio              |
| Google Gemini API key | Used to generate the quiz questions from the transcript             |
| JavaScript runtime (e.g. [Deno](https://deno.com/)) – recommended | Used by yt-dlp (`yt-dlp-ejs`) to solve YouTube's JS challenges; without it some downloads may fail |
| ~3 GB free disk space | PyTorch plus the Whisper `turbo` model (~1.5 GB)                    |

### FFmpeg

[FFmpeg](https://ffmpeg.org/download.html) must be installed and available on the `PATH`.

- Windows: `winget install ffmpeg` (or download a build and add its `bin` folder to the `PATH`)
- macOS: `brew install ffmpeg`
- Linux (Debian/Ubuntu): `sudo apt install ffmpeg`

Check the installation with:

```bash
ffmpeg -version
```

### Whisper model

Whisper is installed via `requirements.txt` (`openai-whisper`), no separate installation is needed. On the **first** quiz generation the `turbo` model is downloaded automatically (~1.5 GB, cached in `~/.cache/whisper`), so the first request takes noticeably longer. Transcription runs locally – a CUDA capable GPU speeds it up considerably, but the CPU works as well.

### Google Gemini API key

1. Sign in at [Google AI Studio](https://aistudio.google.com/)
2. Create a new key under **Get API key**
3. Add it as `GEMINI_API_KEY` to your `.env` file (see [Configure environment variables](#4-configure-environment-variables))

The free tier is sufficient for development. If a model is temporarily unavailable, the backend automatically retries with a fallback model.

## Project Structure

```
quizly_main/
├── .github/workflows/  # CI pipeline (lint + tests)
├── core/               # Project settings and root URL configuration
├── user_auth_app/      # Custom user model and authentication
│   ├── api/            # Serializers, views, URLs, cookie JWT authentication
│   └── tests/          # Tests for the authentication flow
├── quiz_app/           # Quiz generation and management
│   ├── api/            # Serializers, views, URLs, services (YouTube download / transcription)
│   ├── tests/          # Tests for the quiz endpoints
│   └── models.py       # Quiz and Question models
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
| `GEMINI_API_KEY`    | API key from Google AI Studio   |

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

## Quizzes

A quiz is generated from a YouTube video in three steps:

1. **Download** – the audio track is downloaded with yt-dlp into the system's temporary directory (`tempfile.gettempdir()`, e.g. `%TEMP%` on Windows, `/tmp` on Linux)
2. **Transcribe** – the audio is transcribed locally with Whisper; the temporary audio file is deleted afterwards
3. **Generate** – the transcript is sent to Google Gemini, which returns a quiz with 10 multiple-choice questions. The response is validated before the quiz is saved

No audio files are stored permanently in the project. Users can only see and edit their own quizzes.

### Data model

| Model      | Fields                                                                                           |
| ---------- | ------------------------------------------------------------------------------------------------ |
| `Quiz`     | `creator` (FK User), `title`, `description`, `video_url`, `created_at`, `updated_at`             |
| `Question` | `quiz` (FK Quiz), `question_title`, `question_options` (list of 4), `answer`, `created_at`, `updated_at` |

Deleting a quiz also deletes all its questions.

### Endpoints

| Method | Endpoint              | Description                                       |
| ------ | --------------------- | ------------------------------------------------- |
| POST   | `/api/quizzes/`       | Create a quiz from a YouTube URL                  |
| GET    | `/api/quizzes/`       | List all quizzes of the current user              |
| GET    | `/api/quizzes/{id}/`  | Retrieve a single quiz                            |
| PATCH  | `/api/quizzes/{id}/`  | Update `title` and/or `description`               |
| DELETE | `/api/quizzes/{id}/`  | Delete a quiz including its questions             |

**Create quiz** – request body:

```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

Returns `201` with the full quiz including its questions, `400` for an invalid URL and `500` if the quiz could not be generated (download, transcription or Gemini failed). Detail endpoints return `403` if the quiz belongs to another user and `404` if it does not exist. `DELETE` returns `204` without a body.

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
2. Generate migrations (they are not part of the repository)
3. Django system check
4. Run the test suite

## Frontend Connection

Allowed frontend origins are configured in `CORS_ALLOWED_ORIGINS` in `core/settings.py`. Add the address your frontend is served from (e.g. `http://127.0.0.1:5500` for VS Code Live Server).
