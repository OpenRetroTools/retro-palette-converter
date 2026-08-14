# Palette analysis, validation, and conversion planning

M2.4f adds a Qt-independent preflight layer between a `CustomPalette` and an
external format or documented hardware target. Analysis and planning are pure:
they neither mutate the immutable source nor write files. Execution is a
separate operation governed by an explicit conservative policy.

```text
CustomPalette -> PaletteAnalysis -> ConversionPlan -> explicit execute
```

## Typed model

`PaletteAnalysis` contains deterministic `PaletteStatistics` and typed
`ValidationIssue` values. Issues have stable codes, a severity
(`informational`, `warning`, `lossy`, or `blocking`), affected indexes, and
metadata fields. `ConversionPlan` identifies the target, exactness,
transformations, issues, and whether export is supported. These records are
immutable and directly serializable without implementation-specific `repr`
strings.

Exactness is classified as `exact`, `metadata-loss`, `rgb-loss`, `index-loss`,
`multiple-losses`, `unsupported`, or `impossible`. Exact means identity of RGB
entries, count, order, duplicates, and populated metadata within the target's
capability—not merely similar visible colours.

Statistics include stored and unique counts, duplicate index groups, channel
minima/maxima, deterministic Rec. 601-style RGB luminance extrema (for
statistics only), 4-bit/channel exactness, and populated metadata. This
luminance is not a perceptual colour-distance metric.

## Targets

Format targets reuse the shared codec registry's preservation and import/export
capabilities. JSON preserves the complete `CustomPalette`; GPL, JASC, RIFF,
ACT, and CSV report their metadata losses. ACT's 256-entry limit is planned
before encoding. Brilliance is reported as `unsupported` for export, exactly
matching its evidence-gated import-only codec.

Hardware targets distinguish:

- **programmable colour spaces**, currently the documented Amiga OCS/ECS
  4-bit/channel targets and AGA 8-bit/channel target, with simultaneous-entry
  limits;
- **fixed palettes**, resolved from the existing fixed-palette registry, where
  exact validation requires literal membership in the target palette.

This is palette-only validation. Attribute cells, palette banks, sprites,
HAM/EHB, display timing, and other rendering restrictions are not inferred.

For 4-bit channels, exact values are `n * 17`. Proposed quantization uses
integer nearest-level rounding to 0–15 followed by the documented `n * 17`
expansion. Every old/new RGB value and affected index is recorded. Fixed
palette remapping, when explicitly enabled, uses squared Euclidean RGB
distance with deterministic target-order tie breaking; it is called RGB
distance, not perceptual distance.

## Index and metadata semantics

Stored entry count and unique RGB count are separate. Duplicate colours are
informational and retain all indexes. They are never deduplicated, sorted, or
used to evade a colour-count limit. Colour reduction is reported as an
index-affecting loss and remains analysis-only because no semantically safe
automatic reduction policy exists yet.

Format metadata loss is derived from codec capability metadata. Additional
source-context issues can carry stable boundaries such as
`indexed-transparency-not-preserved` and
`ilbm-document-metadata-not-preserved`. Transparency, CRNG, BODY, and raw IFF
chunks remain outside `CustomPalette`; planning can report their loss without
contaminating the RGB model.

`InterchangeReport` remains the report from an actual codec operation.
`ConversionPlan` is the richer preflight report produced before execution:

```text
ConversionPlan -> policy-approved execution -> codec -> InterchangeReport
```

## Execution policy

Defaults permit only exact execution. Policy flags separately control metadata
loss, channel quantization, colour reduction, index changes, and fixed-palette
remapping. Only metadata stripping through an existing codec, channel
quantization, and fixed-palette RGB remapping are currently automatic. Colour
reduction is deliberately not automatic even when its policy flag is set.
Blocked plans and rejected policy checks occur before output creation.

## CLI and GUI

```bash
retropal custom-palettes analyze my-palette --json
retropal custom-palettes plan my-palette --target-format gpl
retropal custom-palettes validate my-palette --target amiga-ocs-32
retropal custom-palettes convert my-palette --target-format gpl \
  --output palette.gpl --allow-metadata-loss
retropal custom-palettes transform my-palette --target amiga-ocs-16 \
  --output ocs.retropal-palette.json --allow-channel-quantization
```

`analyze`, `plan`, and `validate` support stable JSON output with `--json`.
Format conversion prints its plan before executing. Hardware transformation
writes a separate native palette and never replaces the source. Existing raw
`export` remains a low-level interchange operation; `convert` is the
conservative preflighted workflow.

The custom-palette dialog includes **Validate…** for format and documented
hardware targets. Export uses the same core format plan and requires explicit
confirmation for reported metadata losses.

## Known limitations

Automatic palette reduction is not implemented. Hardware validation covers
only constraints explicitly represented by the target definitions. Indexed
image and ILBM document metadata must be supplied as source-context issues
after extraction. Brilliance export, M2.5 colour-cycle editing, Delta E, and
general rendering emulation remain outside this milestone.
