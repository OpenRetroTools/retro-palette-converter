$ErrorActionPreference = "Stop"

Write-Host "Local builds are for development diagnostics only."
Write-Host "Official packages are built by GitHub Actions."
uv run --with pyinstaller python scripts/build_release.py
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
