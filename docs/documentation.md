# PlotHole
### Catching narrative debt in Jupyter notebooks before it reaches review

---

## 1. Project Overview

**Project name:** PlotHole
**Tagline:** A narrative debt linter for Jupyter notebooks — it flags where the story stops matching the code.

**Problem statement addressed:** Open Innovation / Problem Statement 3

**The problem, in plain language:**
Jupyter notebooks are supposed to tell a story — explore data, test an idea, show evidence, reach a conclusion. In practice, that story rots fast: cells get run out of order, dead-end explorations get left in, and the final conclusion often claims things the actual cell outputs never proved. Existing linters check whether code *runs*, not whether the notebook still makes *sense*. PlotHole reads a notebook the way a skeptical reviewer would, and tells you exactly where the narrative breaks down.

---

## 2. The Problem — In Detail

**Why "narrative debt" is real and underserved**
A notebook can pass every linter, have zero syntax errors, and still be dishonest — a conclusion cell that claims "Model B performs significantly better" with no cell above it that actually compares the two models, or a feature-importance plot that's computed, admired, and then never used again. This kind of drift accumulates silently because nothing *breaks* — the notebook still executes top to bottom. It just stops being trustworthy.

**Who experiences it**
- **Data scientists**, revisiting their own notebook three weeks later and not trusting their own conclusions
- **Students**, whose graded notebooks often contain analysis that doesn't connect to their final write-up
- **Teams reviewing notebooks** in code review or before a notebook is turned into a report/paper, who currently have to read every cell manually to catch this

**Why existing tools don't solve this**
Tools like `nbQA`, `flake8`, `pylint`, or notebook-specific linters check for *style* and *correctness* — unused imports, PEP8 violations, undefined names. None of them reason about *meaning*: whether a markdown cell's claim is backed by the code below it, or whether a variable computed with real effort was ever actually used again. That's a semantic, narrative-level problem, which is exactly the kind of judgment call a general-purpose linter can't make but an LLM, given the right structure, can.

---

## 3. The Solution — What PlotHole Does

PlotHole parses a notebook, builds a map of every variable's life story across cells, and then uses an LLM to review that map for four kinds of narrative debt:

1. **Orphaned exploration** — a cell performs real analysis, but the result is never referenced again, in code or in the conclusion.
2. **Markdown-code narrative gaps** — a markdown cell describes *what* the code does (paraphrasing it) instead of *why* it matters or what was learned from it.
3. **Conclusion-evidence mismatches** — the final markdown cell makes a claim that isn't actually backed by any earlier cell's output.
4. **Dead-end variables** — variables that are created with meaningful effort and never used again anywhere in the notebook, filtered by LLM judgment so that harmless cases (loop counters, one-off `print`s) aren't flagged.

**What the output looks like**
- An overall **narrative debt score** for the notebook (flags relative to number of code cells)
- A **cell-by-cell list of flags**, each with the cell index, issue type, and a plain-language explanation of what's wrong — shown in the Streamlit frontend so a user can jump straight to the problem cell.

---

## 4. Architecture / How It Works

**Pipeline:** `Notebook (.ipynb)` → **Parser** → **LLM Analysis** → **Frontend**
.ipynb file
│
▼
┌─────────────────┐
│ Parser │ ast-based extraction of cells, variables,
│ (Person 1) │ and a cross-cell "narrative graph"
└─────────────────┘
│ structured dict (cells + narrative_graph)
▼
┌─────────────────┐
│ LLM Analysis │ Claude API reasons over cells + dead-end
│ (Person 2) │ variables, returns structured JSON flags
└─────────────────┘
│ list of flags + narrative debt score
▼
┌─────────────────┐
│ Frontend │ Streamlit app: upload a notebook, see
│ (Person 3) │ score + flagged cells
└─────────────────┘


**Component breakdown**

- **Parser (Person 1)** — `parser/parse_notebook.py`. Reads any `.ipynb` file, extracts every cell (type, source, outputs), and for each code cell uses Python's `ast` module to determine which variables are **assigned** vs **used**. It then cross-references every cell to build a **narrative graph**: a per-variable history of where it was created and every later cell where it was used — which is how dead-end variables are detected. Exposed as a single function, `get_notebook_analysis(path)`.

- **LLM Analysis (Person 2)** — `llm_analysis/analyze.py`. Takes the parser's output dict and sends the cell contents, outputs, and the `dead_end_variables` list to Claude with a structured prompt asking it to identify the four issue types above. The LLM returns strict JSON (`cell_index`, `issue_type`, `explanation` per flag), and the function also computes the overall narrative debt score. Exposed as `analyze_notebook(notebook_data)`.

- **Frontend (Person 3)** — Streamlit app that lets a user upload a `.ipynb` file, runs it through the parser and LLM analysis, and displays the narrative debt score alongside the flagged cells with their explanations.

**Tech stack:** Python, `ast` module, Claude API, Streamlit

---

## 5. Key Technical Highlights

- **AST-based narrative graph, not just linting.** Instead of just checking whether variables are defined before use (a compiler's job), the parser tracks *every* later use of *every* assigned variable across the whole notebook, producing a full `variable_history` map. Dead-end detection falls directly out of this graph — a variable with a `created_at` and an empty `used_at` list.

- **Judgment deliberately left to the LLM, not hardcoded.** Rather than writing brittle heuristics to decide which dead-end variables "matter" (e.g. excluding loop variables or one-off prints), the raw `dead_end_variables` list is handed to the LLM alongside the cell context, and the LLM makes the call — because that distinction is genuinely a judgment call, not a rule.

- **Strict JSON contract between backend and frontend.** The LLM is prompted to return only a structured JSON array (`cell_index`, `issue_type`, `explanation`), which decouples the analysis layer from the frontend completely — Person 3 never has to parse free-form LLM text, just validate and render JSON.

- **Prompt iteration against real data.** The prompt was tuned against real Kaggle notebooks in `test_notebooks/` specifically to avoid being too strict (flagging normal exploratory work) or too lenient (missing genuine gaps) — the score is meant to be a signal for human review, not an automated verdict.

---

## 6. Demo / Usage Instructions

**Setup (local):**
```bash
git clone https://github.com/mysticalayushi/PlotHole.git
cd PlotHole
pip install -r requirements.txt
# set your Claude API key as an environment variable, e.g.
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

**What to try as a judge/user:**
1. Launch the Streamlit app.
2. Upload one of the sample notebooks from `test_notebooks/` (these are real Kaggle notebooks already known to contain narrative debt).
3. Review the narrative debt score and click through the flagged cells to see the LLM's explanation for each one.
4. Try uploading a clean, well-documented notebook for comparison and see the score drop.

---

## 7. Limitations & Honest Caveats

- **LLM judgment isn't ground truth.** Every flag is a suggestion for a human reviewer, not a definitive verdict — the LLM can misjudge context, especially in domain-specific notebooks.
- **Scoped to Jupyter notebooks only.** PlotHole currently only understands `.ipynb` structure and Python code cells; it doesn't support R notebooks, plain scripts, or other formats.
- **Static analysis has real limits.** The `ast`-based variable tracker sees variable names, not runtime values — it can't detect issues that only show up dynamically (e.g., a variable reassigned inside a conditional branch that's never actually taken).
- **Prompt sensitivity.** Flag accuracy depends on prompt tuning; it was validated against the notebooks in `test_notebooks/` and may need further iteration on very different notebook styles (e.g. heavily visualization-only notebooks, or ones with minimal markdown).

---

## 8. Future Work

- **Beyond notebooks:** extend the same "narrative debt" idea to other document types where the write-up is supposed to match the underlying evidence — pentest reports, incident postmortems, and research write-ups are the same shape of problem: does the narrative match the evidence trail?
- **Additional detection types cut for time:**
  - **Unjustified pivots** — flagging when a notebook's analysis direction changes with no explanation for why.
  - **More nuanced scoring** — weighting flags by severity/type rather than a flat count, and normalizing better across notebook lengths.
- **Richer frontend:** inline diff-style highlighting of the exact code/markdown causing a flag, rather than just cell-level pointers.

---

## 9. Team

| Component | Owner |
|---|---|
| Parser & narrative graph (`parser/`) | Person 1 |
| LLM analysis & scoring (`llm_analysis/`) | Person 2 |
| Streamlit frontend | Person 3 |
| Documentation | — |

---

## 10. Links

- **GitHub repo:** https://github.com/mysticalayushi/PlotHole
- **Working demo:** _add link_
- **YouTube video:** _add link
