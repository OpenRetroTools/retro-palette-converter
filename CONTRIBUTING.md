# Contributing

## Local checks

```bash
uv sync --extra dev
./scripts/check.sh
```

The check script runs formatting, linting, static type checking with
`basedpyright`, and the complete test suite. To run type checking alone:

```bash
uv run basedpyright
```

Keep the image-processing core independent from PySide6 so it remains reusable by the CLI and other projects.

Custom palette architecture is documented in
[`docs/custom-palettes.md`](docs/custom-palettes.md). Keep the immutable,
format-independent model separate from native persistence, future interchange
adapters, Qt widgets, and the repository-owned built-in palette registry.
Standard codec capabilities and binary-format references are documented in
[`docs/palette-interchange.md`](docs/palette-interchange.md). Each codec must
continue to map directly to `CustomPalette` and report metadata loss explicitly.
Indexed-image parsing rules are documented in
[`docs/indexed-image-palettes.md`](docs/indexed-image-palettes.md). Parsers must
bounds-check declared structures and preserve complete stored palette tables;
pixel usage and transparency remain outside `CustomPalette` identity.
