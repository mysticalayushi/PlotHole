# PlotHole: Notebook Narrative Debt Detector

A tool that flags where a data science notebook's story breaks down — even when all the code runs perfectly.

---

## Project Status

### ✅ Completed — Notebook Parser & Data Extraction (Person 1)

**What's done:**
- `parser/parse_notebook.py` reads any `.ipynb` file and extracts every cell (code + markdown), including cell type, source content, and outputs.
- For every code cell, extracts which variables are **created** (assigned) and which are **used** (referenced), using Python's `ast` module.
- Builds a "narrative graph" across the whole notebook — cross-references all cells to detect **dead-end variables**: variables created in one cell that are never used again in any later cell.
- Everything is packaged into a single function for easy use:

```python
from parser.parse_notebook import get_notebook_analysis

result = get_notebook_analysis('path/to/notebook.ipynb')
```

**Output format** — `get_notebook_analysis()` returns:
```python
{
    'cells': [
        {
            'index': 0,
            'type': 'code',  # or 'markdown'
            'source': '...',
            'outputs': [...],
            'variables': {
                'assigned': ['df', 'model'],
                'used': ['pd', 'df'],
                'parse_error': False
            }
        },
        ...
    ],
    'narrative_graph': {
        'variable_history': {...},
        'dead_end_variables': [{'variable': 'X', 'created_at': 5}, ...]
    }
}
```

Tested on real Kaggle notebooks in `test_notebooks/`.

---

### ✅ Completed — LLM Analysis Layer (Person 2)

**What's done:**
- `llm_analysis/analyze.py` takes the output of `get_notebook_analysis()` and uses Claude (Anthropic API) to detect narrative coherence issues.
- Detects four issue types:
  - **orphaned_exploration** — a cell does meaningful analysis but its result is never referenced again
  - **markdown_code_gap** — markdown describes *what* the code does rather than *why* it matters
  - **conclusion_evidence_mismatch** — final conclusions aren't backed by earlier cell outputs
  - **dead_end_variable** — variables created but never meaningfully used (filtered by LLM to avoid false positives like loop counters)
- Returns a clean, validated list of flags with specific explanations:

```python
[
    {
        "cell_index": 14,
        "issue_type": "orphaned_exploration",
        "explanation": "This cell computes feature importances but is never referenced again."
    },
    ...
]
```

- `compute_narrative_debt_score(flags, notebook_data)` turns flags into a single 0-100 score (flags per code cell, scaled).
- `test_llm_analysis.py` lets you run the full pipeline against any notebook.

**Setup required:** needs `ANTHROPIC_API_KEY` set as an environment variable (get one from console.anthropic.com — includes free $5 credit for testing).

---

### ✅ Completed — Frontend / Demo Interface (Person 3)

**What's done:**
- `frontend/app.py` — a full Streamlit web app that ties the entire pipeline together
- File upload widget for `.ipynb` files
- Runs the full pipeline on upload: `get_notebook_analysis()` → `analyze_notebook()` → `compute_narrative_debt_score()`
- Displays the narrative debt score prominently with color coding (green/yellow/red)
- Cell-by-cell view: every cell shown with color-coded severity based on flag count
- Flag summary view: all flags grouped by issue type
- Expandable explanations for each flagged cell
- Graceful error handling for missing API keys and pipeline import issues

**Confirmed working:** UI renders correctly, file upload works, pipeline integration is wired correctly end-to-end.

**Known blocker (non-code issue):** Anthropic API credit balance needs to be topped up before live testing/demo — this is a billing setup step, not a bug.

**Run it:**
```bash
streamlit run frontend/app.py
```

---

### 🔜 Next Up — Docs, Testing & Submission (Person 4)

**Goal:** Get everything ready for the final submission — polish, test, document, and package.

**What to do:**

1. **Add Anthropic API credits** (blocking item)
   - Go to console.anthropic.com → Plans & Billing
   - Add credits so the LLM analysis layer can actually run for the demo
   - Test end-to-end once resolved: `streamlit run frontend/app.py`, upload a notebook from `test_notebooks/`, confirm flags appear

2. **Curate more test notebooks**
   - Add 2-3 more notebooks to `test_notebooks/` — a mix of clean and deliberately messy ones
   - Consider hand-editing one notebook to introduce an obvious narrative flaw for a guaranteed demo "gotcha" moment

3. **QA the whole pipeline**
   - Try uploading different notebooks and check for bugs, crashes, or confusing UI moments
   - Report any issues found to the team

4. **Write project documentation**
   - Problem statement, approach, architecture overview (parser → LLM analysis → frontend)
   - Known limitations (e.g. LLM judgment isn't ground truth, notebook-only scope for now)
   - Future vision (extending to pentest reports/postmortems)

5. **Fill the official PPT template**
   - Embed: Project Documentation link, GitHub Repository link, Working Demo link
   - Optional but recommended: record a short YouTube video explaining the problem, solution, and impact — embed link in PPT

6. **Prepare demo script**
   - Pick a messy notebook to show live
   - Script the "gotcha" moment (e.g. "Cell 14 computes feature importances but it's never used again")
   - Rehearse timing so the live demo is smooth

**Deliverable:** Final PPT submitted via the official template, before **August 12, 2026, 11:59 PM IST**. Remember: rolling evaluation means earlier submission = earlier results.