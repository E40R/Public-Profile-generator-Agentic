import sys
import os
import io

# Fix Windows console encoding for emoji characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
from graph import create_profile_graph

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<Person Name>\" \"<Context / Role>\"")
        print("Example: python main.py \"Satya Nadella\" \"CEO of Microsoft\"")
        sys.exit(1)

    name = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ""

    print("=" * 70)
    print(f"[*] AI EXECUTIVE PROFILER (LangGraph Workflow)")
    print(f"[*] Target: {name} | Context: {context}")
    print("=" * 70)

    # Compile the LangGraph state machine
    graph = create_profile_graph()

    # Initial state
    initial_state = {
        "name": name,
        "context": context,
        "search_queries": [],
        "raw_search_results": [],
        "extracted_sources": [],
        "combined_raw_doc_path": None,
        "profile": None,
        "retry_count": 0,
        "validation_status": "in_progress",
        "missing_fields": [],
        "output_html_path": None,
        "output_json_path": None,
        "output_md_path": None,
    }

    try:
        # Run the workflow
        final_state = graph.invoke(initial_state)

        print("\n" + "=" * 70)
        print("[OK] WORKFLOW EXECUTION COMPLETE!")
        print("=" * 70)
        if final_state.get("profile"):
            prof = final_state["profile"]
            print(f"Name: {prof.full_name}")
            print(f"Role: {prof.current_role}")
            print(f"Location: {prof.current_city_country}")
            print(f"Estimated Net Worth: {prof.estimated_net_worth}")
            print("\nGENERATED ARTIFACTS:")
            print(f"  - Local Master Source Doc:  {final_state.get('combined_raw_doc_path')}")
            print(f"  - Structured JSON:          {final_state.get('output_json_path')}")
            print(f"  - Clean Markdown:           {final_state.get('output_md_path')}")
            print(f"  - Rendered HTML Infographic: {final_state.get('output_html_path')}")
            print("\nOpen the HTML file in your browser to view the formatted executive profile!")
        else:
            print("[FAIL] Workflow finished without generating a profile.")
    except Exception as e:
        print(f"\n[ERROR] Error running profile graph: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
