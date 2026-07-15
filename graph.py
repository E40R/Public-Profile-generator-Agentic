from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END


class AgentState(TypedDict):
    """Shared state dictionary passed across all nodes in the LangGraph workflow."""
    name: str
    context: str
    search_queries: List[str]
    raw_search_results: List[Dict[str, Any]]
    extracted_sources: List[Any]       # List[SourceExtract] at runtime
    combined_raw_doc_path: Optional[str]
    profile: Optional[Any]             # FinalProfile at runtime
    retry_count: int
    validation_status: str             # 'complete' or 'needs_retry'
    missing_fields: List[str]
    output_html_path: Optional[str]
    output_json_path: Optional[str]
    output_md_path: Optional[str]


def create_profile_graph() -> StateGraph:
    """Builds and compiles the LangGraph state machine for profile generation."""
    from nodes.search_node import search_node
    from nodes.extract_node import extract_node
    from nodes.combine_node import combine_node
    from nodes.validate_node import validate_node
    from nodes.render_node import render_node

    workflow = StateGraph(AgentState)

    # Add processing nodes
    workflow.add_node("search", search_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("combine", combine_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("render", render_node)

    # Define sequential transitions
    workflow.add_edge(START, "search")
    workflow.add_edge("search", "extract")
    workflow.add_edge("extract", "combine")
    workflow.add_edge("combine", "validate")

    # Define conditional routing from validator
    def route_after_validation(state: AgentState) -> str:
        if state.get("validation_status") == "needs_retry" and state.get("retry_count", 0) <= 2:
            print(f"\n🔁 [Route] Missing critical fields: {state.get('missing_fields', [])}. Retrying search (Attempt {state.get('retry_count')}/2)...")
            return "search"
        print("\n✅ [Route] Validation passed or retries exhausted. Routing to render node...")
        return "render"

    workflow.add_conditional_edges(
        "validate",
        route_after_validation,
        {
            "search": "search",
            "render": "render"
        }
    )

    workflow.add_edge("render", END)

    return workflow.compile()
