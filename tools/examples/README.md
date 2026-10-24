# Example authoring and verification

The playable BASIC files are in [examples](../../examples/README.md). These helpers maintain their compact artwork, source code and illustrations.

- `build_s70_quest.py` generates the French and English Quest files from `s70-quest-assets.json` and the LCD sprite catalogue.
- `update_paper_games.py` contains the shared native-byte encoding and Ruins direction selector, along with the paper-row conversion helpers.
- `build_byte_font.py` generates Studio’s hexadecimal DATA-byte badge font.
- `render_s70_quest.py` and `export_s70_quest_sprites.py` prepare guide images and editable sprite examples.
- `validate_*.py` checks native encoding, ROM execution, game startup, printed rows and movement. Tests use developer-supplied Canon ROMs; controlled fixtures are described in each script.

Generated reports and intermediate files remain in the ignored `build/` directory. The firmware build pipeline is documented in [tools/firmware](../firmware/README.md).
