"""
Azure Cloud Provider Service Module.

Required RBAC Roles:
  - Cost Management Reader (on Subscription level)
  - Reader (on Resource Groups / Subscription for resource discovery)
"""
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def validate_credentials(subscription_id: str, tenant_id: str, client_id: str, client_secret: str) -> dict:
    """
    Validate Azure Service Principal credentials via ClientSecretCredential & SubscriptionClient.
    """
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.resource import SubscriptionClient

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        sub_client = SubscriptionClient(credential)
        sub = sub_client.subscriptions.get(subscription_id)

        return {
            "success": True,
            "data": {
                "subscription_id": sub.subscription_id,
                "display_name": sub.display_name,
                "state": sub.state,
            }
        }
    except Exception as exc:
        err_msg = str(exc)
        logger.warning("Azure credential validation failed: %s", err_msg)
        return {"success": False, "error": f"Azure validation failed: {err_msg}"}


def get_cost_data(subscription_id: str, tenant_id: str, client_id: str, client_secret: str, months: int = 3) -> dict:
    """
    Fetch cost data via Azure Cost Management query API.
    """
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.costmanagement import CostManagementClient
        from azure.mgmt.costmanagement.models import (
            QueryDefinition, QueryTimePeriod, QueryDataset, QueryAggregation, QueryGrouping
        )

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        client = CostManagementClient(credential)

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=months * 30)

        scope = f"/subscriptions/{subscription_id}"

        query_def = QueryDefinition(
            type="Usage",
            timeframe="Custom",
            time_period=QueryTimePeriod(
                from_property=start_date.isoformat(),
                to=end_date.isoformat()
            ),
            dataset=QueryDataset(
                granularity="Monthly",
                aggregation={
                    "totalCost": QueryAggregation(name="Cost", function="Sum")
                },
                grouping=[
                    QueryGrouping(type="Dimension", name="ServiceName")
                ]
            )
        )

        result = client.query.usage(scope=scope, parameters=query_def)

        normalized_costs = []
        if result and result.rows:
            # Column mapping: [Cost, ServiceName, Currency, ...]
            for row in result.rows:
                cost_val = float(row[0]) if row[0] is not None else 0.0
                service_name = str(row[1]) if len(row) > 1 and row[1] else "Azure Service"
                currency = str(row[2]) if len(row) > 2 and row[2] else "USD"

                if cost_val > 0:
                    normalized_costs.append({
                        "service": service_name,
                        "provider": "azure",
                        "monthly_cost": round(cost_val, 2),
                        "currency": currency,
                        "period_start": start_date.strftime("%Y-%m-%d"),
                        "period_end": end_date.strftime("%Y-%m-%d"),
                    })

        return {"success": True, "data": normalized_costs}
    except Exception as exc:
        err_msg = str(exc)
        logger.warning("Azure Cost Management query failed: %s", err_msg)
        return {"success": False, "error": f"Azure Cost Management error: {err_msg}"}


def get_resource_metadata(subscription_id: str, tenant_id: str, client_id: str, client_secret: str) -> dict:
    """
    Fetch Azure VMs and Storage Accounts metadata.
    """
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.compute import ComputeManagementClient
        from azure.mgmt.storage import StorageManagementClient

        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )

        resources = []

        # 1. Virtual Machines
        try:
            compute_client = ComputeManagementClient(credential, subscription_id)
            vms = list(compute_client.virtual_machines.list_all())
            for vm in vms:
                # Determine state
                instance_view = None
                status = "unknown"
                try:
                    rg = vm.id.split("/")[4] if "/" in vm.id else ""
                    instance_view = compute_client.virtual_machines.instance_view(rg, vm.name)
                    for st in instance_view.statuses:
                        if st.code.startswith("PowerState/"):
                            status = st.code.split("/")[-1].lower()
                except Exception:
                    pass

                resources.append({
                    "resource_id": vm.name,
                    "resource_type": "azure_vm",
                    "provider": "azure",
                    "region": vm.location,
                    "status": status,
                    "metadata": {
                        "vm_size": vm.hardware_profile.vm_size if vm.hardware_profile else "unknown",
                        "os_type": vm.storage_profile.os_disk.os_type if vm.storage_profile and vm.storage_profile.os_disk else "unknown",
                    }
                })
        except Exception as exc:
            logger.warning("Failed to list Azure VMs: %s", exc)

        # 2. Storage Accounts
        try:
            storage_client = StorageManagementClient(credential, subscription_id)
            accounts = list(storage_client.storage_accounts.list())
            for sa in accounts:
                resources.append({
                    "resource_id": sa.name,
                    "resource_type": "azure_storage_account",
                    "provider": "azure",
                    "region": sa.location,
                    "status": "active",
                    "metadata": {
                        "kind": sa.kind,
                        "sku": sa.sku.name if sa.sku else "unknown",
                        "allow_blob_public_access": getattr(sa, "allow_blob_public_access", None),
                    }
                })
        except Exception as exc:
            logger.warning("Failed to list Azure storage accounts: %s", exc)

        return {"success": True, "data": resources}
    except Exception as exc:
        logger.exception("Unexpected error fetching Azure resource metadata")
        return {"success": False, "error": f"Unexpected error: {str(exc)}"}
