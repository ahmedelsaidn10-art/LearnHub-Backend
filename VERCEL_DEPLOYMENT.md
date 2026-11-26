# Deploy the LearnHub API to Vercel

This repository exposes the existing Flask application as a Vercel Python Function.

## Import the API repository

1. In Vercel, create a new project and import `ahmedelsaidn10-art/LearnHub-Backend`.
2. Keep the repository root as the project root. Do not set a Root Directory.
3. Vercel detects Python from `index.py` and installs dependencies from `requirements.txt`.
4. Deploy after adding the environment variables below.

## Environment variables

Add these in the Vercel project settings. Copy secret values from your local `.env` directly into Vercel; do not commit `.env` or paste secrets into chat.

- `APP_ENV=production`
- `FLASK_DEBUG=false`
- `SECRET_KEY` and `JWT_SECRET_KEY`: separate long random values
- `JWT_COOKIE_SECURE=true`
- `JWT_COOKIE_SAMESITE=Lax` when the frontend proxies API requests through its own Vercel domain
- `JWT_ACCESS_TOKEN_MINUTES=30`
- `CORS_ORIGINS`: the exact production frontend origin
- `TIDB_HOST`, `TIDB_PORT`, `TIDB_DATABASE`, `TIDB_USER`, `TIDB_PASSWORD`
- `TIDB_SSL_CA`: leave empty so the app uses the `certifi` CA bundle
- `EMAIL_PROVIDER=brevo`
- `BREVO_API_KEY`, `MAIL_FROM`, `MAIL_FROM_NAME=LearnHub`, `OTP_EXPIRY_MINUTES=10`

Do not set `SMTP_*` for the hosted service; verification email uses Brevo's HTTPS API.

## Frontend routing and cookies

After Vercel gives the API project a domain, configure the frontend Vercel project to proxy `/api/*` and `/uploads/*` to that API domain. Then set the frontend's `VITE_API_BASE_URL` to an empty value and redeploy it. This keeps JWT cookies on the frontend's own origin and avoids relying on third-party cookies. The API's `CORS_ORIGINS` should still contain the exact frontend origin.

## Course images

Images already committed under `app/static/uploads/courses/` are bundled with the API and can be served. The current upload endpoint saves new files under `instance/uploads/courses`, which is temporary on Vercel Functions; newly uploaded images can disappear after an invocation or redeploy. Do not use that endpoint for permanent images until it is switched to durable image storage (for example, an image hosting service).

## Notes

- The Vercel Hobby plan is suitable for a small personal test but has usage and execution limits.
- Database migrations should be applied to TiDB before deploying; do not run migrations automatically on every function startup.
- Never add production credentials to `vercel.json`, source files, or Git.
