# Sri Sri Wellbeing Chennai Backend

FastAPI backend for the Sri Sri Wellbeing Chennai platform. It provides:

- Public APIs for website content, inquiries, therapy availability, and bookings
- Admin APIs for CMS-style content management
- Booking management for therapists, schedules, and blackout windows
- Database migrations with Alembic

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- MySQL via PyMySQL
- JWT-based admin authentication

## Project Structure

```text
app/
  api/
    routes/
      admin.py              Admin authentication, CMS, bookings, therapist management
      health.py             Health check endpoint
      public.py             Public content, inquiries, bookings, availability
    content_helpers.py      Shared CRUD/query helpers
    deps.py                 Auth dependencies
  services/
    booking.py             Booking and availability utilities
    content.py             Default content/admin seeding and serializers
  config.py                Settings loader from .env
  database.py              SQLAlchemy engine, session, base
  main.py                  FastAPI app setup and router registration
  models.py                SQLAlchemy models
  schemas.py               Request/response schemas
  security.py              Password hashing and JWT helpers
alembic/
  versions/                Database migrations
requirements.txt
```

## Prerequisites

- Python 3.11+ recommended
- MySQL database

## Configuration

Copy `.env.example` to `.env` and update the values for your environment.
For Render deployment, use `render.env.example` as the checklist for service environment variables.

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/srisriwellbeing
ENVIRONMENT=development
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PASSWORD_RESET_EXPIRE_MINUTES=30
ADMIN_EMAIL=admin@srisriwellbeingchennai.com
ADMIN_PASSWORD=ChangeMe123!
SEED_DEFAULT_CONTENT=false
PROJECT_NAME=Sri Sri Wellbeing Chennai API
FRONTEND_ORIGIN=http://localhost:3000,https://srisriwellbeingchennai.vercel.app,https://srisriwellbeingchennai.com,https://www.srisriwellbeingchennai.com
FRONTEND_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$
ADMIN_RESET_PASSWORD_URL=http://localhost:3000/admin/reset-password
MAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_USER=
SMTP_PASSWORD=
SMTP_PASS=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_TIMEOUT_SECONDS=20
SMTP_LOCAL_HOSTNAME=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=Sri Sri Wellbeing Chennai
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` from `.env.example`.
4. Run database migrations:

```bash
alembic upgrade head
```

5. Start the development server:

```bash
uvicorn app.main:app --reload
```

The API will usually be available at `http://127.0.0.1:8000`.

## Render Deployment

Alembic migrations only need the database settings. If app startup exits with
`Unsafe ADMIN_PASSWORD for production`, update the backend service environment
variables in Render Dashboard before redeploying:

- `ADMIN_PASSWORD`: set a unique password with at least 10 characters. Do not use `ChangeMe123!` or `replace-with-secure-admin-password`.
- `JWT_SECRET_KEY`: set a unique random secret with at least 32 characters. Do not use `replace-with-a-long-random-secret`.
- `DATABASE_URL`: set the MySQL connection string for the hosted database, not localhost.

`ADMIN_PASSWORD` is used to create the initial admin user. If an admin user
already exists and `ADMIN_PASSWORD` is left as a placeholder, startup preserves
the existing password instead of resetting it.

After saving the environment variables, trigger a manual redeploy. The command
`alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT` can stay
as-is.

## Application Startup Behavior

On startup, the application:

- Seeds the default admin user
- Optionally seeds default content data when `SEED_DEFAULT_CONTENT=true`
- Validates production safety when `ENVIRONMENT=production` or Render sets `RENDER=true`

This happens in the FastAPI lifespan hook in [app/main.py](D:\ayati\srisri\srisriwellbingchennai-backend-\app\main.py:1).

## Clear All Data Except Admin Logins

To clear website content, bookings, enquiries, therapist data, and related records while preserving `admin_users` login accounts, run:

```bash
python clear_non_admin_data.py
```

This script also clears any `therapist_id` links from admin users so the saved logins remain valid after therapist records are removed.

## API Overview

### Health

- `GET /api/health`

### Public APIs

- `POST /api/inquiries`
- `POST /api/contact/leads`
- `GET /api/public/services`
- `GET /api/public/testimonials`
- `GET /api/public/nadi-camps`
- `GET /api/public/relaxation-therapies`
- `GET /api/public/alternative-treatments`
- `GET /api/public/panchakarma-core-therapies`
- `GET /api/public/panchakarma-other-treatments`
- `GET /api/public/booking-slots`
- `GET /api/public/therapy-availability`
- `POST /api/public/bookings`
- `POST /api/public/bookings/cancel`

### Admin APIs

- `POST /api/admin/login`
- `POST /api/admin/forgot-password`
- `POST /api/admin/reset-password`
- `GET /api/admin/dashboard`
- `GET /api/admin/inquiries`
- `PATCH /api/admin/inquiries/{inquiry_id}`
- `GET|POST|PUT|DELETE /api/admin/services`
- `GET|POST|PUT|DELETE /api/admin/testimonials`
- `GET|POST|PUT|DELETE /api/admin/nadi-camps`
- `GET|POST|PUT|DELETE /api/admin/relaxation-therapies`
- `GET|POST|PUT|DELETE /api/admin/alternative-treatments`
- `GET|POST|PUT|DELETE /api/admin/panchakarma-core-therapies`
- `GET|POST|PUT|DELETE /api/admin/panchakarma-other-treatments`
- `GET|POST|PUT|DELETE /api/admin/booking-slots`
- `GET /api/admin/bookings`
- `PATCH /api/admin/bookings/{booking_id}`
- `GET|POST|PUT|DELETE /api/admin/therapists`
- `GET|POST|PUT|DELETE /api/admin/therapist-availabilities`
- `GET|POST|PUT|DELETE /api/admin/therapist-blackouts`

## Authentication

Admin routes require a bearer token returned by:

```text
POST /api/admin/login
```

Use the configured `ADMIN_EMAIL` and `ADMIN_PASSWORD` values from `.env` to sign in.

## Notes

- CORS is restricted to the comma-separated origins configured in `FRONTEND_ORIGIN` plus any origins matched by `FRONTEND_ORIGIN_REGEX`.
- The backend relies on Alembic migrations for schema changes and does not create tables during app startup.
- Production requires a non-placeholder `JWT_SECRET_KEY` of at least 32 characters and a non-default `ADMIN_PASSWORD` of at least 10 characters.
- `.env.example` is intended to stay committed, while `.env` should remain local only.
- Inquiries now support optional lead-capture metadata: `source`, `service_interest`, and `page_path`.
- Booking emails can be sent from admin, and public booking create/cancel flows can also send client emails when SMTP is configured and `MAIL_ENABLED=true`.
- If your provider uses port `465`, prefer `SMTP_USE_SSL=true` and `SMTP_USE_TLS=false`. If it uses port `587`, use `SMTP_USE_TLS=true`.
- If the API returns `SMTP login succeeded, but the mail server refused all recipients`, the backend credentials are loading correctly and the SMTP relay itself must be fixed by the mail host.
