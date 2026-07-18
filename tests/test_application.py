from __future__ import annotations

import builtins

import pytest

from retropal.application import run_gui


def test_run_gui_explains_missing_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def reject_pyside(name: str, *args: object, **kwargs: object) -> object:
        if name.startswith("PySide6"):
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_pyside)
    with pytest.raises(RuntimeError, match="extra gui"):
        run_gui([])
