"""
GCP Cloud Provider Service Module.

Required IAM roles:
  - roles/billing.viewer (to view billing data)
  - roles/bigquery.dataViewer (to query BigQuery billing export table)
  - roles/compute.viewer (to view Compute Engine resources)
  - roles/storage.objectViewer (to view Storage buckets)
"""
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def validate_credentials(service_account_json: str, project_id: str) -> dict:
    """
    Validate GCP credentials via service account JSON and BigQuery/Storage client.
    """
    try:
        from google.oauth2 import service_account
        from google.cloud import storage

        creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
        credentials = service_account.Credentials.from_service_account_info(creds_dict)

        client = storage.Client(project=project_id, credentials=credentials)
        # Lightweight check: list buckets with max_results=1
        list(client.list_buckets(max_results=1))

        return {
            "success": True,
            "data": {
                "project_id": project_id,
                "client_email": creds_dict.get("client_email"),
            }
        }
    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid GCP Service Account JSON format."}
    except Exception as exc:
        logger.warning("GCP credential validation failed: %s", exc)
        return {"success": False, "error": f"GCP validation failed: {str(exc)}"}


def get_cost_data(service_account_json: str, project_id: str, bigquery_dataset: str = None, months: int = 3) -> dict:
    """
    Fetch cost data via BigQuery billing export dataset.

    If dataset is missing or unreachable, returns a clear structured error explaining
    billing export must be enabled.
    """
    if not bigquery_dataset:
        return {
            "success": False,
            "error": (
                "GCP BigQuery billing export dataset is not configured. "
                "Please enable BigQuery Billing Export in GCP Console and specify the dataset name."
            )
        }

    try:
        from google.oauth2 import service_account
        from google.cloud import bigquery

        creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        client = bigquery.Client(project=project_id, credentials=credentials)

        # Build query for export table
        table_path = f"`{project_id}.{bigquery_dataset}.gcp_billing_export_v1_*`"
        query = f"""
            SELECT
                service.description AS service,
                SUM(cost) AS total_cost,
                currency
            FROM {table_path}
            WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {months * 30} DAY)
            GROUP BY service.description, currency
            HAVING total_cost > 0
            ORDER BY total_cost DESC
        """

        query_job = client.query(query)
        results = query_job.result()

        normalized_costs = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for row in results:
            normalized_costs.append({
                "service": row.service or "GCP Service",
                "provider": "gcp",
                "monthly_cost": round(float(row.total_cost or 0.0), 2),
                "currency": row.currency or "USD",
                "period_start": now_str,
                "period_end": now_str,
            })

        return {"success": True, "data": normalized_costs}
    except Exception as exc:
        err_msg = str(exc)
        logger.warning("GCP BigQuery billing query failed: %s", err_msg)
        return {
            "success": False,
            "error": f"Failed to query GCP BigQuery billing export dataset: {err_msg}"
        }


def get_resource_metadata(service_account_json: str, project_id: str) -> dict:
    """
    Fetch Compute Engine instances and Cloud Storage buckets metadata.
    """
    try:
        from google.oauth2 import service_account
        from google.cloud import storage, compute_v1

        creds_dict = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
        credentials = service_account.Credentials.from_service_account_info(creds_dict)

        resources = []

        # 1. Compute Instances
        try:
            instances_client = compute_v1.InstancesClient(credentials=credentials)
            request = compute_v1.AggregatedListInstancesRequest(project=project_id)
            aggregated_list = instances_client.aggregated_list(request=request)

            for zone, response in aggregated_list:
                if response.instances:
                    for instance in response.instances:
                        status = instance.status.lower() if instance.status else "unknown"
                        resources.append({
                            "resource_id": instance.name,
                            "resource_type": "gcp_instance",
                            "provider": "gcp",
                            "region": zone.split("/")[-1] if zone else "global",
                            "status": status,
                            "metadata": {
                                "machine_type": instance.machine_type.split("/")[-1] if instance.machine_type else "unknown",
                                "disks": [d.source.split("/")[-1] for d in instance.disks if d.source],
                            }
                        })
        except Exception as exc:
            logger.warning("Failed to list GCP instances: %s", exc)

        # 2. Cloud Storage Buckets
        try:
            storage_client = storage.Client(project=project_id, credentials=credentials)
            buckets = list(storage_client.list_buckets())
            for bucket in buckets:
                resources.append({
                    "resource_id": bucket.name,
                    "resource_type": "gcs_bucket",
                    "provider": "gcp",
                    "region": bucket.location.lower() if bucket.location else "global",
                    "status": "active",
                    "metadata": {
                        "storage_class": bucket.storage_class,
                        "time_created": bucket.time_created.isoformat() if bucket.time_created else None,
                        "has_lifecycle_rules": bool(bucket.lifecycle_rules),
                    }
                })
        except Exception as exc:
            logger.warning("Failed to list GCP buckets: %s", exc)

        return {"success": True, "data": resources}
    except Exception as exc:
        logger.exception("Unexpected error fetching GCP resource metadata")
        return {"success": False, "error": f"Unexpected error: {str(exc)}"}
