# Typestar BASIC 0.4.93-dev

[Français](#français) · [English](#english)

## Français

Version du **19 octobre 2026**, accompagnée de **Studio 0.2.34**. Images prêtes pour IC8 sur Canon S-70 / Typestar 7 et sur la révision S-60 / Typestar 6 décrite dans le [guide matériel](../../docs/hardware/typestar-6-serial-upgrade.md).

| Ressource | Valeur |
|---|---:|
| Image ROM IC8 | 32 768 octets |
| ROM occupée / réserve explicite | 32 707 / 61 octets |
| Image miroir W27C512 | 65 536 octets, deux copies identiques |
| RAM BASIC libre à vide | 5 951 octets |
| Mots-clés tokenisés / entrées de commande | 37 / 54 |
| Programme | Lignes 1–65535, 63 caractères natifs par ligne, instructions séparées par `:` |

La RAM libre est partagée entre programme tokenisé, variables, tableaux et tampons temporaires. Le [manuel](../../docs/user-manual/README.md) et la [référence du langage](../../docs/user-manual/98-reference-rapide.md) donnent les commandes et leurs limites.

Depuis la 0.4.88 : correction du masque des glyphes, compensation des reculs papier, grands pixels carrés avec `GLYPH ... ,4`, répétition de 1 à 16 motifs en bande continue, compression de police sans perte et intégration des jeux papier validés. La table des tokens et le format du programme restent compatibles. Les 95 caractères papier décodés conservent leurs pixels.

Pour une suite de dix grands motifs : `GLYPH A(0),16,16,4,10`. Le pilote garde un seul fragment en mémoire ; ce format utilise 348 octets temporaires, pour une ou dix copies. BREAK reste disponible entre blocs. La précision mécanique dépend aussi de l'entraînement et du papier.

Les deux binaires utilisent l'ordre physique d'IC8. [SHA256SUMS.txt](SHA256SUMS.txt) couvre les images ; [release-info.json](release-info.json) contient leurs tailles, empreintes et statistiques. La maskROM Canon reste dans le MCU et est fournie séparément par l'utilisateur pour Studio.

## English

Release dated **19 October 2026**, accompanied by **Studio 0.2.34**. Ready-to-program IC8 images for Canon S-70 / Typestar 7 and the S-60 / Typestar 6 revision described in the [hardware guide](../../docs/hardware/typestar-6-serial-upgrade.md#english).

| Resource | Value |
|---|---:|
| IC8 ROM image | 32,768 bytes |
| Occupied ROM / explicit reserve | 32,707 / 61 bytes |
| W27C512 mirrored image | 65,536 bytes, two identical copies |
| Empty BASIC free RAM | 5,951 bytes |
| Tokenized keywords / command entries | 37 / 54 |
| Program | Lines 1–65535, 63 native characters per line, `:` between statements |

Free RAM is shared by the tokenized program, variables, arrays and temporary buffers. The [manual](../../docs/user-manual/en/README.md) and [language reference](../../docs/user-manual/en/98-reference-rapide.md) cover commands and limits.

Since 0.4.88: corrected glyph mask addressing, paper-reversal compensation, large square pixels with `GLYPH ... ,4`, 1–16 repeated motifs in continuous bands, lossless font compression and the validated paper games. The token table and program format remain compatible. All 95 decoded paper characters retain their pixels.

For ten large motifs: `GLYPH A(0),16,16,4,10`. The driver caches one fragment; this format uses 348 temporary bytes for either one or ten copies. BREAK remains available between blocks. Mechanical accuracy also depends on paper transport and the paper itself.

Both binaries use physical IC8 byte order. [SHA256SUMS.txt](SHA256SUMS.txt) covers the images; [release-info.json](release-info.json) records their sizes, hashes and statistics. Canon's maskROM stays in the MCU and is supplied separately by the user for Studio.
