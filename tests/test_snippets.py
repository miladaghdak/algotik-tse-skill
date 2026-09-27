"""Validate every python snippet in the skill against the real package.

Checks, fully offline:
1. Each ```python block parses (ast).
2. Each `att.<fn>(...)` call exists.
3. Each keyword argument used is accepted by the real signature
   (positional args are not checked — only names).

Signature-display snippets use a bare ``*`` to mark keyword-only
parameters. That is function-definition syntax, not call syntax, so the
checker strips the bare star before parsing; everything else in the
snippet (function names, keyword arguments) is still validated.
"""

import ast
import inspect
import re
from pathlib import Path

import algotik_tse as att

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILES = [REPO_ROOT / "SKILL.md"] + sorted(
    (REPO_ROOT / "references").glob("*.md")
)


def _python_blocks():
    for path in SKILL_FILES:
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"```python\n(.*?)```", text, re.DOTALL):
            yield path.name, match.group(1)
    for path in sorted((REPO_ROOT / "examples").glob("*.py")):
        yield path.name, path.read_text(encoding="utf-8")


def _normalize_signature_display(code):
    """Strip bare ``*`` markers (keyword-only display) so calls can parse."""
    code = re.sub(r",\s*\*(?=\s*,|\s*\))", "", code)
    code = re.sub(r"\(\s*\*,\s*", "(", code)
    return code


def _parse(fname, code):
    try:
        return ast.parse(_normalize_signature_display(code)), None
    except SyntaxError as exc:
        return None, f"{fname}: snippet does not parse: {exc}\n{code}"


def _call_nodes(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "att":
                yield node.func.attr, node


def test_all_snippets_parse():
    blocks = list(_python_blocks())
    assert len(blocks) >= 30, "expected a substantial number of snippets"
    for name, code in blocks:
        _, error = _parse(name, code)
        assert error is None, error


def test_snippet_kwargs_match_real_signatures():
    problems = []
    checked = 0
    for fname, code in _python_blocks():
        tree, error = _parse(fname, code)
        assert error is None, error
        for attr, node in _call_nodes(tree):
            fn = getattr(att, attr, None)
            if fn is None or not callable(fn):
                problems.append(f"{fname}: att.{attr} is not callable")
                continue
            try:
                sig = inspect.signature(fn)
            except (TypeError, ValueError):
                continue
            if any(
                p.kind == inspect.Parameter.VAR_KEYWORD
                for p in sig.parameters.values()
            ):
                continue  # **kwargs passthrough: nothing to check
            accepts_kw = {
                p.name
                for p in sig.parameters.values()
                if p.kind in (
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.KEYWORD_ONLY,
                )
            }
            for kw in node.keywords:
                checked += 1
                if kw.arg is None:  # **unpacking
                    continue
                if kw.arg not in accepts_kw:
                    problems.append(
                        f"{fname}: att.{attr}(...) has no parameter {kw.arg!r}"
                    )
    assert not problems, "\n".join(problems)
    assert checked >= 100, f"only {checked} keyword usages checked — widen coverage"
