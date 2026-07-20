# Palette and platform profile architecture

Retro Palette Converter separates display colours from platform selection:

- A **fixed palette** is a JSON resource in
  `src/retropal/palettes/definitions`. The registry discovers every JSON file;
  there is no palette-ID list to update.
- An **adaptive palette** is registered in `retropal.palettes` and generates
  colours from the source image.
- A **platform profile** is immutable descriptive data in
  `retropal.palettes.profiles`. It lists the palette IDs exposed by the GUI and
  identifies one default. The GUI contains no manufacturer-specific branches.

## Fixed-palette JSON schema

Every definition requires the same metadata keys:

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable canonical identifier; must be globally unique. |
| `display_name` | string | Unique user-facing name. |
| `manufacturer` | string | Hardware or palette producer. |
| `platform` | string | Target system or display standard. |
| `family` | string | Broad grouping used by palette browsing. |
| `year` | integer | Release or publication year. |
| `colour_count` | integer | Exact number of generated or explicit RGB entries. |
| `bit_depth` | string | Indexed and/or RGB precision description. |
| `dac_size` | string or null | DAC precision when applicable. |
| `palette_source` | string | Origin or reference for the RGB values. |
| `tags` | array of strings | Search and classification terms. |
| `notes` | string | Accuracy limits and important context. |

`description`, `generation`, and `platform_family` are optional descriptive
extensions. RGB data uses exactly one of these data forms:

- `colors`: explicit `[red, green, blue]` entries;
- `rgb_levels`: a complete RGB cube using the listed channel levels;
- `color_cube_levels`, with optional `base_colors` and `grayscale_levels`.

Channels are integers from 0 through 255. Registry loading rejects missing
metadata, invalid RGB values, incorrect `colour_count`, duplicate IDs, and
duplicate display names.

## Packaging

The PyInstaller hook collects every JSON resource from the definitions
package. `fixed_palette_ids()` discovers those same resources at runtime, and
`scripts/verify_packaged_palettes.py` compares the source registry with the
packaged directory. Adding a definition therefore updates both runtime
discovery and packaged verification automatically.

## Adding a platform

1. Add one or more schema-valid JSON files to the definitions package.
2. Add a `PlatformProfile` containing descriptive metadata, supported palette
   IDs, and a default palette ID.
3. Run `scripts/generate_palette_inventory.py` to refresh the generated table.
4. Add representative-colour and profile-filtering tests.
5. Run the standard validation and clean release build.

No GUI changes are needed. The profile selector and palette selector read the
registries directly.

See [the generated palette inventory](palette-inventory.md) for the current
profile-to-palette mapping.
