# Automated itch.io publishing

Create a GitHub environment named `itch.io`.

Add this environment secret:

- `BUTLER_API_KEY`

Add this environment variable:

- `ITCH_TARGET` = `pgousdal/retro-palette-converter`

To publish an existing GitHub Release:

1. Open **Actions**.
2. Select **Publish existing release to itch.io**.
3. Click **Run workflow**.
4. Enter a tag such as `v0.1.0`.

The workflow downloads the release ZIP files directly from GitHub and pushes
all available packages to separate itch.io channels.
