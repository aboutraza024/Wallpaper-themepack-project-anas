# Wallpaper Management Backend

A simple FastAPI backend for a mobile wallpaper customization app.
Manages **Categories**, **Wallpapers**, **Themes**, **Icons**, and **Widgets**.

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy 2.0** — ORM
- **Pydantic v2** — request/response validation
- **MySQL** (via PyMySQL) — database
- **Plain integer ids** on every table (`1`, `2`, `3`, ...)
- **Mock S3 service** — future-ready for real `boto3` integration

Tables are created automatically when the app starts (`Base.metadata.create_all`) —
there is no migration tool to run, which keeps the project simple for beginners.

## Project Structure

Everything lives in one flat `app/` folder — no nested sub-folders to dig through.
Each file has one clear job:

```
wallpaper_backend/
├── main.py                   # App entrypoint — creates the app, creates tables on startup
├── requirements.txt
├── .env                       # Your local settings (database URL, etc.)
└── app/
    ├── config.py               # All settings, read from .env
    ├── database.py             # DB engine/session + the get_db dependency
    ├── models.py                # All 5 database tables (Category, Wallpaper, Theme, Icon, Widget)
    ├── schemas.py                # All request/response shapes (Pydantic)
    ├── crud.py                    # All database logic (create/read/update/delete functions)
    ├── s3_service.py                # Mock file-upload service
    ├── utils.py                      # Logging setup + standard JSON response helpers
    ├── routes_categories.py           # /categories endpoints
    └── routes_wallpapers.py            # /wallpapers endpoints
```

That's it — 9 files in `app/`, nothing nested. Want to change how wallpapers are
validated? Open `schemas.py`. Want to change a database query? Open `crud.py`.
Want to add an endpoint? Open the matching `routes_*.py` file.

## Setup

1. **Create a virtual environment and install dependencies**

   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure your database**

   Open `.env` and set your own database URL — that's normally the only
   thing you need to change:

   ```env
   DATABASE_URL=mysql+pymysql://<user>:<password>@<host>:<port>/<database_name>
   ```

3. **Create the MySQL database** (via phpMyAdmin or CLI) — just the empty
   database, no tables needed:

   ```sql
   CREATE DATABASE wallpaper_db CHARACTER SET utf8mb4;
   ```

4. **Run the server**

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

   On startup, the app automatically creates any tables
   (`categories`, `wallpapers`, `themes`, `icons`, `widgets`) that don't
   already exist in your database — nothing else to run.

5. **Open API docs**

   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Overview

| Method | Endpoint                                       | Description                                         |
|--------|-------------------------------------------------|-------------------------------------------------------|
| POST   | `/api/v1/wallpapers`                            | Create wallpaper (+ optional themes/icons/widgets)    |
| GET    | `/api/v1/wallpapers/{wallpaper_id}`             | Get full nested wallpaper detail                      |
| PUT    | `/api/v1/wallpapers/{wallpaper_id}`             | Partial (PATCH-like) update                            |
| DELETE | `/api/v1/wallpapers/{wallpaper_id}`             | Delete wallpaper + cascaded children                   |
| POST   | `/api/v1/wallpapers/upload`                     | Upload a file, get back a (mock) S3 URL                |
| GET    | `/api/v1/categories`                            | List all categories                                    |
| GET    | `/api/v1/categories/{category}/wallpapers`      | Get **all** wallpapers in a category — by id or name   |

### Getting wallpapers for a category (id or name, no pagination)

`{category}` accepts either the category's numeric id **or** its name, and
the endpoint always returns every matching wallpaper — there's no `page` /
`page_size` to deal with:

```
GET /api/v1/categories/3/wallpapers
GET /api/v1/categories/Nature/wallpapers
```

Both return the same shape:

```json
{
  "success": true,
  "message": "Wallpapers for category 'Nature' fetched successfully",
  "data": [ { "id": 1, "title": "Forest Pack", "...": "..." } ]
}
```

### Category resolution rule

`category_name` (when creating/updating a wallpaper) is always resolved via **get-or-create**:
- If a category with that name exists → it's reused.
- If not → a new category is created automatically, in the same transaction.

### File handling: two supported modes

- **Direct URL** — just pass `home_wallpaper_url` / `lock_wallpaper_url` / etc. as strings.
- **File upload** — `POST /api/v1/wallpapers/upload` (multipart form, `file` + `asset_type`
  query param) first, then use the returned `url` in your create/update payload.

### Partial update semantics (`PUT /wallpapers/{id}`)

Every top-level field is optional. For nested `themes` / `icons` / `widgets` arrays:
- Include `id` + fields → **update** that entry.
- Include `id` + `"delete": true` → **delete** that entry.
- Omit `id` → **add** a new entry.

### Mock S3 service

`app/s3_service.py` currently returns deterministic dummy URLs
(`https://dummy-s3-bucket.com/<folder>/<filename>`) since AWS credentials aren't
configured. The real `boto3` implementation is sketched in a comment block in the
same file — flip `USE_MOCK_S3=False` and fill in the `AWS_*` env vars when ready, then
uncomment/implement the real upload logic.

## Notes

- Every table uses a plain auto-incrementing **integer id** (`1`, `2`, `3`, ...) —
  easy to read, easy to type into a URL while testing.
- All transactional operations use `db.commit()` with rollback on failure.
- Cascading deletes are enforced both at the SQLAlchemy `relationship(cascade=...)`
  level and at the database FK level (`ondelete="CASCADE"`) — deleting a wallpaper
  also deletes its themes/icons/widgets; deleting a category also deletes its wallpapers.
- Standardized JSON envelope on every response: `{"success": bool, "message": str, "data": ...}`.
- No migration tool is used — tables are created on startup directly from the
  SQLAlchemy models in `app/models.py`, which keeps the project simple. If you
  later need real migrations, Alembic can be added without changing the app code.
