"""One-to-one API coverage: every exported package name must be documented
in this skill, and every name the skill mentions must exist in the package.

This is the machine-checkable half of the cross-validation against
algotik-tse 1.8.0. It runs fully offline.
"""

import re
from pathlib import Path

import algotik_tse as att
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = [REPO_ROOT / "SKILL.md"] + sorted(
    (REPO_ROOT / "references").glob("*.md")
)


def _skill_corpus():
    text = []
    for path in SKILL_FILES:
        assert path.exists(), f"missing skill file: {path}"
        text.append(path.read_text(encoding="utf-8"))
    return "\n".join(text)


def test_package_version_is_1_8_0():
    assert att.__version__ == "1.8.0"


def test_expected_export_count():
    # The documented API surface of 1.8.0. If this changes, the package was
    # updated and the skill needs a revision pass.
    assert len(att.__all__) == 167


@pytest.mark.parametrize("name", sorted(att.__all__))
def test_every_export_is_documented(name):
    """One-to-one: each of the 167 exported names appears in the skill."""
    corpus = _skill_corpus()
    assert re.search(
        r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])",
        corpus,
    ), (
        f"exported name {name!r} is not documented in SKILL.md or references/"
    )


def test_skill_mentions_only_real_names():
    """No invented API names: every att.* reference in the skill resolves."""
    corpus = _skill_corpus()
    mentioned = set(re.findall(r"\batt\.([A-Za-z_][A-Za-z0-9_]*)", corpus))
    unknown = sorted(m for m in mentioned if not hasattr(att, m))
    assert not unknown, f"skill references unknown attribute(s): {unknown}"


def test_reference_files_exist():
    expected = {
        "price-and-flow.md",
        "instrument-identity.md",
        "live-market.md",
        "market-stream.md",
        "local-history.md",
        "market-analytics.md",
        "industries.md",
        "ownership.md",
        "options.md",
        "fixed-income.md",
        "funds-etfs-bonds.md",
        "energy-commodity.md",
        "tgju-assets.md",
        "http-client.md",
    }
    actual = {p.name for p in (REPO_ROOT / "references").glob("*.md")}
    assert expected == actual, (
        f"reference set mismatch: missing={expected - actual}, "
        f"extra={actual - expected}"
    )


def test_examples_exist_and_parse():
    example_files = sorted((REPO_ROOT / "examples").glob("*.py"))
    assert len(example_files) >= 12, "expected at least 12 example scripts"
    import ast

    for path in example_files:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_legacy_alias_table_is_complete():
    legacy = [
        "stock", "stock_RI", "stock_RL", "stock_capital_increase",
        "stock_intraday", "stockdetail", "stock_information",
        "stock_statistics", "stock_introduction", "stocklist", "shareholders",
        "currency_coin", "market_watch", "market_client_type", "market_data",
    ]
    corpus = _skill_corpus()
    for name in legacy:
        assert name in corpus, f"legacy alias {name} missing from the skill"
        assert hasattr(att, name), f"package lost legacy alias {name}"
