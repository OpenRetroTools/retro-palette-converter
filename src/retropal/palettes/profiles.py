"""Platform profiles that group related conversion palettes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformProfile:
    """Describe a hardware platform and its selectable palette modes."""

    id: str
    name: str
    family: str
    manufacturer: str
    year: int
    palette_ids: tuple[str, ...]
    default_palette_id: str
    notes: str
    tags: tuple[str, ...] = ()


_PROFILES = (
    PlatformProfile(
        id="sinclair-zx-spectrum-48k",
        name="Sinclair ZX Spectrum 48K",
        family="Sinclair",
        manufacturer="Sinclair Research",
        year=1982,
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
        family="Sinclair",
        manufacturer="Sinclair Research",
        year=1985,
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
)
_BY_ID = {profile.id: profile for profile in _PROFILES}


def iter_platform_profiles() -> tuple[PlatformProfile, ...]:
    """Return registered platform profiles in display order."""
    return _PROFILES


def get_platform_profile(profile_id: str) -> PlatformProfile:
    """Look up a platform profile by canonical ID."""
    try:
        return _BY_ID[profile_id]
    except KeyError as exc:
        raise KeyError(f"Unknown platform profile: {profile_id}") from exc
