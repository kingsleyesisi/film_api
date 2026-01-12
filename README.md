# Star Wars API

A Django REST API for Star Wars films with caching, comments, and robust error handling.

## Features

- ✅ **Cache-Aside Architecture** - In-memory caching with 10-minute TTL
- ✅ **Auto-Cache on Startup** - Cache populated automatically when server starts
- ✅ **Comment System** - Add and view comments for films
- ✅ **Background Sync** - Sync films from SWAPI
- ✅ **Flexible URLs** - Works with or without trailing slashes
- ✅ **Robust Error Handling** - Consistent error responses across all endpoints

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Populate Data

```bash
# Sync films from SWAPI
python manage.py sync_films


### 4. Start Server

```bash
python manage.py runserver
```

The cache will automatically populate on startup with console output:
```
🚀 Populating cache on startup...
✅ Cached 6 films
```

---

## API Endpoints

### Films

#### `GET /api/films/`

List all Star Wars films with comment counts (cached).

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "title": "A New Hope",
    "release_date": "1977-05-25",
    "comment_count": 3
  }
]
```

**Error Responses:**
```json
// 500 Internal Server Error
{
  "error": "An error occurred while fetching films",
  "detail": "Internal server error"
}
```

---

#### `GET /api/films/{film_id}/`

Get details for a specific film (cached).

**Parameters:**
- `film_id` (string) - Film identifier from SWAPI (e.g., "1", "2")

**Response: 200 OK**
```json
{
  "id": 1,
  "title": "A New Hope",
  "release_date": "1977-05-25",
  "comment_count": 3
}
```

**Error Responses:**
```json
// 404 Not Found
{
  "error": "Film not found",
  "detail": "Film with ID \"999\" does not exist"
}

// 500 Internal Server Error
{
  "error": "An error occurred while fetching film details",
  "detail": "Internal server error"
}
```

---

### Comments

#### `GET /api/films/{film_id}/comments/`

List all comments for a specific film (ordered by creation time, oldest first).

**Parameters:**
- `film_id` (integer) - Film database ID

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "comment": "Amazing film!",
    "created_at": "2026-01-12T20:45:00Z",
    "film_title": "A New Hope"
  },
  {
    "id": 2,
    "comment": "Classic!",
    "created_at": "2026-01-12T20:46:00Z",
    "film_title": "A New Hope"
  }
]
```

**Error Responses:**
```json
// 404 Not Found
{
  "error": "Film not found",
  "detail": "Film with ID 999 does not exist"
}

// 500 Internal Server Error
{
  "error": "An error occurred while fetching comments",
  "detail": "Internal server error"
}
```

---

#### `POST /api/comments/`

Create a new comment for a film.

**Request Body:**
```json
{
  "comment": "string (max 500 characters)",
  "film": 1
}
```

**Response: 201 Created**
```json
{
  "id": 3,
  "comment": "Best Star Wars movie!",
  "created_at": "2026-01-12T20:50:00Z",
  "film_title": "A New Hope"
}
```

**Error Responses:**
```json
// 400 Bad Request - Missing film ID
{
  "error": "Validation error",
  "detail": "film ID is required"
}

// 400 Bad Request - Invalid film ID
{
  "error": "Validation error",
  "detail": "film ID must be a valid integer"
}

// 400 Bad Request - Missing comment
{
  "error": "Validation error",
  "detail": "comment text is required"
}

// 400 Bad Request - Empty comment
{
  "error": "Validation error",
  "detail": "comment cannot be empty or whitespace only"
}

// 400 Bad Request - Comment too long
{
  "error": "Validation error",
  "detail": "Comment cannot exceed 500 characters (current: 523)"
}

// 404 Not Found
{
  "error": "Film not found",
  "detail": "Film with ID 999 does not exist"
}

// 500 Internal Server Error
{
  "error": "An error occurred while creating the comment",
  "detail": "Internal server error"
}
```

---

## Usage Examples

### Using cURL

```bash
# List all films
curl http://localhost:8000/api/films/

# Get specific film (with or without trailing slash)
curl http://localhost:8000/api/films/1/
curl http://localhost:8000/api/films/1

# List comments for a film
curl http://localhost:8000/api/films/1/comments/

# Create a comment
curl -X POST http://localhost:8000/api/comments/ \
  -H "Content-Type: application/json" \
  -d '{"comment": "Best film ever!", "film": 1}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get all films
response = requests.get(f"{BASE_URL}/films/")
films = response.json()

# Add a comment
data = {
    "comment": "Great movie!",
    "film": 1
}
response = requests.post(f"{BASE_URL}/comments/", json=data)
comment = response.json()

# Handle errors
if response.status_code == 400:
    print(f"Validation error: {response.json()['detail']}")
elif response.status_code == 404:
    print(f"Not found: {response.json()['detail']}")
```

---

## Error Handling

All endpoints return consistent error responses with:

- **`error`** - High-level error category
- **`detail`** - Specific error message

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 404 | Not Found | Resource doesn't exist |
| 500 | Internal Server Error | Server encountered an error |

### Error Response Format

All errors follow this structure:

```json
{
  "error": "Error category",
  "detail": "Specific error message"
}
```

---

## Caching

### How It Works

1. **Auto-Population** - Cache populated on server startup
2. **Cache-Aside Pattern** - Check cache → Miss → Query DB → Cache result
3. **TTL** - 10-minute expiration
4. **Invalidation** - Cache cleared when new comments are created

### Cache Behavior

```bash
# First request after startup
GET /api/films/ → Cache hit (from auto-population)

# After cache expires (10 minutes)
GET /api/films/ → Cache miss → DB query → Cache update

# After creating a comment
POST /api/comments/ → Cache invalidated
GET /api/films/ → Cache miss → DB query (shows updated comment count)
```

---

## Development

### Project Structure

```
starwars_api/
├── film/
│   ├── models.py              # Film, FilmCache, Comments models
│   ├── views.py               # API views with caching
│   ├── serializers.py         # DRF serializers
│   ├── urls.py                # URL routing
│   ├── utils.py               # SWAPI fetching utilities
│   └── management/commands/
│       ├── sync_films.py              # Sync from SWAPI
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

### Management Commands

```bash
# Sync films from SWAPI
python manage.py sync_films
```

---

## Troubleshooting

### "Film with ID X not found"

The Film and FilmCache models are separate. Run:
```bash
python manage.py create_films_from_cache
```

### Cache not populating on startup

Check console for:
```
⚠️  No films in database. Run: python manage.py sync_films
```

Then run the sync command and restart the server.

### Database Warning on Startup

The warning about database access in `AppConfig.ready()` is harmless:
```
RuntimeWarning: Accessing the database during app initialization is discouraged.
```

This is intentional for cache pre-population and doesn't affect functionality.

---

## Technologies

- **Django** 5.2+ - Web framework
- **Django REST Framework** - API framework
- **django-cors-headers** - CORS support
- **drf-spectacular** - API documentation
- **LocMemCache** - In-memory caching (no Redis needed)

---

## License

This is a technical assessment project for demonstration purposes.
