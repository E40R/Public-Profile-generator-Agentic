import os
import re
import sys
from typing import Dict, Any, List
from models.profile import SourceExtract, FinalProfile
from nodes.combine_node import smart_fallback_synthesis, combine_node
from nodes.validate_node import validate_node
from nodes.render_node import render_node

# Fix Windows console UTF-8 encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def continue_from_created_files(file_path: str = "outputs/sundar_pichai_combined_sources.md"):
    print("=" * 70)
    print(f"[*] RESUMING PROFILE GENERATION FROM PREVIOUSLY RETRIEVED SOURCES")
    print(f"[*] Source file: {file_path}")
    print("=" * 70)

    if not os.path.exists(file_path):
        print(f"[ERROR] Source file {file_path} not found!")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract target person name
    name_match = re.search(r'Master Combined Raw Source Document:\s*([^\n]+)', content)
    name = name_match.group(1).strip() if name_match else "Sundar Pichai"
    context = "CEO of Alphabet and Google" if "Sundar Pichai" in name else "Executive"

    print(f"[*] Target Individual: {name} | Context: {context}")

    # Parse raw content chunks from section 2
    raw_results = []
    chunks = re.split(r'### Raw Chunk \d+:\s*', content)
    for chunk in chunks[1:]:
        lines = chunk.strip().split("\n")
        source_name = lines[0].strip()
        url_match = re.search(r'- \*\*URL:\*\*\s*([^\n]+)', chunk)
        url = url_match.group(1).strip() if url_match else ""
        text_match = re.search(r'```text\n(.*?)```', chunk, re.DOTALL)
        raw_text = text_match.group(1).strip() if text_match else chunk

        raw_results.append({
            "source": source_name,
            "url": url,
            "content": raw_text
        })

    print(f"[*] Loaded {len(raw_results)} raw search chunks from file.")

    # Re-extract structured facts from these loaded chunks using smart_chunk_extraction
    from nodes.extract_node import smart_chunk_extraction
    extracted_sources = []
    for r in raw_results:
        ext = smart_chunk_extraction(
            name=name,
            src_name=r["source"],
            src_url=r["url"],
            src_content=r["content"],
            pre_photo_url="https://upload.wikimedia.org/wikipedia/commons/c/c3/Sundar_Pichai_-_2023_%28cropped%29.jpg" if "Wikipedia" in r["source"] else None
        )
        extracted_sources.append(ext)

    # Ensure local image copy exists for reliable local file:// viewing
    try:
        import urllib.request, ssl
        ctx = ssl._create_unverified_context()
        img_url = "https://upload.wikimedia.org/wikipedia/commons/c/c3/Sundar_Pichai_-_2023_%28cropped%29.jpg"
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, context=ctx)
        img_data = res.read()
        os.makedirs("outputs", exist_ok=True)
        open("outputs/sundar_pichai.jpg", "wb").write(img_data)
        print("[*] Verified and saved local portrait image to outputs/sundar_pichai.jpg")
    except Exception as e:
        print(f"[*] Note: Could not download local image backup: {e}")

    print(f"[*] Re-extracted {len(extracted_sources)} structured records.")

    # Build state dictionary
    state = {
        "name": name,
        "context": context,
        "raw_search_results": raw_results,
        "extracted_sources": extracted_sources,
        "retry_count": 0,
        "profile": None
    }

    # Run combine node (will immediately use fast fallback/synthesis if rate limit hit)
    print("\n[*] Running Combine Phase...")
    combined_output = combine_node(state)
    state.update(combined_output)

    # Run validate node
    print("\n[*] Running Validation Phase...")
    validation_output = validate_node(state)
    state.update(validation_output)

    # Run render node
    print("\n[*] Running Render Phase (HTML, JSON, MD)...")
    render_output = render_node(state)
    state.update(render_output)

    print("\n" + "=" * 70)
    print("[OK] RESUMED PROFILE GENERATION SUCCESSFULLY FINISHED!")
    print("=" * 70)
    prof = state.get("profile")
    if prof:
        print(f"Name: {prof.full_name}")
        print(f"Role: {prof.current_role}")
        print(f"Location: {prof.current_city_country}")
        print(f"Estimated Net Worth: {prof.estimated_net_worth}")
        print("\nFINAL ARTIFACTS IN 'outputs/':")
        print(f"  - Structured JSON:          {state.get('output_json_path')}")
        print(f"  - Clean Markdown:           {state.get('output_md_path')}")
        print(f"  - Rendered HTML Profile:    {state.get('output_html_path')}")
        print("\nOpen outputs/sundar_pichai_profile.html in any browser to see the complete infographic!")


if __name__ == "__main__":
    file_arg = sys.argv[1] if len(sys.argv) > 1 else "outputs/sundar_pichai_combined_sources.md"
    continue_from_created_files(file_arg)

