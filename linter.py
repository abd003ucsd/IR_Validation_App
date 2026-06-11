"""Lightweight validation script for the IR validation app.

This script is intended to serve as the repository's automated sanity check:
- compile all Python modules with py_compile
- fail if deprecated Streamlit width API usage remains in app.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import py_compile


REPO_ROOT = Path(__file__).resolve().parent
PYTHON_FILES = [
    "app.py",
    "ui_theme.py",
    "data_loading.py",
    "db_config.py",
    "matching_engine.py",
    "validation_utils.py",
]


def main() -> int:
    failures: list[str] = []

    for relative_name in PYTHON_FILES:
        file_path = REPO_ROOT / relative_name
        try:
            py_compile.compile(str(file_path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{relative_name}: {exc}")

    app_path = REPO_ROOT / "app.py"
    app_text = app_path.read_text(encoding="utf-8")
    if "use_container_width" in app_text:
        failures.append("app.py still contains deprecated use_container_width usage")

    if failures:
        print("Validation failed:")
        for item in failures:
            print(f" - {item}")
        return 1

    print("Validation passed: py_compile succeeded and no deprecated width API usage remains.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
