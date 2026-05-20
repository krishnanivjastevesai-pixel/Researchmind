import streamlit as st
import time
from datetime import datetime
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain
from pipeline import run_research_pipeline
from utils import validate_topic, save_report, clear_cache, get_cache_stats, get_reports_stats, logger
from history import load_research_history, filter_history, delete_report, load_report_content, get_history_stats
from pdf_exporter import export_report_to_pdf

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",  # Changed to expanded so sidebar is visible
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── CSS Variables for theming ── */
:root {
    --bg-primary: #0a0a0f;
    --bg-secondary: rgba(255,255,255,0.03);
    --text-primary: #e8e4dc;
    --text-secondary: #a09890;
    --accent-primary: #ff8c32;
    --accent-secondary: #ff5a1a;
    --border-color: rgba(255,140,50,0.15);
    --success-color: #50c878;
}

[data-theme="light"] {
    --bg-primary: #ffffff;
    --bg-secondary: rgba(0,0,0,0.03);
    --text-primary: #1a1a1a;
    --text-secondary: #666666;
    --accent-primary: #ff8c32;
    --accent-secondary: #ff5a1a;
    --border-color: rgba(255,140,50,0.25);
    --success-color: #50c878;
}

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text-primary);
}

.stApp {
    background: var(--bg-primary);
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(255,140,50,0.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(255,80,30,0.08) 0%, transparent 55%);
}

/* ── Hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 3rem 4rem; max-width: 1200px; }

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 3.5rem 0 2.5rem;
    position: relative;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--accent-primary);
    margin-bottom: 1rem;
    opacity: 0.9;
}
.hero h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 800;
    line-height: 1.0;
    letter-spacing: -0.03em;
    color: var(--text-primary);
    margin: 0 0 1rem;
}
.hero h1 span {
    color: var(--accent-primary);
}
.hero-sub {
    font-size: 1.05rem;
    font-weight: 300;
    color: var(--text-secondary);
    max-width: 520px;
    margin: 0 auto;
    line-height: 1.65;
}

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-color), transparent);
    margin: 2rem 0;
}

/* ── Input card ── */
.input-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(8px);
}

/* ── Streamlit input overrides ── */
.stTextInput > div > div > input {
    background: var(--bg-secondary) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 0 0 3px rgba(255,140,50,0.12) !important;
}
.stTextInput > label {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--accent-primary) !important;
    font-weight: 500 !important;
}

/* ── Button ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
    color: #0a0a0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.04em !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.7rem 2.2rem !important;
    cursor: pointer !important;
    transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s !important;
    box-shadow: 0 4px 20px rgba(255,140,50,0.3) !important;
    width: 100%;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(255,140,50,0.4) !important;
    opacity: 0.95 !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Pipeline step cards ── */
.step-card {
    background: var(--bg-secondary);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.step-card.active {
    border-color: rgba(255,140,50,0.4);
    background: rgba(255,140,50,0.04);
}
.step-card.done {
    border-color: rgba(80,200,120,0.3);
    background: rgba(80,200,120,0.03);
}
.step-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: 14px 0 0 14px;
    background: rgba(255,255,255,0.05);
    transition: background 0.3s;
}
.step-card.active::before { background: var(--accent-primary); }
.step-card.done::before   { background: var(--success-color); }

.step-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.3rem;
}
.step-num {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    color: var(--accent-primary);
    opacity: 0.7;
}
.step-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--text-primary);
}
.step-status {
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
}
.status-waiting  { color: #555; }
.status-running  { color: var(--accent-primary); }
.status-done     { color: var(--success-color); }

/* ── Result panels ── */
.result-panel {
    background: var(--bg-secondary);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 1.8rem 2rem;
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}
.result-panel-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent-primary);
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid var(--border-color);
}
.result-content {
    font-size: 0.92rem;
    line-height: 1.8;
    color: var(--text-secondary);
    white-space: pre-wrap;
    font-family: 'DM Sans', sans-serif;
}

/* ── Report & feedback panels ── */
.report-panel {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-top: 1rem;
}
.feedback-panel {
    background: var(--bg-secondary);
    border: 1px solid rgba(80,200,120,0.2);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-top: 1rem;
}
.panel-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1.2rem;
    padding-bottom: 0.7rem;
}
.panel-label.orange {
    color: var(--accent-primary);
    border-bottom: 1px solid var(--border-color);
}
.panel-label.green {
    color: var(--success-color);
    border-bottom: 1px solid rgba(80,200,120,0.15);
}

/* ── Progress text ── */
.stSpinner > div { color: var(--accent-primary) !important; }

/* ── Expander ── */
details summary {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.1em !important;
    cursor: pointer;
}

/* ── Section heading ── */
.section-heading {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 2rem 0 1rem;
}

/* ── Toast-style notice ── */
.notice {
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-secondary);
    text-align: center;
    margin-top: 3rem;
    letter-spacing: 0.08em;
}

/* ── Keyboard shortcut hint ── */
.shortcut-hint {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.5rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-secondary);
    opacity: 0.7;
    transition: opacity 0.3s;
}
.shortcut-hint:hover {
    opacity: 1;
}

/* ── Loading skeleton ── */
@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}
.skeleton {
    background: linear-gradient(90deg, var(--bg-secondary) 25%, rgba(255,255,255,0.05) 50%, var(--bg-secondary) 75%);
    background-size: 1000px 100%;
    animation: shimmer 2s infinite;
    border-radius: 8px;
    height: 20px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


# ── Helper: render a step card ────────────────────────────────────────────────
def step_card(num: str, title: str, state: str, desc: str = ""):
    status_map = {
        "waiting": ("WAITING", "status-waiting"),
        "running": ("● RUNNING", "status-running"),
        "done":    ("✓ DONE",   "status-done"),
    }
    label, cls = status_map.get(state, ("", ""))
    card_cls = {"running": "active", "done": "done"}.get(state, "")
    st.markdown(f"""
    <div class="step-card {card_cls}">
        <div class="step-header">
            <span class="step-num">{num}</span>
            <span class="step-title">{title}</span>
            <span class="step-status {cls}">{label}</span>
        </div>
        {"<div style='font-size:0.82rem;color:#706860;margin-top:0.3rem;'>"+desc+"</div>" if desc else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Session state init ────────────────────────────────────────────────────────
for key in ("results", "running", "done", "progress", "progress_text", "error", "viewing_report", "model", "temperature", "report_length", "pdf_bytes", "pdf_filename"):
    if key not in st.session_state:
        if key == "results":
            st.session_state[key] = {}
        elif key in ("progress", "progress_text", "error", "viewing_report", "pdf_bytes", "pdf_filename"):
            st.session_state[key] = None
        elif key == "model":
            st.session_state[key] = "llama-3.3-70b-versatile"
        elif key == "temperature":
            st.session_state[key] = 0.0
        elif key == "report_length":
            st.session_state[key] = "Medium"
        else:
            st.session_state[key] = False


# ── Hero ──────────────────────────────────────────────────────────────────────
# Check if viewing a report
if st.session_state.viewing_report:
    report_content = load_report_content(st.session_state.viewing_report)
    
    if report_content:
        # Back button
        if st.button("← Back to Research"):
            st.session_state.viewing_report = None
            st.rerun()
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Display report
        st.markdown(report_content)
        
        # Download button
        st.download_button(
            label="⬇ Download Report",
            data=report_content,
            file_name=f"{st.session_state.viewing_report}.md",
            mime="text/markdown",
        )
    else:
        st.error("Report not found!")
        if st.button("← Back"):
            st.session_state.viewing_report = None
            st.rerun()
    
    st.stop()  # Don't show the rest of the page

st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">Multi-Agent AI System</div>
    <h1>Research<span>Mind</span></h1>
    <p class="hero-sub">
        Four specialized AI agents collaborate — searching, scraping, writing,
        and critiquing — to deliver a polished research report on any topic.
    </p>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)


# ── Layout: input left, pipeline right ───────────────────────────────────────
col_input, col_spacer, col_pipeline = st.columns([5, 0.5, 4])

with col_input:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    topic = st.text_input(
        "Research Topic",
        placeholder="e.g. Quantum computing breakthroughs in 2025",
        key="topic_input",
        label_visibility="visible",
    )
    run_btn = st.button("⚡  Run Research Pipeline", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Example chips
    st.markdown("""
    <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.5rem;">
        <span style="font-family:'DM Mono',monospace;font-size:0.68rem;color:#605850;letter-spacing:0.1em;">TRY →</span>
    """, unsafe_allow_html=True)
    examples = ["LLM agents 2025", "CRISPR gene editing", "Fusion energy progress"]
    for ex in examples:
        st.markdown(f"""
        <span style="
            background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);
            border-radius:6px;
            padding:0.25rem 0.7rem;
            font-size:0.75rem;
            color:#a09890;
            font-family:'DM Sans',sans-serif;
            cursor:default;
        ">{ex}</span>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_pipeline:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)

    r = st.session_state.results
    done = st.session_state.done

    def s(step):
        if not r:
            return "waiting"
        steps_map = {
            "search": "search_results",
            "reader": "scraped_content",
            "writer": "report",
            "critic": "feedback"
        }
        
        # Check if this step is done
        if steps_map[step] in r:
            return "done"
        
        # Check if pipeline is running
        if st.session_state.running:
            # Find which step is currently running
            for step_name, result_key in steps_map.items():
                if result_key not in r:
                    return "running" if step_name == step else "waiting"
        
        return "waiting"

    step_card("01", "Search Agent",  s("search"), "Gathers recent web information")
    step_card("02", "Reader Agent",  s("reader"), "Scrapes & extracts deep content")
    step_card("03", "Writer Chain",  s("writer"), "Drafts the full research report")
    step_card("04", "Critic Chain",  s("critic"), "Reviews & scores the report")


# ── Run pipeline ──────────────────────────────────────────────────────────────
if run_btn:
    if not topic.strip():
        st.warning("⚠️ Please enter a research topic first.")
    else:
        # Validate topic
        is_valid, error_msg = validate_topic(topic)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.session_state.results = {}
            st.session_state.running = True
            st.session_state.done = False
            st.session_state.error = None
            st.session_state.progress = 0
            st.session_state.progress_text = "Starting..."
            st.session_state.pdf_bytes = None  # Clear previous PDF
            st.session_state.pdf_filename = None
            logger.info(f"Starting research for topic: {topic}")
            st.rerun()

if st.session_state.running and not st.session_state.done:
    topic_val = st.session_state.topic_input
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    def update_progress(percent, text):
        st.session_state.progress = percent
        st.session_state.progress_text = text
        progress_bar.progress(percent)
        status_text.text(text)
    
    try:
        # Run the pipeline with progress callback
        results = run_research_pipeline(topic_val, progress_callback=update_progress)
        
        # Store results
        st.session_state.results = results
        st.session_state.running = False
        st.session_state.done = True
        
        # Auto-save report
        try:
            filepath = save_report(
                topic=results['topic'],
                report=results['report'],
                feedback=results['feedback'],
                format='md'
            )
            st.session_state.saved_filepath = str(filepath)
            logger.info(f"Report auto-saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to auto-save report: {e}")
        
        st.rerun()
    
    except Exception as e:
        st.session_state.error = str(e)
        st.session_state.running = False
        st.session_state.done = False
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        st.rerun()

# Show error if any
if st.session_state.error:
    st.error(f"❌ Pipeline failed: {st.session_state.error}")
    if st.button("Try Again"):
        st.session_state.error = None
        st.rerun()


# ── Results display ───────────────────────────────────────────────────────────
r = st.session_state.results

if r:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-heading">Results</div>', unsafe_allow_html=True)

    # Raw outputs in expanders
    if "search_results" in r:
        with st.expander("🔍 Search Results (raw)", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">Search Agent Output</div>'
                        f'<div class="result-content">{r["search_results"]}</div></div>', unsafe_allow_html=True)

    if "scraped_content" in r:
        with st.expander("📄 Scraped Content (raw)", expanded=False):
            st.markdown(f'<div class="result-panel"><div class="result-panel-title">Reader Agent Output</div>'
                        f'<div class="result-content">{r["scraped_content"]}</div></div>', unsafe_allow_html=True)

    # Final report
    if "report" in r:
        st.markdown("""
        <div class="report-panel">
            <div class="panel-label orange">📝 Final Research Report</div>
        """, unsafe_allow_html=True)
        st.markdown(r["report"])   # render markdown natively
        st.markdown("</div>", unsafe_allow_html=True)

        # Download options - All in one row
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 Download Markdown",
                data=r["report"],
                file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            # TXT export
            txt_content = f"Research Report: {r.get('topic', 'Unknown')}\n\n{r['report']}\n\n---\n\nCritic Feedback:\n{r.get('feedback', '')}"
            st.download_button(
                label="📝 Download TXT",
                data=txt_content,
                file_name=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col3:
            # PDF export - Generate and download in one click
            if st.button("📕 Download PDF", use_container_width=True, key="pdf_download_btn"):
                try:
                    with st.spinner("Generating PDF..."):
                        pdf_path = export_report_to_pdf(
                            topic=r.get('topic', 'Research Report'),
                            report=r['report'],
                            feedback=r.get('feedback', '')
                        )
                        
                        # Read PDF file
                        with open(pdf_path, 'rb') as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        # Store in session state for download
                        st.session_state.pdf_bytes = pdf_bytes
                        st.session_state.pdf_filename = pdf_path.name
                        st.success("✅ PDF ready!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ PDF generation failed: {str(e)}")
                    logger.error(f"PDF generation failed: {e}", exc_info=True)
        
        # Show PDF download button if PDF was generated
        if 'pdf_bytes' in st.session_state and st.session_state.pdf_bytes:
            st.download_button(
                label="⬇️ Download Generated PDF",
                data=st.session_state.pdf_bytes,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True,
                key="pdf_download_final"
            )
        
        # Show auto-saved path
        if "saved_filepath" in st.session_state:
            st.info(f"✅ Report auto-saved to: `{st.session_state.saved_filepath}`")

    # Critic feedback
    if "feedback" in r:
        st.markdown("""
        <div class="feedback-panel">
            <div class="panel-label green">🧐 Critic Feedback</div>
        """, unsafe_allow_html=True)
        st.markdown(r["feedback"])
        st.markdown("</div>", unsafe_allow_html=True)


# ── Sidebar: Settings & Stats ────────────────────────────────────────────────
with st.sidebar:
    # Tab selection
    tab_selection = st.radio(
        "Navigation",
        ["🏠 Home", "📚 History", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if tab_selection == "📚 History":
        st.markdown("### 📚 Research History")
        
        # Load history
        history = load_research_history()
        
        if history:
            # Search filter
            search_query = st.text_input("🔍 Search topics", placeholder="Search...")
            
            # Score filter
            min_score = st.slider("Minimum Score", 0.0, 10.0, 0.0, 0.5)
            
            # Apply filters
            filtered = filter_history(
                history,
                query=search_query if search_query else None,
                min_score=min_score if min_score > 0 else None
            )
            
            st.markdown(f"**{len(filtered)} reports found**")
            st.markdown("---")
            
            # Display history items
            for report in filtered[:10]:  # Show max 10 in sidebar
                with st.container():
                    # Report card
                    score_color = "🟢" if report['score'] and report['score'] >= 8 else "🟡" if report['score'] and report['score'] >= 6 else "🔴"
                    score_text = f"{score_color} {report['score']}/10" if report['score'] else "⚪ N/A"
                    
                    st.markdown(f"**{report['topic'][:40]}{'...' if len(report['topic']) > 40 else ''}**")
                    st.markdown(f"{score_text} · {report['relative_time']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📖 View", key=f"view_{report['id']}"):
                            st.session_state.viewing_report = report['id']
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Del", key=f"del_{report['id']}"):
                            if delete_report(report['id']):
                                st.success("Deleted!")
                                time.sleep(0.5)
                                st.rerun()
                    
                    st.markdown("---")
            
            # Show stats
            stats = get_history_stats(history)
            st.markdown("### 📊 Statistics")
            st.metric("Total Reports", stats['total_reports'])
            st.metric("Avg Score", f"{stats['avg_score']}/10")
            st.metric("Unique Topics", stats['topics_count'])
        
        else:
            st.info("No research history yet. Start by running your first research!")
    
    elif tab_selection == "⚙️ Settings":
        st.markdown("### ⚙️ Settings")
        
        # Cache management
        st.markdown("#### 📦 Cache Management")
        cache_stats = get_cache_stats()
        st.metric("Cached Items", cache_stats['total_files'])
        st.metric("Cache Size", f"{cache_stats['total_size_mb']} MB")
        
        if st.button("🗑️ Clear Cache"):
            count = clear_cache()
            st.success(f"Cleared {count} cache files!")
            st.rerun()
        
        st.markdown("---")
        
        # Reports stats
        st.markdown("#### 📊 Reports")
        reports_stats = get_reports_stats()
        st.metric("Total Reports", reports_stats['total_reports'])
        st.metric("Reports Size", f"{reports_stats['total_size_mb']} MB")
        
        st.markdown("---")
        
        # Advanced settings
        st.markdown("#### 🎛️ Advanced")
        
        # Model selection
        model_options = [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ]
        selected_model = st.selectbox(
            "Model",
            model_options,
            index=0,
            help="Select the Groq model to use"
        )
        
        # Temperature
        temperature = st.slider(
            "Temperature",
            0.0, 1.0, 0.0, 0.1,
            help="Higher = more creative, Lower = more focused"
        )
        
        # Report length
        report_length = st.select_slider(
            "Report Length",
            options=["Short", "Medium", "Long"],
            value="Medium"
        )
        
        # Save settings to session state
        st.session_state.model = selected_model
        st.session_state.temperature = temperature
        st.session_state.report_length = report_length
        
        if st.button("💾 Save Settings"):
            st.success("Settings saved!")
    
    else:  # Home tab
        st.markdown("### 🏠 Quick Stats")
        reports_stats = get_reports_stats()
        st.metric("Total Reports", reports_stats['total_reports'])
        
        cache_stats = get_cache_stats()
        st.metric("Cache Size", f"{cache_stats['total_size_mb']} MB")
    

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="notice">
    ResearchMind · Powered by LangChain multi-agent pipeline · Built with Streamlit
</div>
<div class="shortcut-hint">
    💡 Tip: Press Ctrl+Enter in the input field to run research
</div>
""", unsafe_allow_html=True)