# Amiga CRNG colour cycling

M2.5 implements editing and deterministic preview of Electronic Arts Deluxe
Paint `CRNG` ranges. It does not interpret Brilliance `DRNG`/`BRNG`, HAM, EHB,
or arbitrary animation formats.

## Historical basis

The field layout, direction, inclusive range, and timing follow the original
Commodore/EA ILBM material:

- [EA IFF 85 / ILBM specification scan](https://amiga.net.au/files/Tech_Amiga/Commodore_EA_IFF_85_Standard.pdf), “Nonstandard Data Chunks — CRNG”.
- [Commodore Amiga Developer CD ILBM regular expression](https://amigadev.elowar.com/read/ADCD_2.1/Devices_Manual_guide/node01BB.html), confirming zero or more ordered CRNG chunks before BODY.
- [Maintained ILBM specification transcription](https://documentation.help/LightWave/ilbm.html), including the Deluxe Paint rate-36 warning and BODY/ByteRun1 rules.

The eight-byte big-endian record is:

```text
UWORD reserved
UWORD rate
UWORD flags
UBYTE low
UBYTE high
```

`low..high` is inclusive. Flag bit 0 (`RNG_ACTIVE`) enables the range. Bit 1
(`RNG_REVERSE`) reverses it. Normal cycling moves each colour to the next
higher register and wraps `high` into `low`; reverse does the opposite. All
other flag bits and the reserved word are retained exactly.

The documented rate is:

```text
steps_per_second = rate * 60 / 16384
seconds_per_step = 16384 / (rate * 60)
```

Thus 16384 is 60 steps/second, 8192 is 30, and the documented integer value
273 approximates one step/second. The engine evaluates step boundaries with
exact rational arithmetic, so it does not accumulate timer drift. Historical
documentation warns that some Deluxe Paint output writes ACTIVE with rate 36
to mean no cycling. RetroPal reports that convention and treats rates 0 and 36
as stationary during preview without changing the stored bit or value. Other
small nonzero rates retain their documented slow timing.

## Model, validation, and execution

`ColorCycleRange` is immutable. `edited()` changes only requested known fields,
preserving reserved and unknown flag bits. Documents provide immutable add,
replace, and remove operations while retaining range order.

Stable validation issues cover palette bounds, single-entry ranges, zero rate,
the rate-36 convention, unknown flags, and overlapping active ranges. Bounds
violations block writeback. Single-entry and disabled ranges remain stored.
Overlaps are legal but warned: simulation applies ranges sequentially in CRNG
chunk order. They are never merged.

`palette_at(base, ranges, elapsed)` returns a new ordered RGB tuple. The base
palette never changes. Each range derives its absolute step from elapsed time;
GUI timers merely request states and do not advance mutable engine counters.

## Indexed image preview

The read-only decoder produces `IndexedIlbmImage(width, height,
pixel_indexes, mask)`. The planar index buffer remains constant while the
renderer combines it with each derived palette state. This is palette cycling,
not pixel animation or re-quantization.

The supported subset is deliberately narrow:

- one 20-byte BMHD and one BODY;
- 1–8 indexed bitplanes, least-significant plane first;
- ILBM word-padded rows, including odd widths;
- no mask, one mask plane, or transparent-colour masking;
- uncompressed BODY or read-only ByteRun1 compression.

ByteRun1 rows are decoded independently. Literal runs, repeated runs, and the
`-128`/byte `128` no-op are supported with truncation, row overflow, output
underflow, and trailing-data checks. No encoder is included; BODY is never
rewritten.

HAM and EHB CAMG modes, unsupported masking/compression, invalid BMHD, and
unsupported plane counts produce controlled preview errors. CRNG metadata can
still be inspected and edited when image preview is unavailable.

## Preservation and unsupported cycling metadata

CRNG save-as replaces only selected eight-byte CRNG payloads or inserts/removes
the requested CRNG chunk. Existing CMAP, BODY, annotations, unknown chunks,
untouched CRNG payloads, pad bytes, and ordering remain byte-identical. FORM
lengths are regenerated correctly. A new range is inserted after the last
existing CRNG, or immediately before BODY when none exists.

`DRNG` and `BRNG` are detected, reported as preserved-but-not-simulated, and
retained byte-for-byte. No semantics are inferred from Brilliance files and
Brilliance PLT export remains unsupported.

## CLI

```bash
retropal ilbm cycles picture.iff --json
retropal ilbm cycle-at picture.iff --time 1/60 --json
retropal ilbm cycle-preview picture.iff --time 2.5 --output preview.png
retropal ilbm cycle-add picture.iff --output added.iff \
  --rate 273 --low 4 --high 7 --active --no-reverse
retropal ilbm cycle-set picture.iff 0 --output edited.iff \
  --rate 8192 --reverse
retropal ilbm cycle-remove picture.iff 0 --output removed.iff
```

Time accepts decimal seconds or an exact fraction. Editing always writes a
separate output and refuses overwrite without `--overwrite`.

## GUI

Use **Tools → Custom Palettes… → Cycle ILBM…**. The focused editor shows stored
ranges, validation warnings, current animated palette swatches, and an indexed
image preview where supported. It can add, apply, remove, enable/disable,
reverse, and change rate/bounds, then deliberately save to a new ILBM.

Play, pause, restart, and preview-speed controls are transient. Preview speed
does not alter the stored CRNG rate. Unsupported image modes leave range
inspection/editing available.

## Limitations

No DRNG/BRNG simulation or editing, CCRT editing, HAM/EHB rendering, ByteRun1
encoding, BODY modification, frame export, or Brilliance writer is provided.
