# Shared PC tools

Studio imports these modules for BASIC encoding, tokenization, serial transfers, graphics and glyphs. Most users can perform these operations directly in **Typestar BASIC Studio**.

- `native_text.py`, `native_program.py`: native character encoding and current tokenized format.
- `transfer_basic.py`, `transfer_native_basic.py`, `transfer_messages.py`, `serial_rates.py`: communication and program transfers.
- `print_image.py`, `graphics_stream.py`, `graphics_packed.py`: monochrome image conversion and serial printing.
- `glyph_definition.py`, `bitmap_assets.py`, `pattern_codec.py`, `raster16.py`: glyph and bitmap preparation.
- `firmware/`: firmware assembly, linking and packaging stages.

Earlier token codecs remain here because the current codec imports their shared definitions. Keep this directory alongside `studio/`, `src/`, `docs/` and `examples/`.
