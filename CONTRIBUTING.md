# Contributing

## Local checks

```bash
uv sync --extra dev
./scripts/check.sh
```

Keep the image-processing core independent from PySide6 so it remains reusable by the CLI and other projects.
