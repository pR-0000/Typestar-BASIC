# Firmware regression checks

These suites exercise the BASIC ROM and HD6301 core. Generated binaries, disassembly maps and reports belong in the ignored `build/` directory. Original Canon ROMs are supplied locally by the developer.

Run `run_release_audit.py` after the incremental firmware build. It runs ROM layout/data checks, BASIC, memory, serial and state suites, followed by waveform, glyph, tile-row and game checks. `tools/firmware/prepare_release_candidate.py` requires sixteen passing reports for the exact 0.4.100 CPU-image hash before packaging socket images.

`validate_buzzer_survey_v3.py` also provides the instruction-timing oracle used by the sound regressions. `validate_quest_*.py` drives actual tokenized game rules with controlled fixtures. The [audit notes](../../docs/firmware-test-0.4.100.md) describe coverage and physical-test boundaries.

Exploratory recording analyses and standalone sound-survey firmware are archived in the ignored local development tree. They are separate from the regression entry point.
