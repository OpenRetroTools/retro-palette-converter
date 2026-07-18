"""Insert Linux launcher post-processing into the release workflow."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/release.yml")
BUILD_COMMAND = (
    "      - name: Build native package\n"
    "        run: uv run --with pyinstaller python scripts/build_release.py\n"
)
INSERT = (
    BUILD_COMMAND
    + "\n"
    + "      - name: Add Crostini-aware Linux launcher\n"
    + "        if: runner.os == 'Linux'\n"
    + "        run: |\n"
    + "          uv run python scripts/add_linux_launcher_to_release.py\n"
)


def main() -> int:
    if not WORKFLOW.is_file():
        raise SystemExit(f"Missing workflow: {WORKFLOW}")

    text = WORKFLOW.read_text(encoding="utf-8")

    if "Add Crostini-aware Linux launcher" in text:
        print("Release workflow already contains the v0.1.2 launcher step.")
        return 0

    if BUILD_COMMAND not in text:
        raise SystemExit(
            "Could not find the expected native build step in release.yml. No file was changed."
        )

    WORKFLOW.write_text(
        text.replace(BUILD_COMMAND, INSERT, 1),
        encoding="utf-8",
        newline="\n",
    )
    print("Updated .github/workflows/release.yml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
