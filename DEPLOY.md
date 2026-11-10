# Deploying TerraFlow

Recommended shape: **static frontend + containerised API + managed PostgreSQL**, all HTTPS.

## 1. Database
Create a managed PostgreSQL instance (Neon, Supabase, Render, Railway, AWS RDS, etc.). Enable automatic daily backups and test one restore.
Copy the connection string; `postgres://` / `postgresql://` URLs are converted automatically.

## 2. Backend (FastAPI, Docker)
Host `backend/` anywhere that runs a Dockerfile (Render, Railway, Fly.io, AWS App Runner, a VPS).
Environment variables:

    APP_ENV=production
    DATABASE_URL=<from step 1>
    JWT_SECRET=<output of: python -c "import secrets;print(secrets.token_urlsafe(64))">
    JWT_EXPIRE_MINUTES=720
    CORS_ORIGINS=https://app.yourdomain.co.za

With `APP_ENV=production` the API refuses to start on the default JWT secret and hides /docs.
Health check path: `/health`. Put it behind HTTPS (the host's proxy does this) at e.g. `https://api.yourdomain.co.za`.

## 3. Frontend (static)
Host `frontend/` on Vercel, Netlify, Cloudflare Pages, etc.
Build command `npm run build`, output directory `dist`, environment variable:

    VITE_API_BASE_URL=https://api.yourdomain.co.za

## 4. Before real customers
- Add email verification + password reset, and login rate limiting.
- Replace startup auto-create/`ensure_columns()` with Alembic migrations.
- Move the JWT out of localStorage (httpOnly cookie) if you can.
- Have the privacy policy, terms and POPIA position reviewed; get invoice/VAT layout checked by an accountant.
- Monitoring (Sentry / uptime check) and a tested backup restore.
