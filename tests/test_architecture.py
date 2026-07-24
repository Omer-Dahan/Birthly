"""Enforces the layering rules from SPEC.md chapter 5.

- app/core: no aiogram, no DB/SQLAlchemy imports.
- app/services: no aiogram imports.
- app/handlers: no direct SQLAlchemy/repository imports (no raw SQL in handlers).
"""

from __future__ import annotations

import ast
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"


def _imported_top_level_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def _python_files(subdir: str) -> list[Path]:
    d = APP_DIR / subdir
    if not d.exists():
        return []
    return list(d.rglob("*.py"))


def test_core_does_not_import_aiogram() -> None:
    offenders = [f for f in _python_files("core") if "aiogram" in _imported_top_level_modules(f)]
    assert not offenders, f"app/core must not import aiogram: {offenders}"


def test_core_does_not_import_sqlalchemy() -> None:
    offenders = [
        f for f in _python_files("core") if "sqlalchemy" in _imported_top_level_modules(f)
    ]
    assert not offenders, f"app/core must not import sqlalchemy: {offenders}"


def test_services_does_not_import_aiogram() -> None:
    offenders = [
        f for f in _python_files("services") if "aiogram" in _imported_top_level_modules(f)
    ]
    assert not offenders, f"app/services must not import aiogram: {offenders}"


def test_handlers_does_not_import_sqlalchemy_directly() -> None:
    offenders = [
        f for f in _python_files("handlers") if "sqlalchemy" in _imported_top_level_modules(f)
    ]
    assert not offenders, f"app/handlers must not import sqlalchemy directly: {offenders}"
