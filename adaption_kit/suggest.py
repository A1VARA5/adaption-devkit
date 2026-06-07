"""suggest.py - propose a column mapping for a CSV or JSONL.

Given a dataset, this heuristically detects a likely prompt or instruction
column and a likely completion or answer column, by header name and by content,
identifies plausible context columns, and recommends the anchor:

  - prompt only        (let the platform generate completions)
  - completion only     (a high quality answers corpus; prompts get synthesized)
  - both                (instruction plus answer pairs; the common case)

It prints a ready to paste mapping JSON and a short note on which recipes and
brand controls to consider. When it cannot tell, it says so plainly and points
the user to guides/column-mapping.md.

Pure standard library. Reuses the preflight loader so CSV and JSONL are read
BOM safe with utf-8-sig, and reuses lint_dataset to sanity check the pick.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .preflight import _cell_text, _load_rows, lint_dataset

# Header tokens that hint at each role. Matched case insensitively as substrings.
_PROMPT_TOKENS = (
    "prompt",
    "instruction",
    "question",
    "query",
    "input",
    "request",
    "ask",
    "task",
    "user",
)
_COMPLETION_TOKENS = (
    "completion",
    "answer",
    "response",
    "output",
    "target",
    "label",
    "gold",
    "reply",
    "assistant",
    "summary",
)
_CONTEXT_TOKENS = (
    "context",
    "passage",
    "document",
    "source",
    "reference",
    "citation",
    "evidence",
    "snippet",
    "grounding",
    "background",
    "notes",
)
_CHAT_TOKENS = ("messages", "conversation", "dialogue", "turns", "chat")

# A header containing any of these is unlikely to be an anchor or context.
_IGNORE_TOKENS = ("id", "index", "uuid", "timestamp", "date", "split", "url", "lang")


@dataclass
class SuggestResult:
    """Outcome of :func:`suggest_mapping`."""

    path: str
    fmt: str = ""
    columns: List[str] = field(default_factory=list)
    row_count: int = 0
    prompt_col: Optional[str] = None
    completion_col: Optional[str] = None
    context_cols: List[str] = field(default_factory=list)
    chat_col: Optional[str] = None
    anchor: str = ""  # "prompt", "completion", "both", "chat", or "" (unsure)
    confident: bool = False
    notes: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def mapping(self) -> Dict[str, Any]:
        """The ready to paste column_mapping dict (empty if unsure)."""
        if self.chat_col:
            return {"chat": self.chat_col}
        m: Dict[str, Any] = {}
        if self.prompt_col:
            m["prompt"] = self.prompt_col
        if self.context_cols:
            m["context"] = list(self.context_cols)
        if self.completion_col:
            m["completion"] = self.completion_col
        return m

    def summary(self) -> str:
        lines: List[str] = []
        lines.append("adaption-kit mapping suggestion")
        lines.append("=" * 60)
        lines.append("file        : " + self.path)
        lines.append("format      : " + (self.fmt or "unknown"))
        lines.append("rows        : " + str(self.row_count))
        lines.append(
            "columns     : "
            + (", ".join(self.columns) if self.columns else "(none)")
        )
        lines.append("")

        if self.error:
            lines.append("[WARN] " + self.error)
            lines.append("")
            lines.append(
                "Could not suggest a mapping. See guides/column-mapping.md and "
                "map it by hand."
            )
            return "\n".join(lines)

        if not self.confident or not self.mapping():
            lines.append(
                "Could not confidently tell which columns are the anchor."
            )
            for note in self.notes:
                lines.append("  - " + note)
            lines.append("")
            lines.append(
                "Open guides/column-mapping.md for the decision tree and pick "
                "the columns by hand, then run 'adaption-kit lint' again to check "
                "anchor uniqueness."
            )
            return "\n".join(lines)

        label = {
            "both": "prompt + completion (instruction plus answer pairs)",
            "prompt": "prompt only (platform generates completions)",
            "completion": "completion only (high quality answers corpus; "
            "platform synthesizes prompts)",
            "chat": "chat (multi turn conversations)",
        }.get(self.anchor, self.anchor)
        lines.append("recommended anchor: " + label)
        lines.append("")
        lines.append("ready to paste column_mapping:")
        lines.append("")
        lines.append(json.dumps(self.mapping(), indent=2, ensure_ascii=False))
        lines.append("")
        if self.notes:
            lines.append("notes:")
            for note in self.notes:
                lines.append("  - " + note)
            lines.append("")
        lines.append(
            "Next: run 'adaption-kit lint " + self.path + "' with these "
            "columns to confirm the anchor is unique before you spend credits."
        )
        return "\n".join(lines)


def _header_score(name: str, tokens: Sequence[str]) -> int:
    """Score a header against a token list. Exact match beats substring."""
    low = name.strip().lower()
    if not low:
        return 0
    if low in tokens:
        return 3
    for tok in tokens:
        if tok == low:
            return 3
    for tok in tokens:
        if tok in low:
            return 2
    return 0


def _is_ignorable(name: str) -> bool:
    low = name.strip().lower()
    for tok in _IGNORE_TOKENS:
        # Match a whole word boundary so "valid" does not match "id".
        if low == tok or low.endswith("_" + tok) or low.startswith(tok + "_"):
            return True
    return False


def _avg_len(rows: Sequence[Dict[str, Any]], col: str) -> float:
    """Average character length of non empty cells in a column."""
    total = 0
    count = 0
    for r in rows:
        text = _cell_text(r.get(col))
        if text:
            total += len(text)
            count += 1
    if count == 0:
        return 0.0
    return total / count


def _looks_like_chat(rows: Sequence[Dict[str, Any]], col: str) -> bool:
    """A column whose cells parse as a list of role/content turn dicts."""
    checked = 0
    for r in rows:
        raw = r.get(col)
        value: Any = raw
        if isinstance(raw, str):
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                value = json.loads(stripped)
            except (ValueError, TypeError):
                return False
        if not isinstance(value, list) or not value:
            return False
        first = value[0]
        if not isinstance(first, dict) or "role" not in first or "content" not in first:
            return False
        checked += 1
        if checked >= 5:
            break
    return checked > 0


def suggest_mapping(path: "str | Path") -> SuggestResult:
    """Suggest a column_mapping for a CSV or JSONL (or JSON) dataset.

    Returns a :class:`SuggestResult`. Reads with utf-8-sig via the preflight
    loader. Never makes a network call.
    """
    p = Path(path)
    result = SuggestResult(path=str(p))

    if not p.exists():
        result.error = "file does not exist"
        return result

    try:
        fmt, rows, columns = _load_rows(p)
    except ValueError as exc:
        result.error = str(exc)
        return result
    except Exception as exc:  # parse errors from csv/json
        result.error = "could not parse file: " + str(exc)
        return result

    result.fmt = fmt
    result.columns = columns
    result.row_count = len(rows)

    if result.row_count == 0:
        result.error = "no rows found"
        return result
    if not columns:
        result.error = "no columns found"
        return result

    # --- chat short circuit ------------------------------------------------
    for col in columns:
        if _header_score(col, _CHAT_TOKENS) >= 2 and _looks_like_chat(rows, col):
            result.chat_col = col
            result.anchor = "chat"
            result.confident = True
            result.notes.append(
                "'" + col + "' parses as a list of role/content turns, so map "
                "it as chat. Do not also map prompt, completion, or context."
            )
            result.notes.append(
                "Recipes to consider: deduplication on. Brand controls: a "
                "blueprint for voice if the assistant turns need a consistent "
                "persona."
            )
            return result

    # --- score every column for each role ----------------------------------
    candidates = [c for c in columns if not _is_ignorable(c)]
    if not candidates:
        candidates = list(columns)

    prompt_scores: List[Tuple[int, float, str]] = []
    completion_scores: List[Tuple[int, float, str]] = []
    for col in candidates:
        avg = _avg_len(rows, col)
        ps = _header_score(col, _PROMPT_TOKENS)
        cs = _header_score(col, _COMPLETION_TOKENS)
        if ps:
            prompt_scores.append((ps, avg, col))
        if cs:
            completion_scores.append((cs, avg, col))

    # Best header matches first, then by length as a tiebreaker.
    prompt_scores.sort(key=lambda t: (t[0], -t[1]), reverse=True)
    completion_scores.sort(key=lambda t: (t[0], t[1]), reverse=True)

    prompt_col = prompt_scores[0][2] if prompt_scores else None
    completion_col = completion_scores[0][2] if completion_scores else None

    # If both resolved to the same column, keep the stronger role and drop it
    # from the other.
    if prompt_col and prompt_col == completion_col:
        ps = prompt_scores[0][0]
        cs = completion_scores[0][0]
        if ps >= cs:
            completion_col = (
                completion_scores[1][2] if len(completion_scores) > 1 else None
            )
        else:
            prompt_col = prompt_scores[1][2] if len(prompt_scores) > 1 else None

    # --- content fallback when headers are unhelpful -----------------------
    header_found = bool(prompt_col or completion_col)
    if not header_found and len(candidates) >= 1:
        # Use text length: shorter free text column is the prompt, longer is the
        # completion. Only attempt when there are usable text columns.
        text_cols = [
            (c, _avg_len(rows, c)) for c in candidates if _avg_len(rows, c) >= 8
        ]
        text_cols.sort(key=lambda t: t[1])
        if len(text_cols) >= 2:
            prompt_col = text_cols[0][0]
            completion_col = text_cols[-1][0]
            result.notes.append(
                "No header named like a prompt or completion was found; guessed "
                "by text length ('" + str(prompt_col) + "' is shorter, '"
                + str(completion_col) + "' is longer). Verify this is right."
            )
        elif len(text_cols) == 1:
            completion_col = text_cols[0][0]
            result.notes.append(
                "Only one free text column ('" + str(text_cols[0][0]) + "') was "
                "found and no question column; treating it as a high quality "
                "answers corpus (completion only)."
            )

    # --- context columns ---------------------------------------------------
    chosen = {prompt_col, completion_col}
    context_cols: List[str] = []
    for col in candidates:
        if col in chosen:
            continue
        if _header_score(col, _CONTEXT_TOKENS) >= 2:
            context_cols.append(col)
    result.context_cols = context_cols

    result.prompt_col = prompt_col
    result.completion_col = completion_col

    # --- decide the anchor -------------------------------------------------
    if prompt_col and completion_col:
        result.anchor = "both"
        result.confident = True
    elif completion_col and not prompt_col:
        result.anchor = "completion"
        result.confident = True
    elif prompt_col and not completion_col:
        result.anchor = "prompt"
        result.confident = True
    else:
        result.anchor = ""
        result.confident = False
        result.notes.append(
            "Could not identify a prompt or a completion column from headers or "
            "content."
        )
        return result

    # --- sanity check the anchor uniqueness via preflight ------------------
    try:
        report = lint_dataset(
            p,
            prompt=prompt_col,
            completion=completion_col,
            context=context_cols or None,
        )
        if report.anchor:
            rate = report.unique_anchor_rate
            if rate < 0.5 and report.anchor == "prompt":
                result.notes.append(
                    "Heads up: only "
                    + str(round(rate * 100, 1))
                    + "% of the prompt anchor values are unique, so "
                    "deduplication (always on, keyed on the prompt) would "
                    "collapse many rows. If the prompts are templated, consider "
                    "completion only instead."
                )
            elif rate >= 0.95 and report.anchor in ("prompt", "completion"):
                result.notes.append(
                    str(round(rate * 100, 1))
                    + "% of the anchor values are unique; dedup impact is "
                    "minimal."
                )
    except Exception:
        # Linting is advisory here; never let it break the suggestion.
        pass

    # --- recipe and brand control hints ------------------------------------
    _add_recipe_notes(result)
    return result


def _add_recipe_notes(result: SuggestResult) -> None:
    """Append a short, domain neutral note on recipes and brand controls."""
    if result.context_cols:
        result.notes.append(
            "Found likely context column(s): "
            + ", ".join(result.context_cols)
            + ". Mapped as a context list for grounding. For fact sensitive "
            "data also consider the hallucination_mitigation brand control."
        )

    if result.anchor == "completion":
        result.notes.append(
            "Completion only means the platform synthesizes a prompt per "
            "answer, which is the escape hatch when prompts would be templated."
        )

    result.notes.append(
        "Recipes to consider: deduplication on almost always; prompt_rephrase "
        "for more prompt variety (skip it if prompts are gold and must stay "
        "verbatim); reasoning_traces for math, code, science, legal, or finance."
    )
    result.notes.append(
        "Brand controls to consider: length to match the eval's expected "
        "answer depth; blueprint for a consistent voice (good for marketing or "
        "language); hallucination_mitigation for fact sensitive domains."
    )
    result.notes.append(
        "See guides/column-mapping.md for the full decision tree and worked "
        "examples."
    )
