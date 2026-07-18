# Changes

- Add `BatchConvertDialog` with directory pickers and conversion options.
- Run conversion in a `QThread` so the GUI remains responsive.
- Show per-file progress and converted/skipped/failed totals.
- Support cancellation between files and opening the output directory.
- Extend `convert_batch()` with optional progress and cancellation callbacks.
- Add regression tests for progress and cancellation.
- Update README and changelog.
