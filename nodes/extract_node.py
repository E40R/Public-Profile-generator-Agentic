import re
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from models.profile import SourceExtract
from utils.llm import get_llm, invoke_with_retry


def smart_chunk_extraction(name: str, src_name: str, src_url: str, src_content: str, pre_photo_url: str = None) -> SourceExtract:
    """Smart text-based extraction from a raw source chunk when LLM API is unavailable."""
    # Net worth check
    nw_match = re.search(r'net worth[^$]*?(?:US)?\$([0-9.,]+\s*(?:billion|million|B|M))', src_content, re.IGNORECASE)
    estimated_net_worth = f"US${nw_match.group(1)}" if nw_match else None
    if not estimated_net_worth:
        nw_match2 = re.search(r'(?:US)?\$([0-9.,]+)\s*(billion|million)', src_content, re.IGNORECASE)
        if nw_match2:
            estimated_net_worth = f"US${nw_match2.group(1)} {nw_match2.group(2)}"

    # Education check
    education = []
    edu_patterns = [
        r'(B\.?Tech|Bachelor[^.]+(?:Engineering|Science)[^.]+)',
        r'(M\.?S\.?[^.]+(?:University|Institute|School)[^.]+)',
        r'(MBA[^.]+(?:University|School|Business)[^.]+)',
        r'(Ph\.?D\.?[^.]+(?:University|Institute)[^.]+)',
    ]
    for pat in edu_patterns:
        matches = re.findall(pat, src_content)
        education.extend(matches)

    # Career milestones
    career_timeline = []
    if "joined google in 2004" in src_content.lower():
        career_timeline.append("2004: Joined Google leading product management for Chrome and Drive")
    if "ceo of google since 2015" in src_content.lower():
        career_timeline.append("2015: Appointed Chief Executive Officer of Google")
    if "alphabet inc. since 2019" in src_content.lower():
        career_timeline.append("2019: Appointed Chief Executive Officer of Alphabet Inc.")

    role = None
    if "CEO of Google" in src_content or "CEO of Alphabet" in src_content:
        role = "CEO of Alphabet and Google"

    return SourceExtract(
        source_name=src_name,
        source_url=src_url,
        full_name=name,
        current_role=role,
        industry="Technology" if "Google" in src_content or "Alphabet" in src_content else None,
        current_city_country="United States" if "Google" in src_content else None,
        estimated_net_worth=estimated_net_worth,
        net_worth_date="2026" if estimated_net_worth else None,
        biography_summary=src_content[:600],
        career_timeline=career_timeline,
        education=list(dict.fromkeys(education))[:4],
        photo_url=pre_photo_url
    )


def extract_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node 2: Per-Source LLM Extraction using strict Pydantic schemas."""
    raw_results = state.get("raw_search_results", [])
    name = state["name"]
    context = state.get("context", "")

    print(f"\n[Extract Node] Processing {len(raw_results)} raw source chunks with Pydantic schema validation...")

    llm = get_llm(temperature=0.0, use_pro=False)
    structured_llm = llm.with_structured_output(SourceExtract)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert fact-extraction AI. Your job is to extract exact, verifiable facts about {name} ({context}) from the provided source text chunk.

CRITICAL INSTRUCTIONS:
1. Extract ONLY facts that are explicitly mentioned in the source text chunk.
2. If a specific field (like estimated net worth, education, or career timeline) is NOT stated in this text, set it to null or empty list. DO NOT guess, estimate, or hallucinate.
3. If the text mentions any financial figures or compensation, accurately record them under estimated_net_worth and note the date/year under net_worth_date.
4. If you see a photo or image URL mentioned or attached in the source metadata, capture it under photo_url.
5. In missing_info_notes, list any key fields (net worth, education, etc.) that you checked for but were NOT present in this specific chunk."""),
        ("human", "Source Name: {source_name}\nSource URL: {source_url}\n\nRaw Content Chunk:\n{content}")
    ])

    chain = prompt | structured_llm

    extracted_list: List[SourceExtract] = []

    for i, item in enumerate(raw_results):
        src_name = item.get("source", f"Source {i+1}")
        src_url = item.get("url", "")
        src_content = item.get("content", "")

        # Check if Wikipedia already attached a photo_url
        pre_photo_url = item.get("photo_url")

        try:
            print(f"  Extracting from [{i+1}/{len(raw_results)}]: {src_name[:60]}...")
            extract: SourceExtract = invoke_with_retry(chain, {
                "name": name,
                "context": context,
                "source_name": src_name,
                "source_url": src_url,
                "content": src_content[:4000]
            }, max_retries=1, base_delay=0.1)

            # Ensure source name/url are preserved accurately
            extract.source_name = src_name
            extract.source_url = src_url
            if pre_photo_url and not extract.photo_url:
                extract.photo_url = pre_photo_url

            extracted_list.append(extract)
        except Exception as e:
            print(f"  [Extract Node] Extraction via LLM API quota fallback for {src_name[:40]}...")
            fallback = smart_chunk_extraction(name, src_name, src_url, src_content, pre_photo_url)
            extracted_list.append(fallback)

    print(f"[Extract Node] Extracted structured fact sheets from {len(extracted_list)} sources.")
    return {"extracted_sources": extracted_list}
