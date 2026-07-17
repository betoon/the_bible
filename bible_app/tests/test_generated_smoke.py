"""Generated smoke tests for Testing Workbench.

These tests are intentionally conservative. They check syntax and JSON data
without launching GUI windows or making network requests.
"""

import json
import py_compile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IGNORE_DIRS = {".git", ".venv", "venv", "env", "__pycache__", "build", "dist", "test_logs"}


def project_files(suffix):
    for path in PROJECT_ROOT.rglob(f"*{suffix}"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.is_file():
            yield path


class GeneratedSmokeTests(unittest.TestCase):
    def test_python_files_compile(self):
        for path in project_files(".py"):
            with self.subTest(path=str(path.relative_to(PROJECT_ROOT))):
                py_compile.compile(str(path), doraise=True)

    def test_json_files_parse(self):
        for path in project_files(".json"):
            with self.subTest(path=str(path.relative_to(PROJECT_ROOT))):
                json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
