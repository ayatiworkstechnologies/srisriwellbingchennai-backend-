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

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/srisriwellbeing
JWT_SECRET_KEY=change-this-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ADMIN_EMAIL=admin@srisriwellbeingchennai.com
ADMIN_PASSWORD=ChangeMe123!
PROJECT_NAME=Sri Sri Wellbeing Chennai API
FRONTEND_ORIGIN=http://localhost:3000,https://srisriwellbeingchennai.vercel.app,https://srisriwellbeingchennai.com,https://www.srisriwellbeingchennai.com
FRONTEND_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$
MAIL_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
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

## Application Startup Behavior

On startup, the application:

- Creates database tables from SQLAlchemy metadata
- Seeds the default admin user
- Seeds default content data

This happens in the FastAPI lifespan hook in [app/main.py](/d:/2026/srisri/backend/app/main.py).

## API Overview

### Health

- `GET /health`

### Public APIs

- `POST /api/v1/inquiries`
- `POST /api/v1/contact/leads`
- `GET /api/v1/public/services`
- `GET /api/v1/public/testimonials`
- `GET /api/v1/public/nadi-camps`
- `GET /api/v1/public/relaxation-therapies`
- `GET /api/v1/public/alternative-treatments`
- `GET /api/v1/public/panchakarma-core-therapies`
- `GET /api/v1/public/panchakarma-other-treatments`
- `GET /api/v1/public/booking-slots`
- `GET /api/v1/public/therapy-availability`
- `POST /api/v1/public/bookings`
- `POST /api/v1/public/bookings/cancel`

### Admin APIs

- `POST /api/v1/admin/login`
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/inquiries`
- `PATCH /api/v1/admin/inquiries/{inquiry_id}`
- `GET|POST|PUT|DELETE /api/v1/admin/services`
- `GET|POST|PUT|DELETE /api/v1/admin/testimonials`
- `GET|POST|PUT|DELETE /api/v1/admin/nadi-camps`
- `GET|POST|PUT|DELETE /api/v1/admin/relaxation-therapies`
- `GET|POST|PUT|DELETE /api/v1/admin/alternative-treatments`
- `GET|POST|PUT|DELETE /api/v1/admin/panchakarma-core-therapies`
- `GET|POST|PUT|DELETE /api/v1/admin/panchakarma-other-treatments`
- `GET|POST|PUT|DELETE /api/v1/admin/booking-slots`
- `GET /api/v1/admin/bookings`
- `PATCH /api/v1/admin/bookings/{booking_id}`
- `GET|POST|PUT|DELETE /api/v1/admin/therapists`
- `GET|POST|PUT|DELETE /api/v1/admin/therapist-availabilities`
- `GET|POST|PUT|DELETE /api/v1/admin/therapist-blackouts`

## Authentication

Admin routes require a bearer token returned by:

```text
POST /api/v1/admin/login
```

Use the configured `ADMIN_EMAIL` and `ADMIN_PASSWORD` values from `.env` to sign in.

## Notes

- CORS is restricted to the comma-separated origins configured in `FRONTEND_ORIGIN` plus any origins matched by `FRONTEND_ORIGIN_REGEX`.
- The backend relies on Alembic migrations for schema changes and no longer creates tables during app startup.
- `.env.example` is intended to stay committed, while `.env` should remain local only.
- Inquiries now support optional lead-capture metadata: `source`, `service_interest`, and `page_path`.
- Booking emails can be sent from admin, and public booking create/cancel flows can also send client emails when SMTP is configured and `MAIL_ENABLED=true`.
- If your provider uses port `465`, prefer `SMTP_USE_SSL=true` and `SMTP_USE_TLS=false`. If it uses port `587`, use `SMTP_USE_TLS=true`.
