"""
Quick harness for iterating on the narrative-debt prompt.

Drop this file in the repo root (next to parser/ and test_notebooks/) and run:

    export ANTHROPIC_API_KEY=sk-ant-...
    python test_llm_analysis.py test_notebooks/some_notebook.ipynb

Or with no args, it'll run against every .ipynb in test_notebooks/.
"""

import sys
import glob
import json

from parser.parse_notebook import get_notebook_analysis
from llm_analysis.analyze import analyze_notebook, compute_narrative_debt_score


def run_one(path):
    print(f"\n{'=' * 70}\n{path}\n{'=' * 70}")
    notebook_data = get_notebook_analysis(path)
    flags = analyze_notebook(notebook_data)
    score = compute_narrative_debt_score(flags, notebook_data)

    print(f"narrative_debt_score: {score}")
    print(f"flags: {len(flags)}")
    for f in flags:
        print(f"  [cell {f['cell_index']}] {f['issue_type']}: {f['explanation']}")

    return {"path": path, "score": score, "flags": flags}


def main():
    if len(sys.argv) > 1:
        paths = sys.argv[1:]
    else:
        paths = sorted(glob.glob("test_notebooks/*.ipynb"))

    if not paths:
        print("No notebooks found. Pass a path or add .ipynb files to test_notebooks/.")
        return

    results = [run_one(p) for p in paths]

    with open("llm_analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved full results to llm_analysis_results.json")


if __name__ == "__main__":
    main()
