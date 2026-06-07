"""run.py - thin, friendly helpers over the ``adaption`` SDK.

Covers the adapt -> evaluate loop: estimate, pilot, run_full, and a
wait_for_result that polls BOTH the run status AND the evaluation, returning the
headline improvement_percent.

Configuration is env-based only. Nothing here hardcodes a host or a key.
    ADAPTION_API_KEY   - bearer key
    ADAPTION_BASE_URL  - REST base (optional; SDK default used if unset)

The ``adaption`` SDK is an OPTIONAL dependency. Importing this module never
imports it; each entry point imports lazily and raises a friendly error if it
is missing (install with ``pip install adaption-kit[sdk]``).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

DEFAULT_PILOT_ROWS = 200


class SdkNotInstalled(RuntimeError):
    """Raised when the optional ``adaption`` SDK is not importable."""


def _client() -> Any:
    """Build an ``Adaption`` client from environment variables.

    Raises SdkNotInstalled with install guidance if the SDK is absent.
    """
    try:
        from adaption import Adaption  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on env
        raise SdkNotInstalled(
            "The 'adaption' SDK is not installed. Install it with "
            "'pip install adaption-kit[sdk]' (or 'pip install adaption'). "
            "adaption-kit keeps the SDK optional so lint/card/cover work "
            "without it."
        ) from exc

    api_key = os.environ.get("ADAPTION_API_KEY")
    base_url = os.environ.get("ADAPTION_BASE_URL")
    kwargs: Dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    # If api_key is unset the SDK reads ADAPTION_API_KEY itself; we pass nothing
    # rather than an empty string so we never override its own lookup.
    return Adaption(**kwargs)


def _build_column_mapping(
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    context: Optional[Sequence[str]] = None,
    chat: Optional[str] = None,
) -> Dict[str, Any]:
    """Assemble a valid column_mapping. Enforces the anchor + exclusivity rules
    locally so we fail before reserving credits."""
    mapping: Dict[str, Any] = {}
    if chat:
        if prompt or completion or context:
            raise ValueError(
                "'chat' is mutually exclusive with prompt/completion/context"
            )
        mapping["chat"] = chat
        return mapping
    if not prompt and not completion:
        raise ValueError(
            "a run needs an anchor: pass prompt=... or completion=... (or chat=...)"
        )
    if prompt:
        mapping["prompt"] = prompt
    if completion:
        mapping["completion"] = completion
    if context:
        mapping["context"] = list(context)
    return mapping


def _build_recipe_spec(
    deduplication: Optional[bool] = None,
    prompt_rephrase: Optional[bool] = None,
    reasoning_traces: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    recipes: Dict[str, bool] = {}
    if deduplication is not None:
        recipes["deduplication"] = deduplication
    if prompt_rephrase is not None:
        recipes["prompt_rephrase"] = prompt_rephrase
    if reasoning_traces is not None:
        recipes["reasoning_traces"] = reasoning_traces
    if not recipes:
        return None
    return {"recipes": recipes}


@dataclass
class RunResult:
    """Outcome of a wait_for_result poll."""

    dataset_id: str
    run_id: Optional[str]
    run_status: str
    evaluation_status: str
    improvement_percent: Optional[float] = None
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def estimate(
    dataset_id: str,
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    context: Optional[Sequence[str]] = None,
    chat: Optional[str] = None,
    brand_controls: Optional[Dict[str, Any]] = None,
    deduplication: Optional[bool] = None,
    prompt_rephrase: Optional[bool] = None,
    reasoning_traces: Optional[bool] = None,
    client: Any = None,
) -> Any:
    """Validate the mapping and quote credits/time WITHOUT starting a run.

    Always call this before a real run. Returns the SDK estimate object
    (estimated_credits_consumed, estimated_minutes, ...).
    """
    cli = client or _client()
    mapping = _build_column_mapping(prompt, completion, context, chat)
    recipe_spec = _build_recipe_spec(deduplication, prompt_rephrase, reasoning_traces)
    kwargs: Dict[str, Any] = {"column_mapping": mapping, "estimate": True}
    if brand_controls:
        kwargs["brand_controls"] = brand_controls
    if recipe_spec:
        kwargs["recipe_specification"] = recipe_spec
    return cli.datasets.run(dataset_id, **kwargs)


def pilot(
    dataset_id: str,
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    context: Optional[Sequence[str]] = None,
    chat: Optional[str] = None,
    brand_controls: Optional[Dict[str, Any]] = None,
    deduplication: Optional[bool] = None,
    prompt_rephrase: Optional[bool] = None,
    reasoning_traces: Optional[bool] = None,
    max_rows: int = DEFAULT_PILOT_ROWS,
    idempotency_key: Optional[str] = None,
    client: Any = None,
) -> Any:
    """Start a capped real run for cheap iteration (default 200 rows).

    Returns the SDK run object (carries run_id). Poll with wait_for_result.
    """
    return run_full(
        dataset_id,
        prompt=prompt,
        completion=completion,
        context=context,
        chat=chat,
        brand_controls=brand_controls,
        deduplication=deduplication,
        prompt_rephrase=prompt_rephrase,
        reasoning_traces=reasoning_traces,
        max_rows=max_rows,
        idempotency_key=idempotency_key,
        client=client,
    )


def run_full(
    dataset_id: str,
    prompt: Optional[str] = None,
    completion: Optional[str] = None,
    context: Optional[Sequence[str]] = None,
    chat: Optional[str] = None,
    brand_controls: Optional[Dict[str, Any]] = None,
    deduplication: Optional[bool] = None,
    prompt_rephrase: Optional[bool] = None,
    reasoning_traces: Optional[bool] = None,
    max_rows: Optional[int] = None,
    idempotency_key: Optional[str] = None,
    client: Any = None,
) -> Any:
    """Start a real adaptation run.

    Pass max_rows to cap the run (a pilot); omit it for the full corpus.
    idempotency_key makes a retry safe (returns the original response).
    """
    cli = client or _client()
    mapping = _build_column_mapping(prompt, completion, context, chat)
    recipe_spec = _build_recipe_spec(deduplication, prompt_rephrase, reasoning_traces)
    kwargs: Dict[str, Any] = {"column_mapping": mapping, "estimate": False}
    if brand_controls:
        kwargs["brand_controls"] = brand_controls
    if recipe_spec:
        kwargs["recipe_specification"] = recipe_spec
    job_spec: Dict[str, Any] = {}
    if max_rows is not None:
        job_spec["max_rows"] = max_rows
    if idempotency_key:
        job_spec["idempotency_key"] = idempotency_key
    if job_spec:
        kwargs["job_specification"] = job_spec
    return cli.datasets.run(dataset_id, **kwargs)


def _improvement_from_eval(ev: Any) -> Dict[str, Optional[float]]:
    out: Dict[str, Optional[float]] = {
        "improvement_percent": None,
        "score_before": None,
        "score_after": None,
    }
    quality = getattr(ev, "quality", None)
    if quality is not None:
        out["improvement_percent"] = getattr(quality, "improvement_percent", None)
        out["score_before"] = getattr(quality, "score_before", None)
        out["score_after"] = getattr(quality, "score_after", None)
    return out


def wait_for_result(
    dataset_id: str,
    timeout: float = 1800.0,
    poll_interval: float = 5.0,
    client: Any = None,
) -> RunResult:
    """Poll run status AND evaluation, returning improvement_percent.

    The run can be ``succeeded`` before evaluation finishes, so evaluation is
    polled separately. Stops when both the run is terminal and the evaluation is
    terminal (or on timeout).
    """
    cli = client or _client()
    deadline = time.time() + timeout

    run_status = "unknown"
    eval_status = "unknown"
    run_error: Optional[str] = None
    run_id: Optional[str] = None

    run_terminal = {"succeeded", "failed", "ready", "cancelled", "canceled"}
    eval_terminal = {"succeeded", "failed", "skipped"}

    while True:
        status_obj = cli.datasets.get_status(dataset_id)
        run_status = str(getattr(status_obj, "status", "unknown"))
        run_id = getattr(status_obj, "run_id", run_id)
        err = getattr(status_obj, "error", None)
        if err is not None:
            run_error = getattr(err, "message", str(err))

        ev = cli.datasets.get_evaluation(dataset_id)
        eval_status = str(getattr(ev, "status", "unknown"))

        run_done = run_status in run_terminal
        eval_done = eval_status in eval_terminal
        if run_done and eval_done:
            metrics = _improvement_from_eval(ev)
            return RunResult(
                dataset_id=dataset_id,
                run_id=run_id,
                run_status=run_status,
                evaluation_status=eval_status,
                error=run_error,
                **metrics,
            )

        if time.time() >= deadline:
            metrics = _improvement_from_eval(ev)
            return RunResult(
                dataset_id=dataset_id,
                run_id=run_id,
                run_status=run_status,
                evaluation_status=eval_status,
                error=run_error or "timed out waiting for run/evaluation",
                **metrics,
            )

        time.sleep(poll_interval)


def download(
    dataset_id: str,
    file_format: Optional[str] = None,
    client: Any = None,
) -> str:
    """Return a presigned download URL for the processed dataset."""
    cli = client or _client()
    if file_format:
        return cli.datasets.download(dataset_id, file_format=file_format)
    return cli.datasets.download(dataset_id)
