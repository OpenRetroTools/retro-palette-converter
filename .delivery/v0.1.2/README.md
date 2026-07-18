# Retro Palette Converter v0.1.2 delivery

Apply after extracting this ZIP over the repository:

```bash
./.delivery/v0.1.2/APPLY.sh
uv sync --python 3.12 --extra dev --extra gui --extra release
uv run ruff check . --fix
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run pytest
./scripts/verify-release.sh
./.delivery/v0.1.2/VERIFY.sh
```

Build and test the Linux package:

```bash
rm -rf build dist
uv run --python 3.12 --with pyinstaller python scripts/build_release.py
uv run --python 3.12 python scripts/add_linux_launcher_to_release.py
unzip -l dist/retro-palette-converter-linux-x86_64.zip \
  | grep -E 'RetroPaletteConverter.sh|README-LINUX.txt'
```
