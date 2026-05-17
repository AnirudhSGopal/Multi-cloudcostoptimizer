"""
CloudMetric model — Objective 1 scaffold.
Stores raw storage usage metrics collected from AWS / Azure / GCP.
"""
import enum
from datetime import datetime, timezone

from app.core.extensions import db


class CloudProviderEnum(str, enum.Enum):
    AWS   = "aws"
    AZURE = "azure"
    GCP   = "gcp"


class CloudMetric(db.Model):
    __tablename__ = "cloud_metrics"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False, index=True)
    provider     = db.Column(db.Enum(CloudProviderEnum), nullable=False, index=True)
    account_id   = db.Column(db.String(128), nullable=True)   # AWS account / GCP project
    region       = db.Column(db.String(64),  nullable=True)
    bucket_name  = db.Column(db.String(256), nullable=True)
    storage_class = db.Column(db.String(64), nullable=True)    # e.g. STANDARD, NEARLINE
    size_bytes   = db.Column(db.BigInteger,  nullable=False, default=0)
    object_count = db.Column(db.Integer,     nullable=False, default=0)
    cost_usd     = db.Column(db.Numeric(12, 4), nullable=True)
    collected_at = db.Column(db.DateTime(timezone=True),
                             default=lambda: datetime.now(timezone.utc), index=True)

    owner = db.relationship("User", backref=db.backref("cloud_metrics", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id":            self.id,
            "user_id":       self.user_id,
            "provider":      self.provider.value,
            "account_id":    self.account_id,
            "region":        self.region,
            "bucket_name":   self.bucket_name,
            "storage_class": self.storage_class,
            "size_bytes":    self.size_bytes,
            "object_count":  self.object_count,
            "cost_usd":      float(self.cost_usd) if self.cost_usd is not None else None,
            "collected_at":  self.collected_at.isoformat() if self.collected_at else None,
        }

    def __repr__(self):
        return (f"<CloudMetric provider={self.provider.value} "
                f"bucket={self.bucket_name} size={self.size_bytes}>")