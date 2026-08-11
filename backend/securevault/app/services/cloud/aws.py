"""
AWS Cloud Provider Service Module.

Required IAM permissions:
  - sts:GetCallerIdentity (for credential validation)
  - ce:GetCostAndUsage (for Cost Explorer queries)
  - ec2:DescribeInstances, ec2:DescribeVolumes (for EC2/EBS metadata)
  - s3:ListAllMyBuckets, s3:GetBucketLocation (for S3 metadata)
"""
import logging
from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


def validate_credentials(access_key_id: str, secret_access_key: str, region: str = "us-east-1") -> dict:
    """
    Validate AWS credentials using STS get_caller_identity.

    Returns:
        {"success": True, "data": {"account_id": ..., "arn": ...}}
        or {"success": False, "error": str}
    """
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region or "us-east-1"
        )
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        return {
            "success": True,
            "data": {
                "account_id": identity.get("Account"),
                "arn": identity.get("Arn"),
                "user_id": identity.get("UserId"),
            }
        }
    except (BotoCoreError, ClientError) as exc:
        err_msg = exc.response.get("Error", {}).get("Message") if hasattr(exc, "response") else str(exc)
        logger.warning("AWS credential validation failed: %s", err_msg)
        return {"success": False, "error": f"AWS validation failed: {err_msg}"}
    except Exception as exc:
        logger.exception("Unexpected error validating AWS credentials")
        return {"success": False, "error": f"Unexpected error: {str(exc)}"}


def get_cost_data(access_key_id: str, secret_access_key: str, region: str = "us-east-1", months: int = 3) -> dict:
    """
    Fetch monthly cost breakdown by service via AWS Cost Explorer.

    Returns normalized list of cost items.
    """
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region or "us-east-1"
        )
        ce = session.client("ce")

        end_date = datetime.now(timezone.utc).replace(day=1)
        start_date = end_date
        for _ in range(months):
            # Move back 1 month
            start_date = (start_date - timedelta(days=1)).replace(day=1)

        time_period = {
            "Start": start_date.strftime("%Y-%m-%d"),
            "End": end_date.strftime("%Y-%m-%d"),
        }

        response = ce.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        normalized_costs = []
        for result in response.get("ResultsByTime", []):
            period_start = result.get("TimePeriod", {}).get("Start")
            period_end = result.get("TimePeriod", {}).get("End")
            for group in result.get("Groups", []):
                service_name = group.get("Keys", ["Unknown"])[0]
                amount = float(group.get("Metrics", {}).get("UnblendedCost", {}).get("Amount", 0.0))
                unit = group.get("Metrics", {}).get("UnblendedCost", {}).get("Unit", "USD")

                if amount > 0:
                    normalized_costs.append({
                        "service": service_name,
                        "provider": "aws",
                        "monthly_cost": round(amount, 2),
                        "currency": unit,
                        "period_start": period_start,
                        "period_end": period_end,
                    })

        return {"success": True, "data": normalized_costs}
    except (BotoCoreError, ClientError) as exc:
        err_msg = exc.response.get("Error", {}).get("Message") if hasattr(exc, "response") else str(exc)
        logger.warning("AWS Cost Explorer error: %s", err_msg)
        return {"success": False, "error": f"AWS Cost Explorer error: {err_msg}"}
    except Exception as exc:
        logger.exception("Unexpected error fetching AWS cost data")
        return {"success": False, "error": f"Unexpected error: {str(exc)}"}


def get_resource_metadata(access_key_id: str, secret_access_key: str, region: str = "us-east-1") -> dict:
    """
    Fetch EC2 instances, EBS volumes, and S3 buckets metadata.

    Returns normalized list of resource items.
    """
    try:
        session = boto3.Session(
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region or "us-east-1"
        )
        resources = []

        # 1. EC2 Instances
        try:
            ec2 = session.client("ec2")
            paginator = ec2.get_paginator("describe_instances")
            for page in paginator.paginate():
                for reservation in page.get("Reservations", []):
                    for inst in reservation.get("Instances", []):
                        instance_id = inst.get("InstanceId")
                        instance_type = inst.get("InstanceType")
                        state = inst.get("State", {}).get("Name")
                        launch_time = inst.get("LaunchTime")

                        resources.append({
                            "resource_id": instance_id,
                            "resource_type": "ec2_instance",
                            "provider": "aws",
                            "region": region,
                            "status": state,
                            "metadata": {
                                "instance_type": instance_type,
                                "launch_time": launch_time.isoformat() if launch_time else None,
                                "attached_volumes": [
                                    bd.get("Ebs", {}).get("VolumeId")
                                    for bd in inst.get("BlockDeviceMappings", [])
                                    if "Ebs" in bd
                                ],
                            }
                        })
        except Exception as exc:
            logger.warning("Failed to describe EC2 instances: %s", exc)

        # 2. EBS Volumes (check for unattached)
        try:
            volumes = ec2.describe_volumes().get("Volumes", [])
            for vol in volumes:
                vol_id = vol.get("VolumeId")
                size_gb = vol.get("Size")
                attachments = vol.get("Attachments", [])
                status = "attached" if attachments else "unattached"

                resources.append({
                    "resource_id": vol_id,
                    "resource_type": "ebs_volume",
                    "provider": "aws",
                    "region": region,
                    "status": status,
                    "metadata": {
                        "size_gb": size_gb,
                        "volume_type": vol.get("VolumeType"),
                        "attached_to": [att.get("InstanceId") for att in attachments],
                    }
                })
        except Exception as exc:
            logger.warning("Failed to describe EBS volumes: %s", exc)

        # 3. S3 Buckets
        try:
            s3 = session.client("s3")
            buckets = s3.list_buckets().get("Buckets", [])
            for b in buckets:
                bucket_name = b.get("Name")
                creation_date = b.get("CreationDate")

                # Check lifecycle rules
                has_lifecycle = False
                try:
                    s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                    has_lifecycle = True
                except ClientError:
                    has_lifecycle = False

                resources.append({
                    "resource_id": bucket_name,
                    "resource_type": "s3_bucket",
                    "provider": "aws",
                    "region": region,
                    "status": "active",
                    "metadata": {
                        "creation_date": creation_date.isoformat() if creation_date else None,
                        "has_lifecycle_policy": has_lifecycle,
                    }
                })
        except Exception as exc:
            logger.warning("Failed to list S3 buckets: %s", exc)

        return {"success": True, "data": resources}
    except Exception as exc:
        logger.exception("Unexpected error fetching AWS resource metadata")
        return {"success": False, "error": f"Unexpected error: {str(exc)}"}
