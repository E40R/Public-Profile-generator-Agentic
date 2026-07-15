import os
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from graph import create_profile_graph

load_dotenv()

st.set_page_config(
    page_title="Executive Profile Generator (LangGraph)",
    page_icon="🕴️",
    layout="wide"
)

st.title("🕴️ AI-Powered Executive Profile Generator")
st.markdown("""
This application orchestrates a **LangGraph multi-node workflow** to retrieve information from public sources (**Wikipedia, Forbes, News**), extract structured fact sheets via **Pydantic**, resolve conflicts across reports, and render a high-fidelity profile.
""")

with st.sidebar:
    st.header("⚙️ Settings & API")
    st.info("Uses Google Gemini or OpenAI defined in your environment (.env file).")
    st.markdown("### Architecture")
    st.markdown("""
    1. **Search Node:** Multi-source web retrieval
    2. **Extract Node:** Pydantic schema extraction
    3. **Combine Node:** Synthesizes & stores local master raw doc
    4. **Validate Node:** Loopback checkpoint
    5. **Render Node:** Jinja2 HTML, JSON & MD
    """)

# Input section
col1, col2 = st.columns([1, 1])
with col1:
    person_name = st.text_input("Person Name", value="Satya Nadella", placeholder="e.g. Satya Nadella")
with col2:
    person_context = st.text_input("Context / Current Role", value="CEO of Microsoft", placeholder="e.g. CEO of Microsoft")

if st.button("🚀 Generate Executive Profile", type="primary", use_container_width=True):
    if not person_name:
        st.error("Please enter a valid person name.")
    else:
        with st.status(f"Running LangGraph orchestration for '{person_name}'...", expanded=True) as status:
            st.write("🔍 Step 1/5: Querying authoritative sources (Wikipedia & Web search)...")
            graph = create_profile_graph()
            
            initial_state = {
                "name": person_name,
                "context": person_context,
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
                final_state = graph.invoke(initial_state)
                prof = final_state.get("profile")
                
                if prof:
                    status.update(label="✅ Executive Profile generated successfully!", state="complete", expanded=False)
                    
                    st.success(f"Profile generated for **{prof.full_name}** ({prof.current_role})!")
                    
                    # Display outputs in tabs
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "🎨 Rendered Infographic (HTML)", 
                        "📦 Structured Pydantic (JSON)", 
                        "📝 Clean Report (Markdown)", 
                        "📄 Master Combined Raw Sources"
                    ])
                    
                    with tab1:
                        html_path = final_state.get("output_html_path")
                        if html_path and os.path.exists(html_path):
                            with open(html_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            components.html(html_content, height=1050, scrolling=True)
                            
                            st.download_button(
                                label="⬇️ Download Formatted HTML Profile",
                                data=html_content,
                                file_name=f"{person_name.replace(' ', '_')}_profile.html",
                                mime="text/html"
                            )
                        else:
                            st.warning("HTML file not found.")
                            
                    with tab2:
                        st.json(prof.model_dump())
                        json_path = final_state.get("output_json_path")
                        if json_path and os.path.exists(json_path):
                            with open(json_path, "r", encoding="utf-8") as f:
                                st.download_button(
                                    label="⬇️ Download JSON Data",
                                    data=f.read(),
                                    file_name=f"{person_name.replace(' ', '_')}_profile.json",
                                    mime="application/json"
                                )
                                
                    with tab3:
                        md_path = final_state.get("output_md_path")
                        if md_path and os.path.exists(md_path):
                            with open(md_path, "r", encoding="utf-8") as f:
                                md_content = f.read()
                            st.markdown(md_content)
                            st.download_button(
                                label="⬇️ Download Markdown Report",
                                data=md_content,
                                file_name=f"{person_name.replace(' ', '_')}_profile.md",
                                mime="text/markdown"
                            )
                            
                    with tab4:
                        doc_path = final_state.get("combined_raw_doc_path")
                        if doc_path and os.path.exists(doc_path):
                            with open(doc_path, "r", encoding="utf-8") as f:
                                raw_doc_content = f.read()
                            st.markdown(f"**Local storage path:** `{doc_path}`")
                            st.markdown(raw_doc_content)
                            st.download_button(
                                label="⬇️ Download Combined Raw Document",
                                data=raw_doc_content,
                                file_name=f"{person_name.replace(' ', '_')}_combined_sources.md",
                                mime="text/markdown"
                            )
                else:
                    status.update(label="❌ Profile generation failed.", state="error")
            except Exception as e:
                status.update(label="❌ Error executing workflow", state="error")
                st.error(f"Error: {e}")
