from flask import Flask, jsonify

from app.config import Config
# Import model modules so Flask-Migrate can discover their tables.
from app.auth import models as _auth_models
from app.courses import models as _course_models
from app.learning import models as _learning_models
from app.auth.route import auth_bp
from app.courses.route import courses_bp, uploads_bp
from app.learning.route import learning_bp
from app.learning.favorites_route import favorites_bp
from app.extensions import cors, db, jwt, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)
    config_object.validate()

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(uploads_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(favorites_bp)
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"],
            }
        },
        supports_credentials=True,
    )

    @app.get("/api/health")
    def health_check():
        return jsonify({"status": "ok"}), 200

    return app



