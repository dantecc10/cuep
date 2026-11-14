import argparse

import pytest

from scripts.reset_academic_year import ResetError, _confirm_required, _database_url


def _args(**kwargs) -> argparse.Namespace:
    base = {"year": 2027, "close_only": False, "confirm": None, "dry_run": False}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_confirm_requires_exact_phrase():
    with pytest.raises(ResetError):
        _confirm_required(_args(confirm="RESET 2026"), 2026, 2027)
    with pytest.raises(ResetError):
        _confirm_required(_args(confirm="reset 2027"), 2026, 2027)
    assert _confirm_required(_args(confirm="RESET 2027"), 2026, 2027) == "RESET 2027"


def test_confirm_close_only_uses_current_year():
    args = _args(close_only=True, confirm="CLOSE 2026")
    assert _confirm_required(args, 2026, 2026) == "CLOSE 2026"
    with pytest.raises(ResetError):
        _confirm_required(_args(close_only=True, confirm="RESET 2026"), 2026, 2026)


def test_dry_run_does_not_require_confirmation():
    assert _confirm_required(_args(dry_run=True), 2026, 2027) == ""


def test_database_url_uses_plain_postgres_driver():
    url = _database_url()
    assert url.startswith("postgresql://")
    assert "+asyncpg" not in url
