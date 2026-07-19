# v0.1.2 release checklist

- [ ] Run `uv sync --python 3.12 --extra dev --extra gui --extra release`
- [ ] Run `uv run ruff check .`
- [ ] Run `uv run ruff format --check .`
- [ ] Run `uv run pytest`
- [ ] Run `./scripts/verify-release.sh`
- [ ] Build the Linux package with Python 3.12
- [ ] Build the Crostini-aware launcher into the Linux ZIP
- [ ] Confirm `RetroPaletteConverter.sh` and `README-LINUX.txt` are present
- [ ] Extract the Linux ZIP into a clean directory and start it on Crostini
- [ ] Confirm the Windows, Linux, and macOS Apple Silicon workflows are green
- [ ] Commit with `Release v0.1.2`
- [ ] Tag `v0.1.2` and push the tag
- [ ] Smoke-test the GitHub Release downloads
- [ ] Run the itch.io publishing workflow for `v0.1.2`
- [ ] Publish a short v0.1.2 devlog
