import pytest
from app.services.cloud import optimizer


def test_optimizer_rule5_oversized_instance():
    """
    Test Rule 5: Oversized / Right-Sizing compute instances.
    Should trigger recommendation for low-utilization or large-tier instance,
    and NOT trigger for a right-sized instance.
    """
    resources = [
        # Oversized instance with low CPU utilization (<15%)
        {
            "resource_id": "i-oversized-001",
            "resource_type": "ec2_instance",
            "provider": "aws",
            "status": "running",
            "metadata": {
                "instance_type": "m5.large",
                "cpu_utilization": 8.5,  # <15% threshold
                "estimated_monthly_cost": 200.0,
            }
        },
        # Right-sized instance with normal CPU utilization (>15%)
        {
            "resource_id": "i-rightsized-002",
            "resource_type": "ec2_instance",
            "provider": "aws",
            "status": "running",
            "metadata": {
                "instance_type": "t3.medium",
                "cpu_utilization": 45.0,  # >15% threshold
                "estimated_monthly_cost": 50.0,
            }
        },
        # Large instance tier without utilization data (heuristic check)
        {
            "resource_id": "gcp-large-003",
            "resource_type": "gcp_instance",
            "provider": "gcp",
            "status": "running",
            "metadata": {
                "machine_type": "n2-standard-8",
                "estimated_monthly_cost": 300.0,
            }
        }
    ]

    cost_data = [
        {"service": "Amazon EC2", "monthly_cost": 200.0, "provider": "aws"},
        {"service": "Compute Engine", "monthly_cost": 300.0, "provider": "gcp"},
    ]

    recs = optimizer._run_rule_checks(resources, cost_data)

    rec_ids = [r["id"] for r in recs]

    # Oversized instance should trigger rec-oversized-aws-i-oversized-001
    assert "rec-oversized-aws-i-oversized-001" in rec_ids

    # Heuristic large instance should trigger rec-oversized-gcp-gcp-large-003
    assert "rec-oversized-gcp-gcp-large-003" in rec_ids

    # Right-sized instance should NOT trigger rec-oversized
    assert "rec-oversized-aws-i-rightsized-002" not in rec_ids

    # Verify dollar savings calculation
    oversized_rec = next(r for r in recs if r["id"] == "rec-oversized-aws-i-oversized-001")
    assert oversized_rec["estimated_monthly_savings"] == round(200.0 * 0.40, 2)  # $80.00
    assert oversized_rec["category"] == "cost"
    assert oversized_rec["effort"] == "Medium"


def test_optimizer_all_5_rules_fire():
    """
    Verification test: All 5 optimizer rules fire together on a combined dataset.
    """
    resources = [
        # Rule 1: Stopped instance
        {"resource_id": "i-stopped-1", "resource_type": "ec2_instance", "provider": "aws", "status": "stopped"},
        # Rule 2: Unattached volume
        {"resource_id": "vol-unused-2", "resource_type": "ebs_volume", "provider": "aws", "status": "unattached", "metadata": {"size_gb": 100}},
        # Rule 3: Missing lifecycle policy
        {"resource_id": "bucket-no-life-3", "resource_type": "s3_bucket", "provider": "aws", "metadata": {"has_lifecycle_policy": False}},
        # Rule 5: Oversized instance
        {"resource_id": "i-oversized-5", "resource_type": "ec2_instance", "provider": "aws", "status": "running", "metadata": {"instance_type": "m5.4xlarge", "cpu_utilization": 5.0}},
    ]
    cost_data = [
        # Rule 4: MoM cost spike (>20%)
        {"service": "Amazon EC2", "monthly_cost": 1000.0, "provider": "aws"},
        {"service": "Amazon EC2", "monthly_cost": 2500.0, "provider": "aws"},
    ]

    recs = optimizer._run_rule_checks(resources, cost_data)
    rec_ids = [r["id"] for r in recs]

    assert any("stopped" in rid for rid in rec_ids), "Rule 1 (stopped compute) failed to fire"
    assert any("unattached" in rid for rid in rec_ids), "Rule 2 (unattached storage) failed to fire"
    assert any("lifecycle" in rid for rid in rec_ids), "Rule 3 (missing lifecycle) failed to fire"
    assert any("spike" in rid for rid in rec_ids), "Rule 4 (MoM cost spike) failed to fire"
    assert any("oversized" in rid for rid in rec_ids), "Rule 5 (oversized compute) failed to fire"


def test_provider_storage_central_config():
    """
    Requirement 1 & 3:
    Every cloud provider (AWS, GCP, Azure) has a fixed storage capacity value (in GB)
    stored in one central place (config.settings.PROVIDER_STORAGE_CAPACITY_GB).
    Total: 10 GB (AWS: 4 GB / 40%, GCP: 3 GB / 30%, Azure: 3 GB / 30%).
    """
    from config.settings import PROVIDER_STORAGE_CAPACITY_GB, get_provider_storage_capacity

    assert isinstance(PROVIDER_STORAGE_CAPACITY_GB, dict)
    assert PROVIDER_STORAGE_CAPACITY_GB["aws"] == 4
    assert PROVIDER_STORAGE_CAPACITY_GB["gcp"] == 3
    assert PROVIDER_STORAGE_CAPACITY_GB["azure"] == 3

    assert get_provider_storage_capacity("AWS") == 4
    assert get_provider_storage_capacity("GCP") == 3
    assert get_provider_storage_capacity("Azure") == 3
    assert get_provider_storage_capacity("unknown") == 3


def test_storage_size_invariance_before_and_after_optimization():
    """
    Requirement 2 & 4:
    The storage size must be IDENTICAL before and after optimization.
    The optimization algorithm must not change, resize, or reallocate the provider's total storage capacity.
    """
    from config.settings import PROVIDER_STORAGE_CAPACITY_GB

    storage_before = {
        "aws": PROVIDER_STORAGE_CAPACITY_GB["aws"],
        "gcp": PROVIDER_STORAGE_CAPACITY_GB["gcp"],
        "azure": PROVIDER_STORAGE_CAPACITY_GB["azure"],
    }

    resources = [
        {"resource_id": "i-test-1", "resource_type": "ec2_instance", "provider": "aws", "status": "stopped"},
        {"resource_id": "vol-test-2", "resource_type": "ebs_volume", "provider": "aws", "status": "unattached", "metadata": {"size_gb": 100}},
    ]
    cost_data = [
        {"service": "Amazon EC2", "monthly_cost": 500.0, "provider": "aws"},
    ]

    # Run optimizer with explicit provider_storage
    recs = optimizer.analyze(resources, cost_data, provider_storage=storage_before)
    assert len(recs) > 0

    # Ensure storage_before values were NOT modified in place
    assert storage_before["aws"] == 4
    assert storage_before["gcp"] == 3
    assert storage_before["azure"] == 3


def test_storage_size_difference_raises_assertion_error():
    """
    Requirement 4:
    Add an assertion/check that raises an error if the storage size differs before vs after optimization.
    """
    from app.services.cloud.optimizer import verify_storage_capacity_invariance

    # Identical storage before and after passes with no error
    before_valid = {"aws": 4, "azure": 3, "gcp": 3}
    after_valid  = {"aws": 4, "azure": 3, "gcp": 3}
    verify_storage_capacity_invariance(before_valid, after_valid)

    # Resized / altered storage after optimization raises AssertionError
    after_altered = {"aws": 3, "azure": 3, "gcp": 3}  # AWS capacity changed!
    with pytest.raises(AssertionError) as exc_info:
        verify_storage_capacity_invariance(before_valid, after_altered)

    assert "Storage size mismatch for provider 'aws'" in str(exc_info.value)
    assert "before optimization = 4 GB, after optimization = 3 GB" in str(exc_info.value)

    # Missing provider in after raises AssertionError
    after_missing = {"azure": 3, "gcp": 3}
    with pytest.raises(AssertionError) as exc_missing:
        verify_storage_capacity_invariance(before_valid, after_missing)

    assert "Storage size invariance violation" in str(exc_missing.value)


def test_daily_storage_invariance_30_day_cycle():
    """
    Requirement 4 & 5:
    Validation that asserts storage size invariance across all 30 days
    in baseline and optimized phases.
    """
    from app.services.cloud.demo_dataset import get_30_day_chart_cycle, validate_daily_storage_invariance

    trend = get_30_day_chart_cycle()
    assert len(trend) == 30
    assert validate_daily_storage_invariance(trend) is True

    # Mutate a day's storage to simulate illegal optimization shrinkage
    tampered = [dict(d) for d in trend]
    tampered[29]["storage_aws"] = 2  # Alter Day 30 AWS storage
    with pytest.raises(AssertionError) as exc_info:
        validate_daily_storage_invariance(tampered)
    assert "Storage invariance violation on Day 30 for AWS" in str(exc_info.value)
