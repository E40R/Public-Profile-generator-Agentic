from typing import Dict, Any, List


def validate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 4: Checkpoint & Quality Validator with conditional loopback logic."""
    profile = state.get("profile")
    retry_count = state.get("retry_count", 0)
    name = state["name"]
    context = state.get("context", "")

    print(f"\n🛡️ [Validate Node] Checking profile completeness and quality (Current retry count: {retry_count})...")

    if not profile:
        print("❌ [Validate Node] No profile object found! Triggering loopback retry...")
        return {
            "validation_status": "needs_retry",
            "retry_count": retry_count + 1,
            "missing_fields": ["entire_profile"],
            "search_queries": [f"{name} {context} biography net worth career"]
        }

    missing_fields: List[str] = []
    followup_queries: List[str] = []

    # 1. Check net worth
    nw_text = (profile.estimated_net_worth or "").lower()
    if not nw_text or any(kw in nw_text for kw in ["not found", "unknown", "not publicly available", "n/a", "not confirmed"]):
        missing_fields.append("estimated_net_worth")
        followup_queries.append(f"{name} net worth Forbes exact figure")
        followup_queries.append(f"{name} {context} estimated net worth compensation")

    # 2. Check career timeline
    if not profile.career_timeline or len(profile.career_timeline) < 2:
        missing_fields.append("career_timeline")
        followup_queries.append(f"{name} career timeline history previous roles")

    # 3. Check education
    if not profile.education or len(profile.education) == 0:
        missing_fields.append("education")
        followup_queries.append(f"{name} education degree university college")

    # Decide routing (at most 1 retry to avoid long loops when API quota is exhausted)
    if missing_fields and retry_count < 1:
        print(f"⚠️ [Validate Node] Identified missing critical fields: {missing_fields}. Triggering targeted retry (Attempt {retry_count+1}/1)...")
        return {
            "validation_status": "needs_retry",
            "retry_count": retry_count + 1,
            "missing_fields": missing_fields,
            "search_queries": followup_queries
        }

    if missing_fields:
        print(f"ℹ️ [Validate Node] Missing fields {missing_fields} remain after {retry_count} retries. Proceeding to render with explicit disclosure.")
    else:
        print("✅ [Validate Node] All critical executive profile fields validated successfully!")

    return {
        "validation_status": "complete",
        "missing_fields": missing_fields
    }
