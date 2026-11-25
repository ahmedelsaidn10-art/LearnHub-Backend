from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    """A student account or an internal admin account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="student", nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # A user has one current OTP. A new OTP request replaces the old row.
    otp = db.relationship(
        "EmailOTP",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    enrollments = db.relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = db.relationship(
        "LessonProgress", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """Save a hash instead of saving the raw password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class EmailOTP(db.Model):
    """The current email verification code for one user."""

    __tablename__ = "email_otps"

    # Making user_id the primary key keeps only one OTP row per user.
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    code_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="otp")
