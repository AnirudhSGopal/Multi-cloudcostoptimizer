"""
CloudAccount model — stores encrypted cloud provider credentials.

Each user can have one account per provider (aws, gcp, azure).
Credentials are stored as an encrypted JSON blob via Fernet.
"""
import enum
import json
from datetime import datetime, timezone

from app.core.extensions import db
from app.models.cloud import CloudProviderEnum


class AccountStatusEnum(str, enum.Enum):
    CONNECTED = "connected"
    ERROR     = "error"
    PENDING   = "pending"


class CloudAccount(db.Model):
    __tablename__ = "cloud_accounts"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                            nullable=False, index=True)
    provider    = db.Column(db.Enum(CloudProviderEnum), nullable=False)
    account_label = db.Column(db.String(128), nullable=False, default="")
    encrypted_credentials = db.Column(db.Text, nullable=False)
    status      = db.Column(db.Enum(AccountStatusEnum), nullable=False,
                            default=AccountStatusEnum.PENDING)
    last_synced_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at  = db.Column(db.DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc))
    updated_at  = db.Column(db.DateTime(timezone=True),
                            default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ─────────────────────────────────────────────────────
    owner   = db.relationship("User", back_populates="cloud_accounts")
    metrics = db.relationship("CloudMetric", back_populates="account",
                              lazy="dynamic", cascade="all, delete-orphan")

    # Unique constraint: one account per provider per user
    __table_args__ = (
        db.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    # ── Credential helpers ────────────────────────────────────────────────

    def set_credentials(self, creds_dict: dict) -> None:
        """
        Encrypt and store a credentials dictionary.

        Expected shapes per provider:
          aws:   {"access_key_id", "secret_access_key", "region"}
          gcp:   {"service_account_json", "project_id", "bigquery_dataset"}
          azure: {"subscription_id", "tenant_id", "client_id", "client_secret"}
        """
        from app.utils.encryption import encrypt_credential
        plaintext = json.dumps(creds_dict, separators=(",", ":"))
        self.encrypted_credentials = encrypt_credential(plaintext)

    def get_credentials(self) -> dict:
        """Decrypt and return the credentials dictionary."""
        from app.utils.encryption import decrypt_credential
        plaintext = decrypt_credential(self.encrypted_credentials)
        return json.loads(plaintext)

    # ── Serialisation ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """
        Safe representation — NEVER includes credentials.
        """
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "provider":       self.provider.value,
            "account_label":  self.account_label,
            "status":         self.status.value,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "updated_at":     self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (f"<CloudAccount id={self.id} provider={self.provider.value} "
                f"user={self.user_id} status={self.status.value}>")
