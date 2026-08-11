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
