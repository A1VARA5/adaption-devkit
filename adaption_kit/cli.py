"""cli.py - argparse command line for adaption-kit.

Subcommands: doctor, lint, suggest, estimate, run, publish, card, cover.

The SDK-backed subcommands (estimate, run) import run.py lazily so that doctor,
lint, suggest, card, and cover work even when the optional ``adaption`` SDK is
not installed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import BANNER, __version__


def _print_banner() -> None:
    print(BANNER)
    print("-" * 60)


def _split_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _cmd_doctor(args: argparse.Namespace) -> int:
    from .doctor import doctor

    report = doctor()
    print(report.summary())
    # doctor never fails the process; WARN is advisory only.
    return 0


def _cmd_suggest(args: argparse.Namespace) -> int:
    from .suggest import suggest_mapping

    result = suggest_mapping(args.path)
    print(result.summary())
    if result.error:
        return 2
    return 0 if result.confident and result.mapping() else 1


def _cmd_lint(args: argparse.Namespace) -> int:
    from .preflight import FAIL, lint_dataset

    report = lint_dataset(
        args.path,
        prompt=args.prompt,
        completion=args.completion,
        context=_split_csv(args.context),
    )
    print(report.summary())
    return 1 if report.status == FAIL else 0


def _cmd_estimate(args: argparse.Namespace) -> int:
    from .run import SdkNotInstalled, estimate

    try:
        est = estimate(
            args.dataset_id,
            prompt=args.prompt,
            completion=args.completion,
            context=_split_csv(args.context),
            chat=args.chat,
            deduplication=_tri(args.deduplication),
            prompt_rephrase=_tri(args.prompt_rephrase),
            reasoning_traces=_tri(args.reasoning_traces),
        )
    except SdkNotInstalled as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2

    print("estimate (no run started):")
    print("  estimated_credits_consumed: "
          + str(getattr(est, "estimated_credits_consumed", "unknown")))
    print("  estimated_minutes        : "
          + str(getattr(est, "estimated_minutes", "unknown")))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    from .run import SdkNotInstalled, pilot, run_full, wait_for_result

    starter = pilot if args.pilot else run_full
    kwargs = dict(
        prompt=args.prompt,
        completion=args.completion,
        context=_split_csv(args.context),
        chat=args.chat,
        deduplication=_tri(args.deduplication),
        prompt_rephrase=_tri(args.prompt_rephrase),
        reasoning_traces=_tri(args.reasoning_traces),
        idempotency_key=args.idempotency_key,
    )
    if args.pilot:
        kwargs["max_rows"] = args.max_rows if args.max_rows is not None else 200
    elif args.max_rows is not None:
        kwargs["max_rows"] = args.max_rows

    try:
        run = starter(args.dataset_id, **kwargs)
    except SdkNotInstalled as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except ValueError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2

    print("run started. run_id: " + str(getattr(run, "run_id", "unknown")))
    if not args.wait:
        print("(use --wait to poll status and evaluation for improvement_percent)")
        return 0

    print("waiting for run and evaluation ...")
    result = wait_for_result(args.dataset_id, timeout=args.timeout)
    print("run_status        : " + result.run_status)
    print("evaluation_status : " + result.evaluation_status)
    if result.improvement_percent is not None:
        print("improvement_percent: " + str(result.improvement_percent))
    if result.error:
        print("error: " + result.error, file=sys.stderr)
        return 1
    return 0


def _cmd_publish(args: argparse.Namespace) -> int:
    from .publish import publish

    try:
        result = publish(
            args.folder,
            hf_repo=args.hf_repo,
            kaggle_slug=args.kaggle_slug,
            private=not args.public,
        )
    except (ValueError, RuntimeError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    print(result.summary())
    return 0


def _cmd_card(args: argparse.Namespace) -> int:
    from .cards import (
        InvalidKaggleTag,
        generate_dataset_card,
        generate_kaggle_metadata,
        generate_model_card,
    )

    tags = _split_csv(args.tags)
    out = Path(args.out) if args.out else None

    if args.kind == "dataset":
        text = generate_dataset_card(
            title=args.title,
            summary=args.summary or "",
            tags=tags,
            source=args.source,
            improvement_percent=args.improvement_percent,
            row_count=args.row_count,
        )
        _write_or_print(text, out, "README.md")
        return 0

    if args.kind == "model":
        text = generate_model_card(
            title=args.title,
            summary=args.summary or "",
            base_model=args.base_model,
            tags=tags,
            dataset=args.dataset,
            improvement_percent=args.improvement_percent,
        )
        _write_or_print(text, out, "README.md")
        return 0

    # kaggle metadata
    if not args.kaggle_slug:
        print("error: --kaggle-slug is required for 'card kaggle'", file=sys.stderr)
        return 2
    try:
        meta = generate_kaggle_metadata(
            title=args.title,
            kaggle_slug=args.kaggle_slug,
            subtitle=args.summary or "",
            tags=tags,
        )
    except InvalidKaggleTag as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    text = json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    _write_or_print(text, out, "dataset-metadata.json")
    return 0


def _cmd_cover(args: argparse.Namespace) -> int:
    from .cover import generate_cover

    html = None
    if args.html:
        html_path = Path(args.html)
        if not html_path.exists():
            print("error: html file not found: " + str(html_path), file=sys.stderr)
            return 2
        html = html_path.read_text(encoding="utf-8-sig")

    result = generate_cover(
        html,
        args.out,
        title=args.title or "Adaption dataset",
        subtitle=args.subtitle or "",
    )
    print(result.summary())
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tri(value: Optional[bool]) -> Optional[bool]:
    """Pass through tri-state recipe flags (None = backend default)."""
    return value


def _write_or_print(text: str, out: Optional[Path], default_name: str) -> None:
    if out is None:
        sys.stdout.write(text)
        return
    target = out
    if out.is_dir():
        target = out / default_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print("wrote " + str(target))


def _add_recipe_flags(p: argparse.ArgumentParser) -> None:
    # Tri-state: --x sets True, --no-x sets False, absent leaves None (default).
    for name in ("deduplication", "prompt-rephrase", "reasoning-traces"):
        dest = name.replace("-", "_")
        p.add_argument("--" + name, dest=dest, action="store_true", default=None)
        p.add_argument(
            "--no-" + name, dest=dest, action="store_false", default=None
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="adaption-kit",
        description=(
            "Community, unofficial toolkit for Adaption Adaptive Data and "
            "AutoScientist. Not affiliated with Adaption Labs."
        ),
    )
    parser.add_argument(
        "--version", action="version", version="adaption-kit " + __version__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # doctor
    p_doc = sub.add_parser(
        "doctor", help="offline environment healthcheck (no network, no required deps)"
    )
    p_doc.set_defaults(func=_cmd_doctor)

    # suggest
    p_sug = sub.add_parser(
        "suggest", help="suggest a column mapping for a CSV or JSONL"
    )
    p_sug.add_argument("path", help="CSV, JSONL, or JSON file")
    p_sug.set_defaults(func=_cmd_suggest)

    # lint
    p_lint = sub.add_parser("lint", help="preflight a dataset before a run")
    p_lint.add_argument("path", help="CSV, JSONL, or JSON file")
    p_lint.add_argument("--prompt", help="prompt/instruction column (anchor)")
    p_lint.add_argument("--completion", help="completion column (anchor)")
    p_lint.add_argument("--context", help="comma-separated context column(s)")
    p_lint.set_defaults(func=_cmd_lint)

    # estimate
    p_est = sub.add_parser("estimate", help="quote credits/time, no run started")
    p_est.add_argument("dataset_id")
    p_est.add_argument("--prompt")
    p_est.add_argument("--completion")
    p_est.add_argument("--context")
    p_est.add_argument("--chat")
    _add_recipe_flags(p_est)
    p_est.set_defaults(func=_cmd_estimate)

    # run
    p_run = sub.add_parser("run", help="start an adaptation run")
    p_run.add_argument("dataset_id")
    p_run.add_argument("--prompt")
    p_run.add_argument("--completion")
    p_run.add_argument("--context")
    p_run.add_argument("--chat")
    p_run.add_argument(
        "--pilot",
        action="store_true",
        help="cap the run for cheap iteration (default 200 rows)",
    )
    p_run.add_argument("--max-rows", dest="max_rows", type=int, default=None)
    p_run.add_argument("--idempotency-key", dest="idempotency_key")
    p_run.add_argument(
        "--wait",
        action="store_true",
        help="poll run + evaluation and print improvement_percent",
    )
    p_run.add_argument("--timeout", type=float, default=1800.0)
    _add_recipe_flags(p_run)
    p_run.set_defaults(func=_cmd_run)

    # publish
    p_pub = sub.add_parser(
        "publish", help="push a folder to Hugging Face and/or Kaggle (501 workaround)"
    )
    p_pub.add_argument("folder")
    p_pub.add_argument("--hf-repo", dest="hf_repo", help="owner/name on Hugging Face")
    p_pub.add_argument(
        "--kaggle-slug", dest="kaggle_slug", help="owner/dataset-name on Kaggle"
    )
    p_pub.add_argument(
        "--public",
        action="store_true",
        help="create public (default private; Kaggle still needs UI toggle)",
    )
    p_pub.set_defaults(func=_cmd_publish)

    # card
    p_card = sub.add_parser("card", help="generate a dataset/model card or Kaggle metadata")
    p_card.add_argument("kind", choices=["dataset", "model", "kaggle"])
    p_card.add_argument("--title", required=True)
    p_card.add_argument("--summary")
    p_card.add_argument("--tags", help="comma-separated tags")
    p_card.add_argument("--source")
    p_card.add_argument("--base-model", dest="base_model")
    p_card.add_argument("--dataset", help="linked dataset id for a model card")
    p_card.add_argument("--kaggle-slug", dest="kaggle_slug")
    p_card.add_argument(
        "--improvement-percent",
        dest="improvement_percent",
        type=float,
        default=None,
    )
    p_card.add_argument("--row-count", dest="row_count", type=int, default=None)
    p_card.add_argument("--out", help="output file or directory (default stdout)")
    p_card.set_defaults(func=_cmd_card)

    # cover
    p_cov = sub.add_parser("cover", help="render an HTML cover to PNG (Playwright)")
    p_cov.add_argument("out", help="output PNG path")
    p_cov.add_argument("--html", help="HTML file to render (omit for built-in template)")
    p_cov.add_argument("--title")
    p_cov.add_argument("--subtitle")
    p_cov.set_defaults(func=_cmd_cover)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _print_banner()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
