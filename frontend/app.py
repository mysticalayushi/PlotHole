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
from collections import defaultdict

# ---------------------------------------------------------------------------
# Pipeline imports (Person 1 + Person 2's modules)
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
# Styling helpers
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
.big-score {
    font-size: 4rem;
    font-weight: 800;
    text-align: center;
    padding: 1rem 0 0.25rem 0;
    line-height: 1;
}
.score-label {
    text-align: center;
    font-size: 1rem;
    color: #888;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}
.cell-card {
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
    border: 1px solid rgba(0,0,0,0.08);
}
.cell-green {
    background-color: rgba(46, 204, 113, 0.12);
    border-left: 5px solid #2ecc71;
}
.cell-yellow {
    background-color: rgba(241, 196, 15, 0.14);
    border-left: 5px solid #f1c40f;
}
.cell-red {
    background-color: rgba(231, 76, 60, 0.14);
    border-left: 5px solid #e74c3c;
}
.cell-header {
    font-weight: 700;
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.flag-explanation {
    background-color: rgba(0,0,0,0.04);
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 0.9rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def score_color(score: int) -> str:
    if score <= 30:
        return "#2ecc71"  # green
    elif score <= 70:
        return "#f1c40f"  # yellow
    else:
        return "#e74c3c"  # red


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
    st.title("🕳️ Plothole")
    st.caption("Narrative Debt Analyzer for Jupyter Notebooks")
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
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY is not set — the LLM analysis step will fail.")


# ---------------------------------------------------------------------------
# Main — upload
# ---------------------------------------------------------------------------
st.title("Narrative Debt Analyzer")
st.write("Upload a `.ipynb` file to check how coherent its analytical story is.")

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

    # --- Narrative debt score, front and center ---
    color = score_color(score)
    st.markdown(
        f'<div class="big-score" style="color:{color};">{score}/100</div>'
        f'<div class="score-label">Narrative Debt Score</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total cells", len(notebook_data.get("cells", [])))
    col2.metric("Flags raised", len(flags))
    dead_ends = notebook_data.get("narrative_graph", {}).get("dead_end_variables", [])
    col3.metric("Dead-end variables", len(dead_ends))

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
    st.info("👆 Upload a notebook to get started. Try one from `test_notebooks/` for a demo.")
