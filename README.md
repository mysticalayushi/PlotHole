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

### 🔜 Next Up — Frontend / Demo Interface (Person 3)

**Goal:** Build a Streamlit web app that ties the whole pipeline together and displays results visually to judges.

**What to build:**

1. **File upload interface**
   - A file upload widget that accepts `.ipynb` files
   - Show a loading indicator while processing

2. **End-to-end pipeline call**
```python
   from parser.parse_notebook import get_notebook_analysis
   from llm_analysis.analyze import analyze_notebook, compute_narrative_debt_score

   notebook_data = get_notebook_analysis(uploaded_notebook_path)
   flags = analyze_notebook(notebook_data)
   score = compute_narrative_debt_score(flags, notebook_data)
```

3. **Display the narrative debt score prominently**
   - Show as a large metric/number at the top (e.g. "Narrative Debt Score: 45/100")
   - Color code: green for low scores (0-30), yellow for medium (30-70), red for high (70-100)

4. **Cell-by-cell display**
   - Show every cell from the notebook in order (code and markdown)
   - Color code cells:
     - **Green** — no flags reference this cell
     - **Yellow** — 1-2 flags
     - **Red** — 3+ flags
   - Clicking or hovering a flagged cell shows its `explanation`

5. **Flag summary section**
   - List all flags with their `cell_index`, `issue_type`, and `explanation`
   - Grouped by issue type or by severity for readability

6. **Test it locally**
   - Use notebooks from `test_notebooks/` to verify the UI works
   - Make sure the flow is smooth: upload → process → display results

**Tech stack:**
- Streamlit for the web interface (already in `requirements.txt`)
- Python (call your existing parser/analyzer functions directly)

**Deliverable:** `frontend/app.py` — runnable with:
```bash
streamlit run frontend/app.py
```

**Demo script for judges:**
1. Upload a deliberately messy Kaggle notebook
2. Show the narrative debt score light up
3. Click on a flagged cell to show its specific issue
4. Demonstrate how a clean notebook scores low
5. Highlight one "gotcha" moment (e.g. a cell that computes something important but is never referenced again)

---

## Tech Stack

- **Parser:** Python, `ast` module, `json`
- **LLM Analysis:** Claude API (Anthropic), `anthropic` SDK
- **Frontend:** Streamlit
- **Version Control:** GitHub
- **Testing:** Notebooks in `test_notebooks/`

## Setup & Installation

1. Clone the repo and activate the venv:
```bash
   git clone <repo-url>
   cd plothole
   python -m venv venv
   venv\Scripts\Activate.ps1  # Windows
   source venv/bin/activate   # Mac/Linux
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Set your Anthropic API key (for testing the LLM layer):
```bash
   $env:ANTHROPIC_API_KEY="sk-ant-..."  # Windows PowerShell
   export ANTHROPIC_API_KEY="sk-ant-..." # Mac/Linux
```

4. Run the frontend:
```bash
   streamlit run frontend/app.py
```

---

## Submission Deadline

**August 12, 2026 (11:59 PM IST)**

Submissions evaluated on a rolling basis — **submit early for earlier results.**

---

## Next Steps

1. **Person 3:** Build the Streamlit frontend (see "Next Up" section above)
2. **Person 4:** Finalize docs, prepare submission PPT with links, record demo video
3. **All:** Test end-to-end once frontend is ready, iterate on UX before final push