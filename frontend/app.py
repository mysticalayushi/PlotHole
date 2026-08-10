"""
Plothole — Notebook Narrative Debt Analyzer
Frontend / Demo Interface (Streamlit)

Run with:
    streamlit run frontend/app.py
"""

import streamlit as st
import tempfile
import os
import json
import sys
import math
from collections import defaultdict

# ---------------------------------------------------------------------------
# Make sure the project root (parent of this file's folder) is importable,
# since Streamlit only adds this file's own folder to sys.path by default.
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------------------------
# Pipeline imports (Person 1 + Person 2's modules) — UNCHANGED
# ---------------------------------------------------------------------------
try:
    from parser.parse_notebook import get_notebook_analysis
    from llm_analysis.analyze import analyze_notebook, compute_narrative_debt_score
    PIPELINE_AVAILABLE = True
    PIPELINE_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover
    PIPELINE_AVAILABLE = False
    PIPELINE_IMPORT_ERROR = str(e)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Plothole — Narrative Debt Analyzer",
    page_icon="🕳️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Styling — palette / typography overhaul (item 4)
#   - Purple → blue gradient identity, dark canvas, 'Inter' type
#   - New component classes added for hero (1), badges (2), gauge (3),
#     and stat cards (5). Existing cell-card / flag-explanation rules
#     are kept (severity color coding is functional, not decorative)
#     but softened slightly to sit on the new dark/purple canvas.
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --ph-purple: #8b5cf6;
    --ph-blue: #3b82f6;
    --ph-pink: #f472b6;
    --ph-orange: #fb923c;
    --ph-gradient: linear-gradient(135deg, var(--ph-purple), var(--ph-blue));
    --ph-card-bg: rgba(255,255,255,0.035);
    --ph-card-border: rgba(255,255,255,0.09);
    --ph-text-dim: #9ca3af;
}

html, body, .stApp, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 12% -5%, rgba(139,92,246,0.16), transparent 42%),
        radial-gradient(circle at 88% 8%, rgba(59,130,246,0.13), transparent 46%),
        #0b0b14;
}

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.02);
    border-right: 1px solid var(--ph-card-border);
}

/* ---- Hero (item 1) ---- */
.ph-hero {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    padding: 1.75rem 2rem;
    margin-bottom: 1.5rem;
    border-radius: 18px;
    background: var(--ph-card-bg);
    border: 1px solid var(--ph-card-border);
}
.ph-logo-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.ph-logo-icon { font-size: 2rem; }
.ph-logo-title {
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
    color: #f5f5fa;
}
.ph-logo-accent {
    background: var(--ph-gradient);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.ph-tagline {
    font-size: 1.05rem;
    font-weight: 600;
    color: #c7c9f5;
    margin: 0.15rem 0 0.5rem 0;
}
.ph-subtext {
    font-size: 0.92rem;
    color: var(--ph-text-dim);
    max-width: 46ch;
    margin: 0 0 1rem 0;
    line-height: 1.5;
}

/* ---- Badge pills (item 2) ---- */
.ph-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.ph-badge {
    font-size: 0.78rem;
    font-weight: 600;
    color: #e5e7f5;
    background: rgba(255,255,255,0.06);
    border: 1px solid var(--ph-card-border);
    border-radius: 999px;
    padding: 0.3rem 0.75rem;
    white-space: nowrap;
}

.ph-hero-art { flex-shrink: 0; width: 220px; }
.ph-hero-art svg { width: 100%; height: auto; }

/* Sidebar title, restyled to match palette (item 4) */
.ph-sidebar-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #f5f5fa;
    letter-spacing: -0.01em;
}
.ph-sidebar-caption {
    font-size: 0.85rem;
    color: var(--ph-text-dim);
    margin-bottom: 0.5rem;
}

/* ---- Score gauge (item 3) ---- */
.ph-gauge-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0 1.25rem 0;
}
.ph-gauge { width: 210px; height: 210px; }
.ph-gauge-bg { fill: none; stroke: rgba(255,255,255,0.08); stroke-width: 14; }
.ph-gauge-fg {
    fill: none;
    stroke-width: 14;
    stroke-linecap: round;
    transition: stroke-dashoffset 0.6s ease;
}
.ph-gauge-score {
    font-size: 44px;
    font-weight: 800;
    font-family: 'Inter', sans-serif;
}
.ph-gauge-max { font-size: 14px; fill: var(--ph-text-dim); font-family: 'Inter', sans-serif; }
.ph-gauge-label {
    text-align: center;
    font-size: 0.85rem;
    color: var(--ph-text-dim);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 0.25rem;
}

/* ---- Stat cards (item 5) ---- */
.ph-stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.9rem;
    margin-bottom: 1rem;
}
.ph-stat-card {
    background: var(--ph-card-bg);
    border: 1px solid var(--ph-card-border);
    border-radius: 14px;
    padding: 1rem 1.1rem;
}
.ph-stat-icon { font-size: 1.3rem; margin-bottom: 0.35rem; }
.ph-stat-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #f5f5fa;
    line-height: 1.1;
}
.ph-stat-label {
    font-size: 0.78rem;
    color: var(--ph-text-dim);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-top: 0.15rem;
}

@media (max-width: 900px) {
    .ph-hero { flex-direction: column; align-items: flex-start; }
    .ph-hero-art { width: 160px; }
    .ph-stats-row { grid-template-columns: repeat(2, 1fr); }
}

/* ---- Existing cell / flag cards, softened for the dark canvas ---- */
.cell-card {
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
.cell-green {
    background-color: rgba(46, 204, 113, 0.10);
    border-left: 5px solid #2ecc71;
}
.cell-yellow {
    background-color: rgba(241, 196, 15, 0.12);
    border-left: 5px solid #f1c40f;
}
.cell-red {
    background-color: rgba(231, 76, 60, 0.12);
    border-left: 5px solid #e74c3c;
}
.cell-header {
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--ph-text-dim);
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.flag-explanation {
    background-color: rgba(255,255,255,0.04);
    border-radius: 8px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 0.9rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Abstract "plot hole in a notebook" illustration for the hero (item 1).
# Original SVG, not a copy of any reference image — a notebook card with a
# broken narrative line (dashed gap) and a warning badge.
HERO_ART_SVG = """
<div class="ph-hero-art">
<svg viewBox="0 0 320 260" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="phGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6"/>
      <stop offset="100%" stop-color="#3b82f6"/>
    </linearGradient>
    <linearGradient id="phGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f472b6"/>
      <stop offset="100%" stop-color="#fb923c"/>
    </linearGradient>
  </defs>
  <circle cx="160" cy="130" r="115" fill="url(#phGrad1)" opacity="0.10"/>
  <rect x="55" y="45" width="210" height="165" rx="18" fill="#13131f" stroke="url(#phGrad1)" stroke-width="2"/>
  <rect x="78" y="72" width="120" height="10" rx="5" fill="#3b3b55"/>
  <rect x="78" y="94" width="164" height="10" rx="5" fill="#3b3b55"/>
  <rect x="78" y="116" width="90" height="10" rx="5" fill="url(#phGrad1)"/>
  <rect x="176" y="116" width="66" height="10" rx="5" fill="none" stroke="#ef4444" stroke-width="1.5" stroke-dasharray="4 4"/>
  <rect x="78" y="138" width="140" height="10" rx="5" fill="#3b3b55" opacity="0.45"/>
  <rect x="78" y="160" width="100" height="10" rx="5" fill="#3b3b55" opacity="0.3"/>
  <circle cx="238" cy="66" r="23" fill="url(#phGrad2)"/>
  <text x="238" y="75" text-anchor="middle" font-size="26" font-weight="800" fill="#13131f" font-family="Inter, sans-serif">!</text>
</svg>
</div>
"""


def score_color(score: int) -> str:
    if score <= 30:
        return "#2ecc71"  # green
    elif score <= 70:
        return "#f1c40f"  # yellow
    else:
        return "#e74c3c"  # red


def render_gauge(score: int) -> str:
    """Build the circular narrative-debt-score gauge (item 3)."""
    radius = 80
    circumference = 2 * math.pi * radius
    score = max(0, min(100, score))
    offset = circumference * (1 - score / 100)
    color = score_color(score)
    return f"""
    <div class="ph-gauge-wrap">
      <svg viewBox="0 0 200 200" class="ph-gauge">
        <circle cx="100" cy="100" r="{radius}" class="ph-gauge-bg" />
        <circle cx="100" cy="100" r="{radius}" class="ph-gauge-fg"
          stroke="{color}"
          stroke-dasharray="{circumference:.2f}"
          stroke-dashoffset="{offset:.2f}"
          transform="rotate(-90 100 100)" />
        <text x="100" y="97" text-anchor="middle" class="ph-gauge-score" fill="{color}">{score}</text>
        <text x="100" y="120" text-anchor="middle" class="ph-gauge-max">/100</text>
      </svg>
      <div class="ph-gauge-label">Narrative Debt Score</div>
    </div>
    """


def render_stats_row(total_cells: int, num_flags: int, score: int, num_dead_ends: int) -> str:
    """Build the 4-card stat row (item 5) from data already computed by the pipeline."""
    return f"""
    <div class="ph-stats-row">
      <div class="ph-stat-card">
        <div class="ph-stat-icon">📓</div>
        <div class="ph-stat-value">{total_cells}</div>
        <div class="ph-stat-label">Cells Analyzed</div>
      </div>
      <div class="ph-stat-card">
        <div class="ph-stat-icon">🚩</div>
        <div class="ph-stat-value">{num_flags}</div>
        <div class="ph-stat-label">Flags Detected</div>
      </div>
      <div class="ph-stat-card">
        <div class="ph-stat-icon">🎯</div>
        <div class="ph-stat-value">{score}/100</div>
        <div class="ph-stat-label">Narrative Score</div>
      </div>
      <div class="ph-stat-card">
        <div class="ph-stat-icon">🧵</div>
        <div class="ph-stat-value">{num_dead_ends}</div>
        <div class="ph-stat-label">Dead-End Variables</div>
      </div>
    </div>
    """


def render_outputs(outputs, limit: int = 800) -> str:
    """Turn raw nbformat cell outputs into a short text preview for display."""
    if not outputs:
        return ""
    parts = []
    for out in outputs:
        if not isinstance(out, dict):
            continue
        if "text" in out:
            text = out["text"]
            parts.append(text if isinstance(text, str) else "".join(text))
        elif "data" in out:
            data = out["data"]
            if "text/plain" in data:
                tp = data["text/plain"]
                parts.append(tp if isinstance(tp, str) else "".join(tp))
            elif any(k.startswith("image/") for k in data):
                parts.append("[image output]")
            else:
                parts.append(f"[{', '.join(data.keys())} output]")
        elif "ename" in out:
            parts.append(f"[ERROR: {out.get('ename')}: {out.get('evalue')}]")
    combined = "\n".join(p for p in parts if p).strip()
    if len(combined) > limit:
        combined = combined[:limit] + "... [truncated]"
    return combined


def cell_severity_class(num_flags: int) -> str:
    if num_flags == 0:
        return "cell-green"
    elif num_flags <= 2:
        return "cell-yellow"
    else:
        return "cell-red"


ISSUE_TYPE_LABELS = {
    "orphaned_exploration": "🔍 Orphaned Exploration",
    "markdown_code_gap": "📝 Markdown/Code Gap",
    "conclusion_evidence_mismatch": "⚖️ Conclusion/Evidence Mismatch",
    "dead_end_variable": "🧵 Dead-End Variable",
}


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="ph-sidebar-title">🕳️ Plot<span class="ph-logo-accent">Hole</span></div>'
        '<div class="ph-sidebar-caption">Narrative Debt Analyzer for Jupyter Notebooks</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Upload a notebook to see where the story of the analysis "
        "breaks down — dead-end variables, orphaned exploration, "
        "and conclusions that outrun their evidence."
    )
    st.divider()
    st.markdown("**Flag types**")
    for label in ISSUE_TYPE_LABELS.values():
        st.markdown(f"- {label}")
    st.divider()
    if not PIPELINE_AVAILABLE:
        st.error(
            "Pipeline modules not found. Run this app from the project "
            "root so `parser/` and `llm_analysis/` are importable.\n\n"
            f"Import error: {PIPELINE_IMPORT_ERROR}"
        )
    if not os.environ.get("GROQ_API_KEY"):
        st.warning("GROQ_API_KEY is not set — the LLM analysis step will fail.")


# ---------------------------------------------------------------------------
# Main — hero (item 1) + badges (item 2), replacing the old plain title
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="ph-hero">
      <div class="ph-hero-text">
        <div class="ph-logo-row">
          <span class="ph-logo-icon">🕳️</span>
          <h1 class="ph-logo-title">Plot<span class="ph-logo-accent">Hole</span></h1>
        </div>
        <p class="ph-tagline">Notebook Narrative Debt Detector</p>
        <p class="ph-subtext">Upload a <code>.ipynb</code> file to check how coherent its
        analytical story is — we surface orphaned exploration, code gaps, weak
        conclusions, and dead ends.</p>
        <div class="ph-badges">
          <span class="ph-badge">🐍 Python 3.11</span>
          <span class="ph-badge">🔥 Streamlit</span>
          <span class="ph-badge">⚡ Groq · Llama 3.3 70B</span>
          <span class="ph-badge">📄 MIT License</span>
        </div>
      </div>
      {HERO_ART_SVG}
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Upload notebook", type=["ipynb"])

# Session state to avoid re-running pipeline on every widget interaction
if "results" not in st.session_state:
    st.session_state.results = None
if "last_filename" not in st.session_state:
    st.session_state.last_filename = None

if uploaded_file is not None:
    # Re-run pipeline only if a new file was uploaded
    if st.session_state.last_filename != uploaded_file.name:
        if not PIPELINE_AVAILABLE:
            st.error("Cannot process notebook — pipeline modules failed to import (see sidebar).")
        else:
            with st.spinner("Parsing notebook and analyzing narrative coherence..."):
                try:
                    # Save uploaded file to a temp path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".ipynb") as tmp:
                        tmp.write(uploaded_file.getvalue())
                        tmp_path = tmp.name

                    notebook_data = get_notebook_analysis(tmp_path)
                    flags = analyze_notebook(notebook_data)
                    score = compute_narrative_debt_score(flags, notebook_data)

                    os.unlink(tmp_path)

                    st.session_state.results = {
                        "notebook_data": notebook_data,
                        "flags": flags,
                        "score": score,
                    }
                    st.session_state.last_filename = uploaded_file.name
                except Exception as e:
                    st.session_state.results = None
                    st.error(f"Something went wrong while analyzing the notebook: {e}")

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.results:
    notebook_data = st.session_state.results["notebook_data"]
    flags = st.session_state.results["flags"]
    score = st.session_state.results["score"]

    total_cells = len(notebook_data.get("cells", []))
    dead_ends = notebook_data.get("narrative_graph", {}).get("dead_end_variables", [])

    # --- Narrative debt score, front and center: circular gauge (item 3) ---
    st.markdown(render_gauge(score), unsafe_allow_html=True)

    # --- Stat row (item 5) ---
    st.markdown(
        render_stats_row(total_cells, len(flags), score, len(dead_ends)),
        unsafe_allow_html=True,
    )

    st.divider()

    # Group flags by cell index for quick lookup
    flags_by_cell = defaultdict(list)
    for f in flags:
        flags_by_cell[f.get("cell_index")].append(f)

    tab_cells, tab_flags = st.tabs(["📓 Cell-by-cell view", "🚩 Flag summary"])

    # --- Cell-by-cell view ---
    with tab_cells:
        st.caption("Every cell from the notebook, color-coded by how many issues it triggered.")
        for cell in notebook_data.get("cells", []):
            idx = cell.get("index")
            cell_flags = flags_by_cell.get(idx, [])
            css_class = cell_severity_class(len(cell_flags))
            cell_type = cell.get("type", "code")

            with st.container():
                st.markdown(
                    f'<div class="cell-card {css_class}">'
                    f'<div class="cell-header">Cell {idx} · {cell_type}'
                    f'{" · " + str(len(cell_flags)) + " flag(s)" if cell_flags else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if cell_type == "markdown":
                    st.markdown(cell.get("source", ""))
                else:
                    st.code(cell.get("source", ""), language="python")
                    output_text = render_outputs(cell.get("outputs"))
                    if output_text:
                        st.text(output_text)

                if cell_flags:
                    with st.expander(f"⚠️ {len(cell_flags)} issue(s) in this cell", expanded=False):
                        for f in cell_flags:
                            label = ISSUE_TYPE_LABELS.get(f.get("issue_type"), f.get("issue_type"))
                            st.markdown(
                                f'<div class="flag-explanation"><b>{label}</b><br>{f.get("explanation", "")}</div>',
                                unsafe_allow_html=True,
                            )
                st.markdown("</div>", unsafe_allow_html=True)

    # --- Flag summary view ---
    with tab_flags:
        if not flags:
            st.success("No narrative issues detected — this notebook tells a clean story! 🎉")
        else:
            st.caption(f"{len(flags)} flag(s) found, grouped by issue type.")
            grouped = defaultdict(list)
            for f in flags:
                grouped[f.get("issue_type", "other")].append(f)

            for issue_type, group in grouped.items():
                label = ISSUE_TYPE_LABELS.get(issue_type, issue_type)
                st.subheader(f"{label} ({len(group)})")
                for f in sorted(group, key=lambda x: x.get("cell_index", 0)):
                    st.markdown(
                        f'<div class="flag-explanation">'
                        f'<b>Cell {f.get("cell_index")}</b> — {f.get("explanation", "")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.write("")

else:
    st.info("👆 Upload a notebook to get started")