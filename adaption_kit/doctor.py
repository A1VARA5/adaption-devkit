"""doctor.py - a friendly, offline environment healthcheck.

For a beginner who just cloned this and wants to know "am I ready to run?".
It checks the Python version, whether the optional ``adaption`` SDK and the
optional publishing extras are importable, and whether the two environment
variables are set. It NEVER prints a key value and NEVER makes a network call.

Pure standard library. Returns a structured :class:`DoctorReport` plus a
printable summary, in the same spirit as the preflight report.

Configuration is env based only. Nothing here hardcodes a host or a key.
    ADAPTION_API_KEY   - bearer key (we report set or not set, never the value)
    ADAPTION_BASE_URL  - REST base (optional; SDK default used if unset)
"""

from __future__ import annotations

import importlib.util
import os
import sys
from dataclasses import dataclass, field
from typing import List, Tuple

# Severity levels shared with the preflight report vocabulary.
PASS = "PASS"
WARN = "WARN"
_RANK = {PASS: 0, WARN: 1}

# Minimum supported Python.
MIN_PY = (3, 10)

# Host that has been answering for participants. We only ever SHOW this as a
# hint when ADAPTION_BASE_URL is unset; we never set it for the user and the SDK
# never sees it from here.
PARTICIPANT_HOST = "https://api.prod.adaptionlabs.ai"

# Optional extras: (import name, friendly label, pip extra hint).
_EXTRAS: List[Tuple[str, str, str]] = [
    ("huggingface_hub", "Hugging Face publishing", "pip install adaption-kit[hf]"),
    ("kaggle", "Kaggle publishing", "pip install adaption-kit[kaggle]"),
    ("playwright", "cover image rendering", "pip install adaption-kit[cover]"),
]


@dataclass
class DoctorReport:
    """Result of :func:`doctor`.

    ``status`` is the worst of all checks (PASS or WARN; doctor never FAILs, it
    only advises). ``checks`` is a list of ``(level, message)`` tuples in order.
    """

    status: str = PASS
    checks: List[Tuple[str, str]] = field(default_factory=list)

    def add(self, level: str, message: str) -> None:
        self.checks.append((level, message))
        if _RANK[level] > _RANK[self.status]:
            self.status = level

    def summary(self) -> str:
        """Human readable, printable multi line summary."""
        lines: List[str] = []
        lines.append("adaption-kit doctor report")
        lines.append("=" * 60)
        for level, msg in self.checks:
            lines.append("  [" + level + "] " + msg)
        lines.append("")
        if self.status == PASS:
            lines.append("RESULT: PASS - your environment looks ready.")
        else:
            lines.append(
                "RESULT: WARN - you can still use the core commands; see the "
                "hints above to unlock the rest."
            )
        return "\n".join(lines)


def _module_available(name: str) -> bool:
    """Return True if a module can be imported, without importing it.

    Uses ``find_spec`` so we never execute optional dependency code and never
    trigger any network behaviour they might have on import.
    """
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


def doctor() -> DoctorReport:
    """Run the offline environment healthcheck. No network, no required deps."""
    report = DoctorReport()

    # --- Python version ----------------------------------------------------
    py = sys.version_info
    py_str = str(py.major) + "." + str(py.minor) + "." + str(py.micro)
    if (py.major, py.minor) >= MIN_PY:
        report.add(PASS, "Python " + py_str + " (3.10 or newer)")
    else:
        report.add(
            WARN,
            "Python "
            + py_str
            + " is older than 3.10. adaption-kit targets Python 3.10 or newer; "
            "please upgrade your interpreter.",
        )

    # --- adaption SDK ------------------------------------------------------
    if _module_available("adaption"):
        report.add(PASS, "adaption SDK is importable")
    else:
        report.add(
            WARN,
            "adaption SDK is not installed. Install it with "
            "'pip install adaption-kit[sdk]' (or 'pip install adaption'). "
            "The lint, doctor, suggest, card, and cover commands work without it.",
        )

    # --- ADAPTION_API_KEY (set or not set, never the value) ----------------
    if os.environ.get("ADAPTION_API_KEY"):
        report.add(PASS, "ADAPTION_API_KEY is set")
    else:
        report.add(
            WARN,
            "ADAPTION_API_KEY is not set. estimate, run, and download need it. "
            "Set it in your environment (never commit it).",
        )

    # --- ADAPTION_BASE_URL -------------------------------------------------
    if os.environ.get("ADAPTION_BASE_URL"):
        report.add(PASS, "ADAPTION_BASE_URL is set")
    else:
        report.add(
            WARN,
            "ADAPTION_BASE_URL is not set, so the SDK uses its documented "
            "default. That default has been seen to return 503; the host which "
            "has been answering for participants is "
            + PARTICIPANT_HOST
            + " . If you hit 503, set ADAPTION_BASE_URL to that host.",
        )

    # --- optional extras ---------------------------------------------------
    for mod, label, hint in _EXTRAS:
        if _module_available(mod):
            report.add(PASS, mod + " is installed (" + label + ")")
        else:
            report.add(
                WARN,
                mod
                + " is not installed ("
                + label
                + "). Install with '"
                + hint
                + "' if you need it.",
            )

    return report
