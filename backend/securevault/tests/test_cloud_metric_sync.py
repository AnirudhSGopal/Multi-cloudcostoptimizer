import pytest

from app.core.extensions import db
from app.core.factory import create_app
from app.api.v1.cloud.routes import _persist_metrics
from app.models.cloud import CloudMetric, CloudProviderEnum
from app.models.cloud_account import CloudAccount
from app.models.user import RoleEnum, User


def test_failed_metric_replacement_rolls_back_account_scoped_delete():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        owner = User(username="metric-owner", email="metric-owner@example.test", role=RoleEnum.VIEWER)
        owner.password = "test-password"
        db.session.add(owner)
        db.session.flush()
        account = CloudAccount(
            user_id=owner.id,
            provider=CloudProviderEnum.AWS,
            account_label="test account",
            encrypted_credentials="unused",
        )
        db.session.add(account)
        db.session.flush()
        original = CloudMetric(
            user_id=owner.id,
            cloud_account_id=account.id,
            provider=CloudProviderEnum.AWS,
            size_bytes=123,
        )
        db.session.add(original)
        db.session.commit()
        account_id = account.id

        with pytest.raises(AttributeError):
            _persist_metrics(account, [None], [])

        db.session.expire_all()
        remaining = CloudMetric.query.filter_by(cloud_account_id=account_id).all()
        assert len(remaining) == 1
        assert remaining[0].size_bytes == 123

        db.session.remove()
        db.drop_all()
