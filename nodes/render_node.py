import os
import json
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader
from models.profile import FinalProfile


def render_markdown(profile: FinalProfile) -> str:
    """Generates a clean Markdown representation of the executive profile."""
    md = [
        f"# Profile: {profile.full_name}\n",
        f"**Role:** {profile.current_role} | **Industry:** {profile.industry}\n",
        f"**Location:** {profile.current_city_country} | **Nationality:** {profile.nationality}\n",
        "---\n",
        f"## Executive Summary\n{profile.executive_summary}\n",
        f"## Biography\n{profile.biography}\n",
        "## Career Timeline\n"
    ]
    for item in profile.career_timeline:
        md.append(f"- **{item.year}:** {item.event}")

    md.append("\n## Education\n")
    for ed in profile.education:
        md.append(f"- {ed}")

    md.append("\n## Interests & Focus Areas\n")
    for int_item in profile.interests:
        md.append(f"- {int_item}")

    md.append(f"\n## Estimated Net Worth\n**{profile.estimated_net_worth}**\n")
    if profile.net_worth_details_or_conflicts:
        md.append(f"> *Note on sources/variations:* {profile.net_worth_details_or_conflicts}\n")

    if profile.recent_news:
        md.append("## Recent News & Public Activities\n")
        for news in profile.recent_news:
            md.append(f"- {news}")

    if profile.missing_or_conflicting_info:
        md.append("\n## Missing or Conflicting Information Disclosure\n")
        for note in profile.missing_or_conflicting_info:
            md.append(f"- ⚠️ {note}")

    if profile.references:
        md.append("\n## References & Source Links\n")
        for ref in profile.references:
            md.append(f"- [{ref.source}]({ref.url})")

    return "\n".join(md)


def render_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 5: Multi-Format Render Node (Jinja2 HTML, JSON, and Markdown)."""
    profile: FinalProfile = state["profile"]
    name = state["name"]
    name_slug = name.replace(" ", "_").lower()

    os.makedirs("outputs", exist_ok=True)

    # 1. Save structured JSON
    json_path = os.path.join("outputs", f"{name_slug}_profile.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(profile.model_dump(), f, indent=2, default=str)
    print(f"📦 [Render Node] Saved structured Pydantic JSON to: {json_path}")

    # 2. Save Markdown
    md_path = os.path.join("outputs", f"{name_slug}_profile.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_markdown(profile))
    print(f"📝 [Render Node] Saved clean Markdown report to: {md_path}")

    # 3. Render and save Jinja2 HTML profile
    html_path = os.path.join("outputs", f"{name_slug}_profile.html")
    try:
        # Resolve template dir relative to this file's location
        this_dir = os.path.dirname(os.path.abspath(__file__))
        template_dir = os.path.join(os.path.dirname(this_dir), "templates")
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("profile.html")

        profile_dict = profile.model_dump()
        # Convert CareerTimelineItem objects to dicts if needed
        if profile_dict.get("career_timeline"):
            profile_dict["career_timeline"] = [
                item if isinstance(item, dict) else {"year": str(item), "event": ""}
                for item in profile_dict["career_timeline"]
            ]

        rendered_html = template.render(
            profile=profile_dict,
            name=profile.full_name
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
        print(f"🎨 [Render Node] Rendered responsive Jinja2 HTML profile to: {html_path}")
    except Exception as e:
        print(f"⚠️ [Render Node] Could not render Jinja2 HTML template ({e}). Ensuring JSON and MD exist.")
        import traceback
        traceback.print_exc()
        html_path = None

    print(f"\n🌟 All generation outputs finalized in 'outputs/' directory!")
    return {
        "output_html_path": html_path,
        "output_json_path": json_path,
        "output_md_path": md_path
    }
