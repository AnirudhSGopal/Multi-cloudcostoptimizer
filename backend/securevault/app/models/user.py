"""
User model with role-based access control.
Roles: admin  > analyst  > viewer
"""
import enum
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.core.extensions import db


class RoleEnum(str, enum.Enum):
    ADMIN   = "admin"
    ANALYST = "analyst"
    VIEWER  = "viewer"


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(64),  unique=True, nullable=False, index=True)
    email      = db.Column(db.String(120), unique=True, nullable=False, index=True)
    _password  = db.Column("password_hash", db.String(256), nullable=False)
    role       = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.VIEWER)
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ─────────────────────────────────────────────────────
    scan_jobs = db.relationship("ScanJob", back_populates="owner",
                                 lazy="dynamic", cascade="all, delete-orphan")

    # ── Password helpers ──────────────────────────────────────────────────
    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, plaintext: str):
        self._password = generate_password_hash(plaintext)

    def verify_password(self, plaintext: str) -> bool:
        return check_password_hash(self._password, plaintext)

    # ── RBAC helpers ──────────────────────────────────────────────────────
    def has_role(self, *roles: RoleEnum) -> bool:
        return self.role in roles

    def is_admin(self) -> bool:
        return self.role == RoleEnum.ADMIN

    def is_analyst_or_above(self) -> bool:
        return self.role in (RoleEnum.ADMIN, RoleEnum.ANALYST)

    # ── Serialisation ─────────────────────────────────────────────────────
    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role.value,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.username!r} role={self.role.value}>"