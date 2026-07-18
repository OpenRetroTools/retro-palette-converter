# Changes

- Add `CompareDitheringDialog` with a scrollable adaptive preview grid.
- Provide six useful default algorithms while allowing any registered algorithm.
- Limit comparisons to nine previews to keep rendering predictable.
- Scale only comparison previews; final conversion still uses the full source image.
- Add **Tools → Compare Dithering…** and apply the selected algorithm to the main view.
- Add validation tests for default selection, registry order, empty selection, and limits.
