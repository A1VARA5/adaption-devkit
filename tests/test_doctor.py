"""Tests for adaption_kit.doctor.

The doctor is an offline healthcheck: no network, no required dependencies. It
returns a structured report plus a printable summary that mentions the Python
version and the SDK.
"""

from __future__ import annotations

from adaption_kit.doctor import PASS, WARN, DoctorReport, doctor


def test_doctor_runs_offline_and_returns_report():
    """doctor() returns a DoctorReport without any network access."""
    report = doctor()
    assert isinstance(report, DoctorReport)
    # doctor never FAILs; it is PASS or WARN only.
    assert report.status in (PASS, WARN)
    assert report.checks, "expected at least one check"


def test_doctor_summary_mentions_python_and_sdk():
    """The printable summary names Python and the SDK."""
    summary = doctor().summary()
    assert isinstance(summary, str)
    assert "Python" in summary
    assert "SDK" in summary
