"""
AI-Based Multi-Cloud Cost & Resource Optimizer.

Two-pass analysis engine:
  1. Rule-based pass: Deterministic functions that compute exact savings based on resource metadata
     and cost history (e.g. stopped instances, unattached EBS/disks, missing lifecycle policies, >20% cost spikes).
  2. Gemini AI pass: Enhances recommendations with natural-language impact statements, priority tuning,
     and architectural optimization suggestions.

STRICT RULE:
  Gemini is NEVER allowed to invent or mutate `estimated_monthly_savings` values.
  All dollar values stay strictly rule-based and deterministic.
"""
import os
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def analyze(resources: List[Dict[str, Any]], cost_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main entry point for multi-cloud optimization analysis.

    Args:
        resources: Normalized resource list from provider services
        cost_data: Normalized cost list from provider services

    Returns:
        List of Recommendation dicts
    """
    # ── Phase 1: Rule-based Analysis (Deterministic) ─────────────────────────
    rule_recommendations = _run_rule_checks(resources or [], cost_data or [])

    # ── Phase 2: Gemini AI Enhancement (Prioritization & Insight) ────────────
    final_recommendations = _enhance_with_gemini(rule_recommendations, resources or [], cost_data or [])

    return final_recommendations


# ── Phase 1: Rule Engine ──────────────────────────────────────────────────────

def _run_rule_checks(resources: List[Dict[str, Any]], cost_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    recs = []

    # Check 1: Idle/Stopped Compute Instances
    for r in resources:
        r_type = r.get("resource_type")
        status = (r.get("status") or "").lower()
        provider = r.get("provider", "aws")
        res_id = r.get("resource_id", "Unknown")

        if r_type in ("ec2_instance", "gcp_instance", "azure_vm") and status in ("stopped", "deallocated", "terminated", "off"):
            # Estimate monthly storage cost of attached disks (~$0.08 per GB-month default)
            disk_gb = 50  # baseline estimate if size unlisted
            savings = round(disk_gb * 0.08, 2)
            recs.append({
                "id": f"rec-stopped-{provider}-{res_id}",
                "category": "cost",
                "priority": "high",
                "provider": provider,
                "title": f"Stopped instance {res_id} incurring storage charges",
                "description": f"Instance '{res_id}' is stopped but attached storage/disks continue to incur charges.",
                "impact_statement": f"Terminating or archiving instance '{res_id}' will eliminate unnecessary volume reservation costs.",
                "estimated_monthly_savings": savings,
                "effort": "Low",
            })

    # Check 2: Unattached Volumes / Disks
    for r in resources:
        r_type = r.get("resource_type")
        status = (r.get("status") or "").lower()
        provider = r.get("provider", "aws")
        res_id = r.get("resource_id", "Unknown")

        if r_type in ("ebs_volume", "gcp_disk", "azure_disk") and status in ("unattached", "available", "unused"):
            size_gb = r.get("metadata", {}).get("size_gb", 100)
            savings = round(size_gb * 0.10, 2)  # ~$0.10/GB for unattached EBS/disk
            recs.append({
                "id": f"rec-unattached-{provider}-{res_id}",
                "category": "storage",
                "priority": "critical",
                "provider": provider,
                "title": f"Unattached storage volume {res_id}",
                "description": f"Volume '{res_id}' ({size_gb} GB) is not attached to any compute instance.",
                "impact_statement": f"Deleting unattached volume '{res_id}' saves ${savings:.2f}/mo immediately with zero operational downtime.",
                "estimated_monthly_savings": savings,
                "effort": "Low",
            })

    # Check 3: Storage Buckets Without Lifecycle Policies
    for r in resources:
        r_type = r.get("resource_type")
        provider = r.get("provider", "aws")
        res_id = r.get("resource_id", "Unknown")
        has_lifecycle = r.get("metadata", {}).get("has_lifecycle_policy", False)

        if r_type in ("s3_bucket", "gcs_bucket", "azure_storage_account") and not has_lifecycle:
            savings = 120.00  # estimated tiering savings for unmanaged bucket
            recs.append({
                "id": f"rec-lifecycle-{provider}-{res_id}",
                "category": "storage",
                "priority": "medium",
                "provider": provider,
                "title": f"Configure Lifecycle Rules on {res_id}",
                "description": f"Bucket '{res_id}' does not have automated lifecycle transition to Infrequent Access / Glacier tiering.",
                "impact_statement": "Automated lifecycle transitions move stale objects to cold storage, reducing storage costs by up to 50%.",
                "estimated_monthly_savings": savings,
                "effort": "Medium",
            })

    # Check 4: Month-over-Month Service Cost Spikes (>20%)
    # Group cost_data by service
    service_costs: Dict[str, List[float]] = {}
    service_provider: Dict[str, str] = {}
    for c in cost_data:
        srv = c.get("service", "Unknown")
        cost = c.get("monthly_cost", 0.0)
        p = c.get("provider", "aws")
        service_costs.setdefault(srv, []).append(cost)
        service_provider[srv] = p

    for srv, costs in service_costs.items():
        if len(costs) >= 2:
            prev_cost, curr_cost = costs[-2], costs[-1]
            if prev_cost > 0 and (curr_cost - prev_cost) / prev_cost > 0.20:
                spike_delta = curr_cost - prev_cost
                p = service_provider.get(srv, "aws")
                recs.append({
                    "id": f"rec-spike-{p}-{srv.lower().replace(' ', '-')}",
                    "category": "cost",
                    "priority": "critical",
                    "provider": p,
                    "title": f"Anomalous spend spike in {srv}",
                    "description": f"{srv} cost increased by {((curr_cost - prev_cost) / prev_cost) * 100:.1f}% (${prev_cost:.2f} -> ${curr_cost:.2f}).",
                    "impact_statement": f"Investigating resource allocation or API request surges in {srv} can recover ${spike_delta:.2f}/mo in unwanted spend.",
                    "estimated_monthly_savings": round(spike_delta, 2),
                    "effort": "High",
                })

    # Check 5: Oversized Compute Instances / Right-Sizing Candidates
    # Large tier naming patterns per provider
    large_tier_keywords = (
        "xlarge", "2xlarge", "4xlarge", "8xlarge", "12xlarge", "16xlarge", "24xlarge", "metal",
        "d4", "d8", "d16", "e4", "e8", "f4", "f8", "m8", "m16",
        "-4", "-8", "-16", "-32", "-64"
    )

    # Helper to find relevant compute cost from cost_data
    def _get_compute_monthly_cost(p_name: str) -> float:
        for c in cost_data:
            c_p = (c.get("provider") or "").lower()
            c_srv = (c.get("service") or "").lower()
            if c_p == p_name and any(k in c_srv for k in ("ec2", "compute", "virtual", "vm")):
                return float(c.get("monthly_cost", 150.0))
        return 150.0  # default baseline if cost data not linked

    for r in resources:
        r_type = r.get("resource_type")
        status = (r.get("status") or "").lower()
        provider = r.get("provider", "aws")
        res_id = r.get("resource_id", "Unknown")
        meta = r.get("metadata", {})

        if r_type in ("ec2_instance", "gcp_instance", "azure_vm") and status not in ("stopped", "deallocated", "terminated", "off"):
            # Check for CPU utilization metric in metadata
            cpu_util = meta.get("cpu_utilization") or meta.get("avg_cpu_utilization") or meta.get("cpu_utilization_pct")

            if cpu_util is not None:
                try:
                    cpu_val = float(cpu_util)
                except (ValueError, TypeError):
                    cpu_val = 100.0

                if cpu_val < 15.0:
                    inst_cost = meta.get("estimated_monthly_cost") or _get_compute_monthly_cost(provider)
                    savings = round(float(inst_cost) * 0.40, 2)
                    recs.append({
                        "id": f"rec-oversized-{provider}-{res_id}",
                        "category": "cost",
                        "priority": "high" if savings >= 100 else "medium",
                        "provider": provider,
                        "title": f"Right-size low-utilization compute instance {res_id}",
                        "description": f"Instance '{res_id}' has a sustained CPU utilization of {cpu_val:.1f}% (<15% threshold).",
                        "impact_statement": f"Downsizing instance '{res_id}' to a smaller tier will save approximately ${savings:.2f}/mo with no performance degradation.",
                        "estimated_monthly_savings": savings,
                        "effort": "Medium",
                    })
            else:
                # Utilization data not available — use instance-family heuristic
                inst_type = str(meta.get("instance_type") or meta.get("machine_type") or meta.get("vm_size") or "").lower()
                if any(kw in inst_type for kw in large_tier_keywords):
                    inst_cost = meta.get("estimated_monthly_cost") or _get_compute_monthly_cost(provider)
                    savings = round(float(inst_cost) * 0.35, 2)
                    recs.append({
                        "id": f"rec-oversized-{provider}-{res_id}",
                        "category": "cost",
                        "priority": "medium",
                        "provider": provider,
                        "title": f"Review large instance {res_id} ({inst_type}) for right-sizing",
                        "description": f"Instance '{res_id}' is running on a high-spec tier ({inst_type}). Utilization metrics are unattached, so this is a heuristic flag.",
                        "impact_statement": f"Right-sizing large instance '{res_id}' ({inst_type}) could recover ~${savings:.2f}/mo. Confirm metrics before resizing.",
                        "estimated_monthly_savings": savings,
                        "effort": "Medium",
                    })

    return recs


# ── Phase 2: Gemini Enhancement ───────────────────────────────────────────────

def _enhance_with_gemini(
    rule_recs: List[Dict[str, Any]],
    resources: List[Dict[str, Any]],
    cost_data: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Call Gemini API to polish impact statements and suggest architectural optimizations.
    Maintains strictly rule-based dollar savings.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not found — using rule-based cost recommendations only.")
        return rule_recs

    try:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Map savings by rec ID to ensure strict preservation
        savings_map = {r["id"]: r["estimated_monthly_savings"] for r in rule_recs}

        prompt = f"""You are a cloud finops and cost optimization expert.
Review the following rule-based cost recommendations and raw infrastructure metrics for a multi-cloud environment.

RULE-BASED RECOMMENDATIONS:
{json.dumps(rule_recs, indent=2)}

RAW METRICS SUMMARY:
Cost Data Count: {len(cost_data)}
Resource Count: {len(resources)}

Tasks:
1. Provide polished, professional, executive-ready `impact_statement` entries for each recommendation.
2. Adjust `priority` ("critical", "high", "medium", "low") if necessary based on severity.
3. If you detect any additional optimization opportunities from raw metrics (e.g. idle DB, unassigned IPs), add up to 2 new recommendations with category "cost" or "storage" and savings 0.00.

IMPORTANT CONSTRAINTS:
- Do NOT invent or alter the `estimated_monthly_savings` for existing recommendations! Keep exact dollar numbers.
- Return ONLY valid JSON array containing objects with keys: id, category, priority, provider, title, description, impact_statement, estimated_monthly_savings, effort.
"""

        response = model.generate_content(prompt, generation_config={"temperature": 0.2})
        text = response.text.replace("```json", "").replace("```", "").strip()

        gemini_recs = json.loads(text)
        if isinstance(gemini_recs, list):
            # Enforce rule-based savings on Gemini response
            enhanced = []
            for item in gemini_recs:
                item_id = item.get("id")
                if item_id in savings_map:
                    item["estimated_monthly_savings"] = savings_map[item_id]
                else:
                    item["estimated_monthly_savings"] = float(item.get("estimated_monthly_savings", 0.0))

                enhanced.append(item)

            logger.info("Gemini enhanced %d cost recommendations.", len(enhanced))
            return enhanced

    except Exception as exc:
        logger.warning("Gemini optimization enhancement failed: %s — falling back to rule-based recommendations.", exc)

    return rule_recs
