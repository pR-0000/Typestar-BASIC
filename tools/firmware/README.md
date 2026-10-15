# Firmware construction

HD6301 sources are in `../../src/`. The current firmware is **0.4.88-dev**; its final stages are `build_llist.py` and `prepare_llist.py`.

These scripts form an **incremental build pipeline**. Each stage checks the previous CPU image and symbol map before modifying the relevant ROM regions. `build.py` is the initial stage, rather than an independent build of the latest version. Intermediate images, manifests and reports live in the ignored `build/` directory.

Run scripts from the repository root. The existing pipeline requires the A09 assembler, the original Canon firmware and locally generated intermediate reports. It retains paths to the adjacent ROMReader research workspace. A standalone, configurable build remains a separate publication task. This reorganization changes no firmware bytes.

Some shared modules retain a `validate_` prefix because assembly helpers were developed alongside verification code; they remain here when construction stages import them. Independent diagnostics and hardware probes are stored in the ignored `_local/development/` tree.

Archived intermediate releases may be supplied with `TYPESTAR_FIRMWARE_ARCHIVE` or the ignored `_local/build-inputs.ini` (`[inputs]`, `firmware_archive = /path/to/archive`). Output always remains in the project's generated `release/` folder.
