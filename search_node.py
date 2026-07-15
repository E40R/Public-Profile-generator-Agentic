import time
from typing import Dict, Any, List

import wikipedia
from duckduckgo_search import DDGS


def get_wikipedia_info(name: str) -> Dict[str, Any]:
    """Search and extract authoritative biography and photo from Wikipedia."""
    print(f"🔍 [Search Node] Querying Wikipedia for: '{name}'...")
    try:
        search_results = wikipedia.search(name, results=3)
        if not search_results:
            return {}

        page_title = search_results[0]
        page = wikipedia.page(page_title, auto_suggest=False)

        # Filter for a high-quality portrait photo
        photo_url = None
        if hasattr(page, 'images') and page.images:
            name_parts = [p.lower() for p in name.split()]
            for img in page.images:
                img_lower = img.lower()
                skip_words = ['svg', 'icon', 'logo', 'flag', 'symbol', 'signature',
                              'commons-logo', 'wiki', 'edit', 'semi-protection', 'lock']
                if not any(ext in img_lower for ext in ['.jpg', '.jpeg', '.png']):
                    continue
                if any(skip in img_lower for skip in skip_words):
                    continue
                photo_url = img
                # Prefer images matching the person's name
                if any(part in img_lower for part in name_parts):
                    photo_url = img
                    break

        return {
            "source": "Wikipedia",
            "url": page.url,
            "title": page.title,
            "photo_url": photo_url,
            "content": f"Title: {page.title}\nSummary: {page.summary}\nFull Content Snippet: {page.content[:4000]}"
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Try the first option from disambiguation
        try:
            first_option = e.options[0]
            print(f"  ↳ Disambiguation hit, trying: '{first_option}'")
            page = wikipedia.page(first_option, auto_suggest=False)
            return {
                "source": "Wikipedia",
                "url": page.url,
                "title": page.title,
                "photo_url": None,
                "content": f"Title: {page.title}\nSummary: {page.summary}\nFull Content Snippet: {page.content[:4000]}"
            }
        except Exception:
            return {}
    except Exception as e:
        print(f"⚠️ [Search Node] Wikipedia search warning for '{name}': {e}")
        return {}


def get_web_search_results(queries: List[str], max_per_query: int = 3) -> List[Dict[str, Any]]:
    """Search DuckDuckGo for financial figures, Forbes reports, and recent news."""
    results = []
    for q in queries:
        print(f"🌐 [Search Node] Web search query: '{q}'...")
        try:
            ddgs = DDGS()
            hits = ddgs.text(q, max_results=max_per_query)
            for r in hits:
                results.append({
                    "source": f"Web Search ({r.get('title', 'Article')[:60]})",
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "content": f"Title: {r.get('title', '')}\nURL: {r.get('href', '')}\nSnippet: {r.get('body', '')}"
                })
            time.sleep(0.3)
        except Exception as query_err:
            print(f"⚠️ [Search Node] Query '{q}' failed: {query_err}")
    return results


def search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 1: Multi-Source RAG & Web Search retriever."""
    name = state["name"]
    context = state.get("context", "")
    existing_results = state.get("raw_search_results", [])

    # Check if we are doing a targeted retry or initial search
    custom_queries = state.get("search_queries", [])
    if custom_queries and state.get("retry_count", 0) > 0:
        print(f"🔁 [Search Node] Executing targeted loopback queries: {custom_queries}")
        new_web_results = get_web_search_results(custom_queries, max_per_query=4)
        return {
            "raw_search_results": existing_results + new_web_results
        }

    # Primary initial search setup
    print(f"\n🚀 [Search Node] Initializing multi-source RAG retrieval for '{name}' ({context})...")

    # 1. Wikipedia authoritative search
    wiki_data = get_wikipedia_info(name)
    results = [wiki_data] if wiki_data else []

    # 2. Forbes & Net Worth targeted search
    forbes_queries = [
        f"{name} net worth Forbes 2025 OR 2024",
        f"{name} {context} estimated net worth compensation salary"
    ]
    results.extend(get_web_search_results(forbes_queries, max_per_query=3))

    # 3. Career, Education & Recent News search
    bio_queries = [
        f"{name} {context} career timeline education degree university",
        f"{name} {context} recent news achievements activities 2025"
    ]
    results.extend(get_web_search_results(bio_queries, max_per_query=3))

    # Filter out empty results and deduplicate by URL
    seen_urls = set()
    deduped_results = []
    for r in results:
        url = r.get("url", "")
        if r and url and url not in seen_urls:
            seen_urls.add(url)
            deduped_results.append(r)

    print(f"✅ [Search Node] Retrieved {len(deduped_results)} unique source documents across Wikipedia and Web.")
    return {
        "raw_search_results": deduped_results,
        "search_queries": forbes_queries + bio_queries
    }
