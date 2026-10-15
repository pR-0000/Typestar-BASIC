# Typestar BASIC - User's manual

Pierre Raimbault & Chat GPT - English edition, 15 October 2026. Reference firmware: **0.4.88-dev**, Canon S-70 / Typestar 7.

This edition translates the complete French manual: installation, Studio, history, processor and firmware, beginner lessons, language reference, glossary and the four complete program listings. The original BASIC keywords and machine error messages stay unchanged. English example sources are supplied in **examples/** (names ending in **-en.bas**); the terminal pair is in **examples/terminal**.

Start with [capabilities](00-fiche-machine.md), [installation](02-installation-firmware.md) and [Studio](02-studio.md). Then try [your first instructions](03-premiers-pas.md). Later, consult [the quick reference](98-reference-rapide.md), [glossary](99-lexique.md) or [command index](index-commandes.md).

The paginated [English PDF](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.88-dev/typestar-basic-manuel-en.pdf) has its own clickable contents, bookmarks, source notes and calculated glossary/index page references. Edit the UTF-8 Markdown sources to revise it. Each paragraph occupies one source line.

## Illustrations and original documents

Studio captures are rendered with the interface set to English. LCD and paper scenes run the supplied English programs through the HD6301 core using explicitly selected, locally owned ROMs. Native diagrams are regenerated from editable drawing code with English labels. Original historical photographs, advertisements, chip labels and the Canon schematic retain their source inscriptions; English captions explain them.

The schematic restoration uses only cropping, RGB-channel selection, broad illumination correction and contrast. It creates no replacement wires or lettering. The original scan is preserved at `../images/schema-cpu-original.jpg`; the restoration and its two enlarged halves are shared between editions.

Printy's English decision illustration is saved as `images/illustration-decisions.png`. It was edited with the built-in image-generation tool. Prompt: "Translate this existing illustration for the English edition of the same vintage BASIC manual. Preserve the exact slim typewriter character Printy, pose, proportions, two-arrow wooden signpost, paths, ink linework, sepia cream and dark green palette and transparent background. Change only the lettering on the signs: replace upper 'OUI' with exact English word 'YES', and lower 'NON' with exact English word 'NO'. Keep the words bold, centred, completely inside the existing cream sign faces. Keep all other drawing elements unchanged. No additional text or symbols."

## Rebuilding

Use the same document-building Python environment as the French manual:

```text
python docs/user-manual/build_manual.py --config docs/user-manual/manuel-en.json --output output/pdf/typestar-basic-manuel-en.pdf
python docs/user-manual/validate_manual.py --config docs/user-manual/manuel-en.json
```

`manuel-en.json` defines reading order, image sizes, bibliography and examples. The selected-program chapter is generated from the supplied source files. Both editions share the renderer and fonts; output files and page maps remain separate. Canon ROM images are supplied by the user and are not copied into this manual.
