# PlotHole

## Project Status

### ✅ Completed — Notebook Parser & Data Extraction (Person 1)

**What's done:**
- `parser/parse_notebook.py` reads any `.ipynb` file and extracts every cell (code + markdown), including cell type, source content, and outputs.
- For every code cell, extracts which variables are **created** (assigned) and which are **used** (referenced), using Python's `ast` module.
- Builds a "narrative graph" across the whole notebook — cross-references all cells to detect **dead-end variables**: variables created in one cell that are never used again in any later cell. This is a key signal for narrative debt.
- Everything is packaged into a single function for easy use:

```python
from parser.parse_notebook import get_notebook_analysis

result = get_notebook_analysis('path/to/notebook.ipynb')
```

**Output format** — `get_notebook_analysis()` returns a dictionary with two keys:

```python
{
    'cells': [
        {
            'index': 0,
            'type': 'code',  # or 'markdown'
            'source': '...',  # the actual cell content
            'outputs': [...],  # raw output data from the notebook, if any
            'variables': {
                'assigned': ['df', 'model'],
                'used': ['pd', 'df'],
                'parse_error': False
            }  # None for markdown cells
        },
        ...
    ],
    'narrative_graph': {
        'variable_history': {
            'df': {'created_at': 3, 'used_at': [5, 7, 9]},
            ...
        },
        'dead_end_variables': [
            {'variable': 'feature_importance', 'created_at': 12},
            ...
        ]
    }
}
```

Tested on real Kaggle notebooks in `test_notebooks/` — parsing and variable tracking work correctly.

---

### 🔜 Next Up — LLM Analysis Layer (Person 2)

**Goal:** Take the output of `get_notebook_analysis()` above and use an LLM (Claude/GPT) to detect narrative coherence issues, then return a structured list of flags.

**What to build:**
1. Write a function, e.g. `analyze_notebook(notebook_analysis) -> list_of_flags`, that takes the exact dictionary shown above as input.
2. Design a prompt that sends the LLM the cells (source + outputs) and the `dead_end_variables` list, and asks it to identify:
   - **Orphaned exploration** — a cell does meaningful analysis but nothing later references the result
   - **Markdown-code narrative gap** — markdown describes *what* the code does rather than *why* it matters or what was learned
   - **Conclusion-evidence mismatch** — the final markdown cell's claims aren't backed by earlier cell outputs
   - You can also directly pass along the `dead_end_variables` list from the narrative graph and ask the LLM to judge which ones are *meaningfully* dead-ends vs. harmless (e.g. loop variables, one-off prints) — don't try to filter these in code, that's a judgment call better left to the LLM.
3. **Critical:** have the LLM return its findings in strict JSON, e.g.:
```python
[
    {
        "cell_index": 14,
        "issue_type": "orphaned_exploration",
        "explanation": "This cell computes feature importances but the result is never referenced in later cells or the conclusion."
    },
    ...
]
```
This makes it easy for the frontend (Person 3) to parse and display later.
4. Compute an overall **narrative debt score** for the notebook (e.g. number of flags relative to number of code cells).
5. Test the prompt against the same notebooks in `test_notebooks/` — expect to iterate on the prompt several times before flags feel accurate (not too strict, not too lenient).

**Deliverable:** a function that can be called like this:
```python
from parser.parse_notebook import get_notebook_analysis
from llm_analysis.analyze import analyze_notebook

notebook_data = get_notebook_analysis('path/to/notebook.ipynb')
flags = analyze_notebook(notebook_data)
```

This `flags` output is what gets handed to Person 3 for the frontend display.