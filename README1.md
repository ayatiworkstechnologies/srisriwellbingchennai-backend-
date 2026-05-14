# After Cloning: What To Do Next

This file is a quick start guide for running the Sri Sri Wellbeing Chennai backend on your local machine.

## 1. Go to the project folder

```powershell
cd "D:\Ayathiwork\2026\Sri Sri\srisriwellbingchennai-backend-"
```

## 2. Create a Python virtual environment

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## 4. Create the MySQL database

Make sure MySQL is installed and running, then create the database:

```sql
CREATE DATABASE srisriwellbeing;
```

## 5. Create your `.env` file

Copy the example file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and update values if needed. Example:

```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/srisriwellbeing
ENVIRONMENT=development
JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ADMIN_EMAIL=admin@srisriwellbeingchennai.com
ADMIN_PASSWORD=ChangeMe123!
PROJECT_NAME=Sri Sri Wellbeing Chennai API
FRONTEND_ORIGIN=http://localhost:3000,https://srisriwellbeingchennai.vercel.app,https://srisriwellbeingchennai.com,https://www.srisriwellbeingchennai.com
FRONTEND_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$
```

## 6. Run database migrations

```powershell
alembic upgrade head
```

## 7. Start the backend server

```powershell
uvicorn app.main:app --reload
```

The API should start at:

```text
http://127.0.0.1:8000
```

## 8. Check that it is working

Open this in your browser:

```text
http://127.0.0.1:8000/api/health
```

If everything is working, you should get a successful response from the health endpoint.

## Important Notes

- On app startup, the project seeds the admin user and optionally seeds default content.
- Database tables are managed through Alembic migrations.
- The admin user is seeded using `ADMIN_EMAIL` and `ADMIN_PASSWORD` from `.env`.
- CORS allows the comma-separated origins set in `FRONTEND_ORIGIN` plus any origins matched by `FRONTEND_ORIGIN_REGEX`.
- This project uses FastAPI, SQLAlchemy, Alembic, and MySQL.

## Common Commands

Install packages again later:

```powershell
pip install -r requirements.txt
```

Run migrations:

```powershell
alembic upgrade head
```

Start dev server:

```powershell
uvicorn app.main:app --reload
```
