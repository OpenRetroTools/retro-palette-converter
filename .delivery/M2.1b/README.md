# M2.1b — GUI Batch Convert

This overlay adds a responsive **File → Batch Convert…** workflow.

## Apply

From the repository root:

```bash
unzip -o ~/Downloads/retro-palette-converter-M2.1b-gui-batch-overlay.zip -d .
chmod +x .delivery/M2.1b/APPLY.sh .delivery/M2.1b/VERIFY.sh
./.delivery/M2.1b/APPLY.sh
./.delivery/M2.1b/VERIFY.sh
```

## Manual smoke test

```bash
uv run retropal gui
```

Open **File → Batch Convert…**, choose distinct input and output directories, then run a dry run before a real conversion.
