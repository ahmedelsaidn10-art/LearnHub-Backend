# LearnHub Backend

Flask API scaffold organized by feature: auth, courses, and learning.

## Local setup

1. Copy `.env.example` to `.env` and enter your local MySQL password in `MYSQL_PASSWORD`.
2. Make sure the local MySQL Server service is running and the `learnhub_db` schema exists.
3. Activate the virtual environment: `\.venv\Scripts\Activate.ps1`
4. Start the API: `python run.py`
5. Check http://127.0.0.1:5000/api/health

The local database connection uses `mysql+mysqlconnector` and reads its settings
from environment variables. `.env` is ignored by Git; never commit its secrets.
A hosted provider can supply `DATABASE_URL` later.

The current scaffold does not define application models yet, so there are no
project tables to migrate at this stage. Create migrations after the models are
added.
