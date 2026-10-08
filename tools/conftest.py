"""pytest support: the tools/test_*.py files are plain scripts (`python tools/test_x.py`, exit 0 = pass) whose
functions take a `fails` list, so pytest must not collect their functions. Each script runs as ONE pytest item
instead, and its printed output is shown when it fails. `python tools/check.py` stays the full check."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def pytest_pycollect_makemodule(module_path: Path, parent):
    """Replaces pytest's module collector for these files: one item per script, never its functions."""
    return ScriptFile.from_parent(parent, path=module_path)


class ScriptFile(pytest.File):
    def collect(self):
        yield ScriptItem.from_parent(self, name=self.path.stem)


class ScriptItem(pytest.Item):
    def runtest(self):
        run = subprocess.run([sys.executable, str(self.path)], cwd=self.path.parent.parent,
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        if run.returncode != 0:
            raise ScriptFailed(run.stdout + run.stderr)

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, ScriptFailed):
            return str(excinfo.value)[-4000:]
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, 0, f"script {self.path.name}"


class ScriptFailed(Exception):
    pass
