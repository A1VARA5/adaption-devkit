"""adaption-devkit (package ``adaption_kit``).

A community, unofficial, open source toolkit for starting fast with Adaption's
Adaptive Data and AutoScientist. Not affiliated with or endorsed by Adaption Labs.

License: Apache-2.0
Author: Aivaras Navardauskas (MANIFESTA), GitHub A1VARA5
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Aivaras Navardauskas (MANIFESTA)"
__license__ = "Apache-2.0"

BANNER = (
    "adaption-kit "
    + __version__
    + " - community, unofficial toolkit for Adaption Adaptive Data / AutoScientist. "
    "Not affiliated with Adaption Labs."
)

from .preflight import LintReport, lint_dataset  # noqa: E402
from .doctor import DoctorReport, doctor  # noqa: E402
from .suggest import SuggestResult, suggest_mapping  # noqa: E402
from .cards import (  # noqa: E402
    KAGGLE_VALID_TAGS,
    generate_dataset_card,
    generate_kaggle_metadata,
    generate_model_card,
)

__all__ = [
    "__version__",
    "__author__",
    "__license__",
    "BANNER",
    "LintReport",
    "lint_dataset",
    "DoctorReport",
    "doctor",
    "SuggestResult",
    "suggest_mapping",
    "generate_dataset_card",
    "generate_model_card",
    "generate_kaggle_metadata",
    "KAGGLE_VALID_TAGS",
    # run.py helpers are imported lazily by the CLI so the SDK stays optional.
]
