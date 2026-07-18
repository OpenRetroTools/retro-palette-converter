# v0.1.2 Fix

1. Replace `scripts/add_linux_launcher_to_release.py` with this version.
2. Replace `tests/test_linux_release_launcher.py`.
3. Run:

```bash
uv run ruff check scripts tests --fix
uv run ruff format scripts tests
uv run pytest
uv run python scripts/add_linux_launcher_to_release.py
```
