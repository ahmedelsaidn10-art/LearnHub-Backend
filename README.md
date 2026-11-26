# LearnHub Backend

Flask API for LearnHub. The code is organized by feature (`auth`, `courses`, and `learning`), with each feature split into routes, controllers, services, and repositories.

## Run locally

1. Create a virtual environment and install dependencies with `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and enter your local database and Gmail SMTP settings.
3. Make sure MySQL is running and the `learnhub_db` database exists.
4. Start the API with `python run.py`.
5. Check `http://127.0.0.1:5000/api/health`.

## Deploy on Render

The root `render.yaml` defines the free web service, health check, Gunicorn start command, and non-secret defaults. Connect this repository in Render and create the service from the Blueprint. Render will ask for the values marked `sync: false`; set them in the Render dashboard, never in Git:

- `TIDB_HOST`, `TIDB_USER`, and `TIDB_PASSWORD` from TiDB Cloud.
- `BREVO_API_KEY` and `MAIL_FROM` from a verified Brevo sender.

The Blueprint generates `SECRET_KEY` and `JWT_SECRET_KEY` for the service. Course images already used by sample courses are bundled under `app/static/uploads/courses` so they survive a Render deploy. New files uploaded through the API are stored on the service filesystem and are temporary on Render's free plan; use object storage before relying on new uploads long term.

Local development keeps using Gmail SMTP. The hosted service uses Brevo's HTTPS API because Render's free service blocks outbound SMTP ports.
