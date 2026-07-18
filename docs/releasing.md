# Releasing Retro Palette Converter

Official binary packages are built only by GitHub Actions on native runners.

## Platforms

- Linux x86_64
- Windows x86_64
- macOS Intel
- macOS Apple Silicon

PyInstaller is not a cross-compiler. Each package is generated on its target
operating system.

## Test a release build without publishing

Open **Actions → Build native releases → Run workflow**.

The workflow runs linting and tests, then stores the platform ZIP files as
workflow artifacts for 14 days.

## Publish a release

```bash
git status
./scripts/verify-release.sh

git tag v0.1.0
git push origin main
git push origin v0.1.0
```

A version tag causes GitHub Actions to:

1. test the project on every target runner;
2. build each native application;
3. upload the ZIP files as workflow artifacts;
4. create the GitHub Release and attach all ZIP files.

## itch.io

Download the release ZIP files from the GitHub Release and push them with
Butler using separate channels:

```bash
butler push retro-palette-converter-windows-x86_64.zip ACCOUNT/PROJECT:windows
butler push retro-palette-converter-linux-x86_64.zip ACCOUNT/PROJECT:linux
butler push retro-palette-converter-macos-x86_64.zip ACCOUNT/PROJECT:macos-intel
butler push retro-palette-converter-macos-arm64.zip ACCOUNT/PROJECT:macos-apple-silicon
```

Replace `ACCOUNT/PROJECT` with the itch.io project identifier.

## PySide6 packaging policy

Do not add `--collect-all PySide6`.

The application uses QtCore, QtGui, and QtWidgets. Collecting every PySide6
submodule includes unrelated QML, WebEngine, 3D, SQL, Multimedia, and design
components. This greatly increases build time and package size.
