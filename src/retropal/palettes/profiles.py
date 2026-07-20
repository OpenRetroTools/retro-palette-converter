"""Platform profiles that group related conversion palettes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    """Describe a hardware platform and its selectable palette modes."""

    id: str
    name: str
    platform: str
    family: str
    platform_family: str
    generation: str
    manufacturer: str
    year: int
    color_count: int
    palette_ids: tuple[str, ...]
    default_palette_id: str
    notes: str
    tags: tuple[str, ...] = ()


_PROFILES = (
    PlatformProfile(
        id="sinclair-zx-spectrum-48k",
        name="Sinclair ZX Spectrum 48K",
        platform="ZX Spectrum 48K",
        family="Sinclair",
        platform_family="ZX Spectrum",
        generation="8-bit home computer",
        manufacturer="Sinclair Research",
        year=1982,
        color_count=15,
        palette_ids=(
            "zx-spectrum-48k-normal",
            "zx-spectrum-48k-bright",
            "zx-spectrum-48k-auto",
        ),
        default_palette_id="zx-spectrum-48k-auto",
        notes=(
            "Uses the Spectrum's normal and BRIGHT colours without enforcing "
            "8×8 attribute-cell ink/paper restrictions."
        ),
        tags=("sinclair", "zx-spectrum", "48k"),
    ),
    PlatformProfile(
        id="sinclair-zx-spectrum-128k",
        name="Sinclair ZX Spectrum 128K",
        platform="ZX Spectrum 128K",
        family="Sinclair",
        platform_family="ZX Spectrum",
        generation="8-bit home computer",
        manufacturer="Sinclair Research",
        year=1985,
        color_count=15,
        palette_ids=(
            "zx-spectrum-128k-normal",
            "zx-spectrum-128k-bright",
            "zx-spectrum-128k-auto",
        ),
        default_palette_id="zx-spectrum-128k-auto",
        notes=(
            "Uses the 128K model's Spectrum-compatible normal and BRIGHT colours "
            "without enforcing 8×8 attribute-cell restrictions."
        ),
        tags=("sinclair", "zx-spectrum", "128k"),
    ),
    PlatformProfile(
        id="nintendo-nes",
        name="Nintendo Entertainment System (NES)",
        platform="Nintendo Entertainment System",
        family="Nintendo",
        platform_family="Nintendo home console",
        generation="third generation",
        manufacturer="Nintendo",
        year=1983,
        color_count=64,
        palette_ids=("nes-default",),
        default_palette_id="nes-default",
        notes=(
            "Representative 2C02 NTSC palette. Palette emphasis bits and regional "
            "PPU differences are outside this display-palette milestone."
        ),
        tags=("nintendo", "nes", "famicom", "console", "8-bit"),
    ),
    PlatformProfile(
        id="nintendo-game-boy",
        name="Nintendo Game Boy",
        platform="Game Boy",
        family="Nintendo",
        platform_family="Game Boy",
        generation="fourth generation handheld",
        manufacturer="Nintendo",
        year=1989,
        color_count=4,
        palette_ids=("gameboy-dmg",),
        default_palette_id="gameboy-dmg",
        notes="Four-shade DMG LCD approximation; tile restrictions are not emulated.",
        tags=("nintendo", "game-boy", "dmg", "handheld", "monochrome"),
    ),
    PlatformProfile(
        id="nintendo-game-boy-pocket",
        name="Nintendo Game Boy Pocket",
        platform="Game Boy Pocket",
        family="Nintendo",
        platform_family="Game Boy",
        generation="fourth generation handheld",
        manufacturer="Nintendo",
        year=1996,
        color_count=4,
        palette_ids=("gameboy-pocket",),
        default_palette_id="gameboy-pocket",
        notes="Four-shade neutral LCD approximation; tile restrictions are not emulated.",
        tags=("nintendo", "game-boy", "pocket", "handheld", "monochrome"),
    ),
    PlatformProfile(
        id="nintendo-game-boy-color",
        name="Nintendo Game Boy Color",
        platform="Game Boy Color",
        family="Nintendo",
        platform_family="Game Boy",
        generation="fifth generation handheld",
        manufacturer="Nintendo",
        year=1998,
        color_count=32,
        palette_ids=("gameboy-color",),
        default_palette_id="gameboy-color",
        notes=(
            "Representative sample of the 15-bit display colour space; palette "
            "banks and tile restrictions are not emulated."
        ),
        tags=("nintendo", "game-boy-color", "gbc", "handheld", "15-bit"),
    ),
    PlatformProfile(
        id="nintendo-snes",
        name="Nintendo Super NES (SNES)",
        platform="Super Nintendo Entertainment System",
        family="Nintendo",
        platform_family="Nintendo home console",
        generation="fourth generation",
        manufacturer="Nintendo",
        year=1990,
        color_count=64,
        palette_ids=("snes-default",),
        default_palette_id="snes-default",
        notes=(
            "Representative sample of the 15-bit display colour space; colour "
            "math and sprite/background priorities are not emulated."
        ),
        tags=("nintendo", "snes", "super-famicom", "console", "16-bit"),
    ),
    PlatformProfile(
        id="sega-master-system",
        name="Sega Master System",
        platform="Sega Master System",
        family="Sega",
        platform_family="Sega home console",
        generation="third generation",
        manufacturer="Sega",
        year=1985,
        color_count=64,
        palette_ids=("master-system-default",),
        default_palette_id="master-system-default",
        notes=(
            "Complete 6-bit RGB display colour space for representative conversion. "
            "CRAM layout and other hardware behaviour are not emulated."
        ),
        tags=("sega", "master-system", "sms", "console", "8-bit"),
    ),
    PlatformProfile(
        id="sega-game-gear",
        name="Sega Game Gear",
        platform="Sega Game Gear",
        family="Sega",
        platform_family="Sega handheld",
        generation="fourth generation handheld",
        manufacturer="Sega",
        year=1990,
        color_count=4096,
        palette_ids=("game-gear-default",),
        default_palette_id="game-gear-default",
        notes=(
            "Complete deterministic 12-bit RGB colour space for conversion. CRAM, "
            "palette slots, and LCD characteristics are not emulated."
        ),
        tags=("sega", "game-gear", "handheld", "12-bit"),
    ),
    PlatformProfile(
        id="sega-megadrive",
        name="Sega Mega Drive / Genesis",
        platform="Sega Mega Drive / Genesis",
        family="Sega",
        platform_family="Sega home console",
        generation="fourth generation",
        manufacturer="Sega",
        year=1988,
        color_count=512,
        palette_ids=("megadrive-default",),
        default_palette_id="megadrive-default",
        notes=(
            "Complete deterministic 9-bit RGB colour space for representative "
            "conversion. CRAM, shadow/highlight, priorities, and animation are not emulated."
        ),
        tags=("sega", "mega-drive", "genesis", "console", "16-bit", "9-bit"),
    ),
    PlatformProfile(
        id="ibm-pc-cga",
        name="IBM PC — CGA",
        platform="IBM Color Graphics Adapter",
        family="Classic PC",
        platform_family="IBM PC graphics",
        generation="first-generation IBM PC graphics",
        manufacturer="IBM",
        year=1981,
        color_count=4,
        palette_ids=("cga-palette-0", "cga-palette-1"),
        default_palette_id="cga-palette-0",
        notes="Canonical four-colour RGBI palettes; composite artifact colours are not emulated.",
        tags=("ibm", "pc", "cga", "rgbi", "2-bit"),
    ),
    PlatformProfile(
        id="ibm-pc-ega",
        name="IBM PC — EGA",
        platform="IBM Enhanced Graphics Adapter",
        family="Classic PC",
        platform_family="IBM PC graphics",
        generation="second-generation IBM PC graphics",
        manufacturer="IBM",
        year=1984,
        color_count=16,
        palette_ids=("ega-default",),
        default_palette_id="ega-default",
        notes="Canonical EGA 16-colour default selection from its 64-colour RGB space.",
        tags=("ibm", "pc", "ega", "4-bit"),
    ),
    PlatformProfile(
        id="ibm-pc-vga-16",
        name="IBM PC — VGA 16",
        platform="IBM Video Graphics Array",
        family="Classic PC",
        platform_family="IBM PC graphics",
        generation="VGA",
        manufacturer="IBM",
        year=1987,
        color_count=16,
        palette_ids=("vga-16",),
        default_palette_id="vga-16",
        notes="Canonical VGA 16-colour default; DAC reprogramming is not emulated.",
        tags=("ibm", "pc", "vga", "4-bit"),
    ),
    PlatformProfile(
        id="ibm-pc-vga-256",
        name="IBM PC — VGA 256",
        platform="IBM Video Graphics Array",
        family="Classic PC",
        platform_family="IBM PC graphics",
        generation="VGA",
        manufacturer="IBM",
        year=1987,
        color_count=256,
        palette_ids=("vga-256",),
        default_palette_id="vga-256",
        notes=(
            "Canonical mode-13h-style default palette; DAC programming and gamma are not emulated."
        ),
        tags=("ibm", "pc", "vga", "8-bit", "mode-13h"),
    ),
    PlatformProfile(
        id="apple-macintosh-bw",
        name="Apple Macintosh — Black & White",
        platform="Apple Macintosh",
        family="Apple",
        platform_family="Classic Macintosh",
        generation="68k Macintosh",
        manufacturer="Apple Computer",
        year=1984,
        color_count=2,
        palette_ids=("macintosh-bw",),
        default_palette_id="macintosh-bw",
        notes="One-bit black-and-white display palette; QuickDraw behaviour is not emulated.",
        tags=("apple", "macintosh", "monochrome", "1-bit"),
    ),
    PlatformProfile(
        id="apple-macintosh-8bit",
        name="Apple Macintosh — 8-bit System 7",
        platform="Apple Macintosh II",
        family="Apple",
        platform_family="Classic Macintosh",
        generation="System 7 era",
        manufacturer="Apple Computer",
        year=1991,
        color_count=256,
        palette_ids=("macintosh-8bit",),
        default_palette_id="macintosh-8bit",
        notes=(
            "Representative System 7-era conversion palette; QuickDraw behaviour is not emulated."
        ),
        tags=("apple", "macintosh", "system-7", "8-bit"),
    ),
    PlatformProfile(
        id="hercules-monochrome",
        name="Hercules Monochrome",
        platform="Hercules Graphics Card",
        family="Classic PC",
        platform_family="IBM PC graphics",
        generation="monochrome PC graphics",
        manufacturer="Hercules Computer Technology",
        year=1982,
        color_count=2,
        palette_ids=("hercules-default",),
        default_palette_id="hercules-default",
        notes=(
            "Logical black-and-white display values; monitor phosphor "
            "characteristics are not emulated."
        ),
        tags=("hercules", "pc", "monochrome", "1-bit"),
    ),
    PlatformProfile(
        id="sharp-x68000",
        name="Sharp X68000",
        platform="Sharp X68000",
        family="Sharp",
        platform_family="X68000",
        generation="16/32-bit Japanese home computer",
        manufacturer="Sharp",
        year=1987,
        color_count=256,
        palette_ids=("x68000-default",),
        default_palette_id="x68000-default",
        notes=(
            "Representative deterministic 256-colour conversion palette from the "
            "15-bit display space."
        ),
        tags=("sharp", "x68000", "japanese-computer", "15-bit", "8-bit-indexed"),
    ),
)


def _index_profiles(profiles: tuple[PlatformProfile, ...]) -> dict[str, PlatformProfile]:
    by_id: dict[str, PlatformProfile] = {}
    display_names: set[str] = set()
    for profile in profiles:
        if profile.id in by_id:
            raise ValueError(f"Duplicate platform profile ID: {profile.id}")
        folded_name = profile.name.casefold()
        if folded_name in display_names:
            raise ValueError(f"Duplicate platform profile display name: {profile.name}")
        if profile.default_palette_id not in profile.palette_ids:
            raise ValueError(f"Profile {profile.id} has a default outside palette_ids")
        if len(set(profile.palette_ids)) != len(profile.palette_ids):
            raise ValueError(f"Profile {profile.id} contains duplicate palette IDs")
        by_id[profile.id] = profile
        display_names.add(folded_name)
    return by_id


_BY_ID = _index_profiles(_PROFILES)


def iter_platform_profiles() -> tuple[PlatformProfile, ...]:
    """Return registered platform profiles in display order."""
    return _PROFILES


def get_platform_profile(profile_id: str) -> PlatformProfile:
    """Look up a platform profile by canonical ID."""
    try:
        return _BY_ID[profile_id]
    except KeyError as exc:
        raise KeyError(f"Unknown platform profile: {profile_id}") from exc
