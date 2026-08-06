"""
llm_analysis/analyze.py

PlotHole — Person 2: LLM Analysis Layer.

Usage:
    from parser.parse_notebook import get_notebook_analysis
    from llm_analysis.analyze import analyze_notebook, compute_narrative_debt_score

    notebook_data = get_notebook_analysis('path/to/notebook.ipynb')
    flags = analyze_notebook(notebook_data)
    score = compute_narrative_debt_score(flags, notebook_data)

Requires:
    pip install anthropic
    export ANTHROPIC_API_KEY=sk-ant-...
"""

import os
import json
import re
from anthropic import Anthropic

DEFAULT_MODEL = "claude-sonnet-4-5-20250929"

VALID_ISSUE_TYPES = {
    "orphaned_exploration",
    "markdown_code_gap",
    "conclusion_evidence_mismatch",
    "dead_end_variable",
}

# Keep prompts a reasonable size — long outputs (big dataframes, stack
# traces, base64 images) blow up token cost without adding signal.
MAX_SOURCE_CHARS = 1500
MAX_OUTPUT_CHARS = 500

SYSTEM_PROMPT = """You are a meticulous data science reviewer. You review Jupyter notebooks \
for "narrative debt": places where the notebook's story doesn't hold together \
even though the code may run fine.

You are given:
1. Every cell in the notebook, in order, with its type, source, output, and \
(for code cells) the variables it assigns and uses.
2. A list of "dead-end variables" — variables that were created but never \
referenced again in any later cell, detected mechanically.

Identify issues in exactly these four categories:

- "orphaned_exploration": a code cell does meaningful analysis or computation, \
but its result is never referenced again by later code or discussed in later \
markdown/conclusions.
- "markdown_code_gap": a markdown cell describes WHAT the code does (a caption \
or restatement of the code) rather than WHY it matters, what was learned, or \
what decision it informs.
- "conclusion_evidence_mismatch": a concluding/summary markdown cell makes a \
claim that isn't actually backed up by the outputs of earlier cells (e.g. \
claims a trend, number, or result that doesn't appear anywhere in the outputs).
- "dead_end_variable": from the mechanically-detected dead-end variable list, \
judge which ones are MEANINGFUL narrative debt (e.g. a computed metric, model, \
or dataframe that seems important but is dropped) versus harmless (loop \
counters, one-off print variables, throwaway temp variables). Only flag the \
meaningful ones — most loop variables and one-off prints should NOT be flagged.

Rules:
- Be a skeptical but fair reviewer. Do not flag something just because it's \
short — flag it because the narrative genuinely breaks down.
- Only flag real issues. A clean, well-explained notebook should return an \
empty list. Do not force a minimum number of flags just to have something to say.
- Each flag needs a specific, concrete explanation referencing what's actually \
in that cell — never a generic template sentence.
- Respond with ONLY a JSON array. No markdown code fences, no prose before or \
after, no explanation outside the JSON.

Each element of the array must be an object with exactly these keys:
  "cell_index": integer, the index of the cell most responsible for the issue
  "issue_type": one of "orphaned_exploration", "markdown_code_gap", "conclusion_evidence_mismatch", "dead_end_variable"
  "explanation": a specific, one-to-two sentence explanation

If there are no issues, respond with exactly: []
"""


def _truncate(text, limit):
    if text is None:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[:limit] + f"...[truncated, {len(text)} chars total]"


def _stringify_outputs(outputs):
    """Turn raw nbformat outputs into a compact text summary."""
    if not outputs:
        return ""
    parts = []
    for out in outputs:
        if not isinstance(out, dict):
            parts.append(str(out))
            continue
        if "text" in out:
            text = out["text"]
            parts.append(text if isinstance(text, str) else "".join(text))
        elif "data" in out:
            data = out["data"]
            if "text/plain" in data:
                tp = data["text/plain"]
                parts.append(tp if isinstance(tp, str) else "".join(tp))
            else:
                parts.append(f"[non-text output: {', '.join(data.keys())}]")
        elif "ename" in out:
            parts.append(f"[ERROR: {out.get('ename')}: {out.get('evalue')}]")
    return "\n".join(p for p in parts if p)


def _build_cells_block(cells):
    lines = []
    for cell in cells:
        idx = cell.get("index")
        ctype = cell.get("type")
        source = _truncate(cell.get("source", ""), MAX_SOURCE_CHARS)
        lines.append(f"--- Cell {idx} ({ctype}) ---")
        lines.append(source if source.strip() else "(empty)")
        if ctype == "code":
            out_text = _truncate(_stringify_outputs(cell.get("outputs")), MAX_OUTPUT_CHARS)
            if out_text.strip():
                lines.append(f"[output]: {out_text}")
            variables = cell.get("variables") or {}
            assigned = variables.get("assigned") or []
            used = variables.get("used") or []
            if assigned or used:
                lines.append(f"[assigns: {assigned}] [uses: {used}]")
        lines.append("")
    return "\n".join(lines)


def _build_dead_ends_block(dead_end_variables):
    if not dead_end_variables:
        return "(none detected)"
    lines = []
    for d in dead_end_variables:
        lines.append(f"- '{d.get('variable')}' created at cell {d.get('created_at')}, never used again")
    return "\n".join(lines)


def _extract_json_array(raw_text):
    """Strip code fences / stray prose and parse the first JSON array found."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not parse JSON array from model output:\n{raw_text[:500]}")


def _validate_flags(raw_flags, num_cells):
    """Drop anything malformed rather than letting a bad flag crash Person 3's UI."""
    flags = []
    for item in raw_flags:
        if not isinstance(item, dict):
            continue
        cell_index = item.get("cell_index")
        issue_type = item.get("issue_type")
        explanation = item.get("explanation")
        if not isinstance(cell_index, int):
            continue
        if issue_type not in VALID_ISSUE_TYPES:
            continue
        if not isinstance(explanation, str) or not explanation.strip():
            continue
        if not (0 <= cell_index < num_cells):
            continue
        flags.append({
            "cell_index": cell_index,
            "issue_type": issue_type,
            "explanation": explanation.strip(),
        })
    return flags


def compute_narrative_debt_score(flags, notebook_data):
    """
    Narrative debt score: flags per code cell, scaled to 0-100.
    0 = no narrative debt detected. Higher = more issues relative to notebook size.
    """
    cells = notebook_data.get("cells", [])
    num_code_cells = sum(1 for c in cells if c.get("type") == "code")
    if num_code_cells == 0:
        return 0.0
    raw_ratio = len(flags) / num_code_cells
    return min(100.0, round(raw_ratio * 100, 1))


def analyze_notebook(notebook_data, model=DEFAULT_MODEL, api_key=None, client=None, max_tokens=4000):
    """
    Take the dict returned by get_notebook_analysis() and return a list of
    narrative debt flags, e.g.:

        [
            {
                "cell_index": 14,
                "issue_type": "orphaned_exploration",
                "explanation": "..."
            },
            ...
        ]

    This is the exact shape Person 3's frontend expects. To also get the
    narrative debt score, call compute_narrative_debt_score(flags, notebook_data).
    """
    cells = notebook_data.get("cells", [])
    dead_end_variables = notebook_data.get("narrative_graph", {}).get("dead_end_variables", [])

    cells_block = _build_cells_block(cells)
    dead_ends_block = _build_dead_ends_block(dead_end_variables)

    user_prompt = f"""NOTEBOOK CELLS:

{cells_block}

MECHANICALLY-DETECTED DEAD-END VARIABLES:

{dead_ends_block}

Review this notebook and return the JSON array of narrative debt flags now."""

    if client is None:
        client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    try:
        raw_flags = _extract_json_array(raw_text)
    except ValueError as e:
        raise ValueError(f"analyze_notebook: LLM did not return valid JSON. {e}")

    return _validate_flags(raw_flags, num_cells=len(cells))
