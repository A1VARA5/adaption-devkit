"""publish.py - the 501 workaround.

Adaption's REST publish endpoint currently returns 501, so the hackathon's
required Hugging Face and Kaggle releases are done manually. This module pushes a
local folder to either or both, using lazy optional imports and env credentials.

Hugging Face:
    HF_TOKEN (or HUGGINGFACE_TOKEN)   - write token
    pip install adaption-kit[hf]

Kaggle:
    KAGGLE_USERNAME / KAGGLE_KEY (or ~/.kaggle/kaggle.json)
    pip install adaption-kit[kaggle]
    Kaggle datasets are PRIVATE until you toggle them public in the UI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class PublishResult:
    """What was pushed and where."""

    hf_url: Optional[str] = None
    kaggle_ref: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["adaption-kit publish report", "=" * 60]
        if self.hf_url:
            lines.append("Hugging Face : " + self.hf_url)
        if self.kaggle_ref:
            lines.append("Kaggle       : " + self.kaggle_ref)
        if not self.hf_url and not self.kaggle_ref:
            lines.append("nothing published (no target specified)")
        for n in self.notes:
            lines.append("note: " + n)
        return "\n".join(lines)


def _hf_token() -> Optional[str]:
    return os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")


def publish_to_hf(
    folder: "str | Path",
    hf_repo: str,
    repo_type: str = "dataset",
    private: bool = True,
    commit_message: str = "Upload via adaption-kit",
) -> str:
    """Upload a folder to a Hugging Face repo. Returns the repo URL.

    Lazy-imports ``huggingface_hub`` so the dependency stays optional.
    """
    try:
        from huggingface_hub import HfApi  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is not installed. Install with "
            "'pip install adaption-kit[hf]'."
        ) from exc

    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError("folder '" + str(folder_path) + "' is not a directory")

    token = _hf_token()
    if not token:
        raise RuntimeError(
            "no Hugging Face token found. Set HF_TOKEN (or HUGGINGFACE_TOKEN)."
        )

    api = HfApi(token=token)
    api.create_repo(
        repo_id=hf_repo,
        repo_type=repo_type,
        private=private,
        exist_ok=True,
    )
    api.upload_folder(
        repo_id=hf_repo,
        repo_type=repo_type,
        folder_path=str(folder_path),
        commit_message=commit_message,
    )
    kind = "datasets/" if repo_type == "dataset" else ""
    return "https://huggingface.co/" + kind + hf_repo


def publish_to_kaggle(
    folder: "str | Path",
    kaggle_slug: str,
    public: bool = False,
) -> str:
    """Create or version a Kaggle dataset from a folder. Returns the dataset ref.

    ``kaggle_slug`` is ``owner/dataset-name``. The folder must contain a
    ``dataset-metadata.json`` (use cards.generate_kaggle_metadata) or this writes
    a minimal one. Datasets are created PRIVATE; toggle public in the UI or pass
    public=True (still subject to Kaggle review).
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "kaggle is not installed. Install with "
            "'pip install adaption-kit[kaggle]'."
        ) from exc

    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError("folder '" + str(folder_path) + "' is not a directory")

    meta = folder_path / "dataset-metadata.json"
    if not meta.exists():
        raise RuntimeError(
            "no dataset-metadata.json in '"
            + str(folder_path)
            + "'. Generate one with cards.generate_kaggle_metadata first."
        )

    api = KaggleApi()
    api.authenticate()  # reads KAGGLE_USERNAME/KAGGLE_KEY or ~/.kaggle/kaggle.json

    existing = _kaggle_dataset_exists(api, kaggle_slug)
    if existing:
        api.dataset_create_version(
            folder=str(folder_path),
            version_notes="Updated via adaption-kit",
            dir_mode="zip",
        )
    else:
        api.dataset_create_new(
            folder=str(folder_path),
            public=public,
            dir_mode="zip",
        )
    return kaggle_slug


def _kaggle_dataset_exists(api: Any, slug: str) -> bool:
    try:
        owner, name = slug.split("/", 1)
    except ValueError:
        return False
    try:
        results = api.dataset_list(user=owner, search=name)
    except Exception:  # noqa: BLE001 - network/auth; treat as "create new"
        return False
    for ds in results or []:
        if str(getattr(ds, "ref", "")).lower() == slug.lower():
            return True
    return False


def publish(
    folder: "str | Path",
    hf_repo: Optional[str] = None,
    kaggle_slug: Optional[str] = None,
    private: bool = True,
) -> PublishResult:
    """Push a folder to Hugging Face and/or Kaggle (manual 501 workaround).

    At least one of hf_repo or kaggle_slug must be provided.
    """
    if not hf_repo and not kaggle_slug:
        raise ValueError("provide hf_repo and/or kaggle_slug")

    result = PublishResult()
    result.notes.append(
        "Adaption publish endpoint returns 501; releasing manually."
    )

    if hf_repo:
        result.hf_url = publish_to_hf(folder, hf_repo, private=private)

    if kaggle_slug:
        result.kaggle_ref = publish_to_kaggle(
            folder, kaggle_slug, public=not private
        )
        result.notes.append(
            "Kaggle datasets stay private until toggled public in the UI."
        )

    return result
