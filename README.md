# PlotHole 🕳️ — Notebook Narrative Debt Detector

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Deployed-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Groq API](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=for-the-badge&logo=groq&logoColor=white)
![Status](https://img.shields.io/badge/Status-Hackathon%20Build-22C55E?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

<br/>

**A tool that flags where a data science notebook's analytical story breaks down —**
**even when every cell runs perfectly.**

*Built for BRAINWAVE 2026 · Problem Statement 3 — Open Innovation*

</div>

---

## 📌 Project Overview

A Jupyter notebook can execute top to bottom without a single error and still tell a broken story. Three hypotheses get explored and two are abandoned without explanation. A cell computes something important, and it's never mentioned again. A conclusion claims a result that the actual outputs don't support.

Code linters check syntax. Tools like `nbval` and `papermill` check that cells run. **Nothing checks whether the reasoning holds together.**

PlotHole answers the question:

> **"Does this notebook's analysis actually add up — or does it just run?"**

It parses any `.ipynb` file, reconstructs the notebook's variable flow using Python's `ast` module, and uses an LLM (via the Groq API) to review the narrative the way a skeptical reviewer would — surfacing a **Narrative Debt Score** and cell-by-cell flags for exactly where the story breaks down.

---

## 📚 Table of Contents

<ul>
  <li><a href="#-project-overview">📌 Project Overview</a></li>
  <li><a href="#-live-demo">🚀 Live Demo</a></li>
  <li><a href="#-the-four-narrative-checks">🔍 The Four Narrative Checks</a></li>
  <li><a href="#️-architecture--pipeline">🏗️ Architecture & Pipeline</a></li>
  <li><a href="#-project-structure">📂 Project Structure</a></li>
  <li><a href="#️-tech-stack">🛠️ Tech Stack</a></li>
  <li><a href="#-how-it-works">⚙️ How It Works</a></li>
  <li><a href="#-application-features">🚀 Application Features</a></li>
  <li><a href="#️-run-locally">▶️ Run Locally</a></li>
  <li><a href="#-testing--sample-notebooks">🧪 Testing & Sample Notebooks</a></li>
  <li><a href="#-known-limitations">⚠️ Known Limitations</a></li>
  <li><a href="#-future-scope">🔭 Future Scope</a></li>
  <li><a href="#-team">👥 Team</a></li>
</ul>

---

## 🚀 Live Demo

<div align="center">

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](#-live-demo-link-placeholder)
[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](#-youtube-link-placeholder)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mysticalayushi/plothole)

> 🚧 **Live demo & video links coming soon** — placeholders above will be updated once the walkthrough is recorded and the app is deployed.

</div>

---

## 🔍 The Four Narrative Checks

<div align="center">

| Check | What it catches |
|---|---|
| 🔍 **Orphaned Exploration** | A cell does meaningful analysis, but the result is never referenced again — no later cell or conclusion builds on it |
| 📝 **Markdown/Code Gap** | Markdown that describes *what* the code does ("Here we clean the data") instead of *why* it matters or what was learned |
| ⚖️ **Conclusion/Evidence Mismatch** | A closing claim ("Model X performs best") that isn't actually backed up by the outputs shown earlier in the notebook |
| 🧵 **Dead-End Variable** | A variable, dataframe, or model that's created and then never meaningfully used again — filtered by the LLM to exclude harmless loop counters and one-off prints |

</div>

---

## 🏗️ Architecture & Pipeline

```
 Upload         Parse          AST            Graph           LLM          Score        UI
 .ipynb    →    cells    →   variables   →    links     →    issues    →   0–100   →   Streamlit
```

1. **Upload** — a `.ipynb` file is uploaded through the Streamlit interface
2. **Parse** — every cell (code + markdown) is extracted with its type, source, and outputs
3. **AST** — Python's `ast` module identifies which variables each code cell creates and uses
4. **Graph** — a narrative graph cross-references the whole notebook to detect dead-end variables
5. **LLM** — the parsed structure is sent to an LLM (Llama 3.3 70B via Groq), which applies judgment across all four checks
6. **Score** — flags are converted into a single Narrative Debt Score (0–100, scaled to code cell count)
7. **UI** — results render as a color-coded, cell-by-cell view plus a grouped flag summary

---

## 📂 Project Structure

```
plothole/
│
├── parser/
│   └── parse_notebook.py         # Notebook parsing + AST variable tracking + narrative graph
│
├── llm_analysis/
│   ├── __init__.py
│   └── analyze.py                # Claude-powered narrative debt detection + scoring
│
├── frontend/
│   └── app.py                    # Streamlit web application
│
├── test_notebooks/
│   ├── customer-churn.ipynb
│   ├── heart-disease.ipynb
│   ├── house-prices-eda.ipynb
│   └── prediction-with-3-models.ipynb
│
├── test_llm_analysis.py          # CLI harness for iterating on the narrative-debt prompt
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## 🛠️ Tech Stack

<div align="center">

| 🏷️ Category | 🔧 Tools |
|---|---|
| 🐍 **Language** | Python 3.11 |
| 🧩 **Notebook Parsing** | `json`, `ast` (standard library) |
| 🤖 **LLM Analysis** | Llama 3.3 70B via Groq API, `openai`-compatible SDK |
| 🚀 **Frontend** | Streamlit |
| 💾 **Version Control** | GitHub (branch-per-feature, merged via Pull Requests) |
| 🧪 **Testing** | Real-world Kaggle notebooks |

</div>

---

## ⚙️ How It Works

### 1. Parsing & the Narrative Graph

`get_notebook_analysis()` reads the raw `.ipynb` JSON and returns every cell's type, source, and outputs. For code cells, `ast.walk()` identifies which variable names are **assigned** (created) and which are **used** (referenced). Cross-referencing this across the whole notebook builds a **narrative graph** — flagging variables that are created but never referenced again in any later cell.

```python
from parser.parse_notebook import get_notebook_analysis

result = get_notebook_analysis('path/to/notebook.ipynb')
# {
#   'cells': [...],
#   'narrative_graph': {
#       'variable_history': {...},
#       'dead_end_variables': [{'variable': 'X', 'created_at': 5}, ...]
#   }
# }
```

### 2. LLM Narrative Review

`analyze_notebook()` sends the parsed structure — including the mechanically-detected dead-end variables — to an LLM (Llama 3.3 70B via the Groq API) with a structured system prompt. The model applies judgment the mechanical parser can't: distinguishing a genuinely abandoned analysis thread from a harmless one-off print, and checking whether a conclusion's claims are actually backed by prior cell outputs.

```python
from llm_analysis.analyze import analyze_notebook, compute_narrative_debt_score

flags = analyze_notebook(result)
score = compute_narrative_debt_score(flags, result)
# flags: [{"cell_index": 14, "issue_type": "orphaned_exploration", "explanation": "..."}, ...]
# score: 0–100
```

Output is always returned as **strict, validated JSON** — malformed model output is filtered out before it ever reaches the frontend, so a bad response can't crash the UI.

### 3. Streamlit Interface

`frontend/app.py` ties the pipeline together: upload → parse → analyze → score, then renders results as a color-coded cell-by-cell view (green / yellow / red by flag severity) alongside a grouped flag summary.

---

## 🚀 Application Features

- 📤 **Simple file upload** — drop in any `.ipynb` file, no setup required on the user's end
- 🎯 **Narrative Debt Score** — a single 0–100 score, front and center, color-coded by severity
- 📓 **Cell-by-cell view** — every cell shown in order, color-coded by how many issues it triggered
- 🚩 **Flag summary view** — all flags grouped by issue type for quick scanning
- 💬 **Concrete explanations** — every flag references specifics from the actual cell, not a generic template
- 🛡️ **Graceful error handling** — missing API keys or pipeline import issues are surfaced clearly instead of crashing

---

## ▶️ Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/mysticalayushi/plothole.git
cd plothole

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
source venv/bin/activate       # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Groq API key
$env:GROQ_API_KEY="gsk_..."     # Windows PowerShell
export GROQ_API_KEY="gsk_..."   # Mac/Linux

# 5. Launch the app
streamlit run frontend/app.py
```

Or run the CLI test harness directly against any notebook:
```bash
python test_llm_analysis.py test_notebooks/prediction-with-3-models.ipynb
```

---

## 🧪 Testing & Sample Notebooks

PlotHole has been validated against real, unmodified Kaggle notebooks spanning a range of narrative quality:

<div align="center">

| Notebook | Typical Result | Notes |
|---|---|---|
| `prediction-with-3-models.ipynb` | 🔴 Flagged | Dead-end variables and a conclusion citing an accuracy figure that doesn't match the actual model output |
| `house-prices-eda.ipynb` | 🟡 Flagged | Several orphaned exploratory analyses whose results are never revisited |
| `customer-churn.ipynb` | 🟢 Clean | Code-only exploratory Q&A style, no unsupported claims |
| `heart-disease.ipynb` | 🟢 Clean | Markdown present but doesn't restate code, no evidence mismatches |

</div>

> ℹ️ **Note on scores:** the exact Narrative Debt Score can vary slightly between runs on the same notebook, since it depends on the LLM's judgment rather than a fixed rule set. The table above reflects the *typical* outcome and relative severity for each notebook, not a fixed number — the pattern (which notebooks get flagged, and roughly how much) has stayed consistent across repeated runs.

This spread is intentional: PlotHole is calibrated to avoid false positives. A notebook with generic tutorial-style commentary or straightforward exploratory prints isn't automatically flagged — only genuine narrative breakdowns are.

---

## ⚠️ Known Limitations

- **LLM judgment isn't ground truth.** Flags are best treated as suggestions for human review, not a definitive verdict — the model can occasionally be too strict or too lenient.
- **Notebook-only scope.** The current detection pipeline is built specifically around `.ipynb` structure and doesn't generalize to other artifact types out of the box (see Future Scope below).
- **"Print-and-discard" variables aren't always mechanically caught.** A variable referenced exactly once (e.g. just to display it) technically has a "use," even if that use is just a throwaway print — this is a known gap in the current dead-end detector.
- **Requires an Anthropic API key** with available credits to run the real LLM analysis layer.

---

## 🔭 Future Scope

- [ ] 🔀 **Unjustified pivot detection** — flag when a notebook silently switches analytical approach without explanation
- [ ] 🧵 **Smarter dead-end detection** — catch "created → printed once → abandoned" patterns, not just zero-use variables
- [ ] 📄 **Extend beyond notebooks** — the same "does the evidence support the conclusion" technique applies to pentest reports (unjustified severity ratings) and incident postmortems (root causes not backed by the timeline)
- [ ] 📊 **Historical scoring** — track a notebook's narrative debt score across multiple revisions
- [ ] 🌐 **Batch analysis** — score an entire repository of notebooks at once, not just one at a time
- [ ] 🔌 **CI/CD integration** — run PlotHole as a pre-commit or PR check for data science teams

---

## 👥 Team — DataForge

<div align="center">

| Name | Role | Focus | GitHub |
|---|---|---|---|
| Ayushi Rai | 🧩 Notebook Parser, Data Extraction and demo video | `.ipynb` parsing, AST-based variable tracking, narrative graph | [@mysticalayushi](https://github.com/mysticalayushi) |
| Harshit Mishra | 🤖 LLM Analysis Layer and documentation | Prompt design, Groq/Llama integration, flag validation & scoring | [@harshitmishra-dev](https://github.com/harshitmishra-dev) |
| Kalash Sharma | 🎨 Frontend / Demo Interface | Streamlit application, UI/UX, visual design | [@Kalash-here](https://github.com/Kalash-here) |
| Gunjan Sharma | 📄 Testing & Submission | Test notebooks and PPT | [@gunzzzz04](https://github.com/gunzzzz04) |

</div>

---

## 📋 Project Information

<div align="center">

| 📌 Field | 📝 Detail |
|---|---|
| 🏆 **Hackathon** | ACTS EDC BRAINWAVE 2026 |
| 👥 **Team** | DataForge |
| 🎯 **Problem Statement** | Open Innovation (P.S. 3) |
| 🧠 **LLM Used** | Llama 3.3 70B via Groq API |
| 📅 **Submission Deadline** | 12th August 2026, 11:59 PM IST |

</div>

---

<div align="center">
<sub>Built for BRAINWAVE 2026 by Team DataForge</sub>
</div>

---

<div align="center">
  <a href="#-table-of-contents">⬆️ Back to Top</a>
</div>