# Choosing your characters

Studio's **Characters** palette gives access to all 256 LCD codes. Select a drawing, then **Insert expression at cursor**: Studio writes CHR$(code) in your program. Choose a symbol without finding it on the Canon keyboard.

**These two tables reproduce Studio's palette**, transcribed by observing the S-70 display. Choose a letter, border, symbol or piece of scenery.

<a id="ic5-lcd"></a>
## IC5: from character codes to pixels

When your program displays `PRINT "A"`, the processor sends **code 65** to the display. The circuit marked **IC5**, bearing the reference **MB62H177**, then handles drawing the letter on the LCD. The native font resides in the display circuit's character generator; the processor ROMs also hold patterns for some of Canon software's composed characters. [P1] [L2]

### A relationship with the HD44780 family

The observed commands and memory organisation resemble **Hitachi HD44780** controllers. The **HD44780U** data sheet's **Table 4, variant A02**, presents a European font containing letters, signs and accents, several of which resemble the Typestar's patterns. This document provides a comparison reference: IC5 bears the reference MB62H177, and our catalogue retains the shapes and codes observed on the Canon. [L1] [L2]

The resemblance helps explain how the display works. The Typestar has its own character choices and a strip of triangles and indicators adapted to a typewriter. For example, the observed catalogue starts its extended characters with **Ç at code 160** and has a **solid block at code 171**. The Canon table below remains the reference for your programs.

### Three memories with different jobs

| Display memory | What it holds | Example |
|---|---|---|
| **DDRAM**, display memory | Codes placed at screen positions. | Code 65 selects the letter A. |
| **CGROM**, fixed font | Permanent pictures of native letters and symbols. | The pixels of A or Ç. |
| **CGRAM**, custom-picture memory | Pixel rows that a program can change. | A character created with LCDCHAR. |

Tests confirm reading codes from DDRAM and patterns from CGRAM. **Reading a letter from display memory returns its code**, such as 65 for A. The identified accesses provide custom-picture pixels; fixed characters were recorded by displaying them and transcribing their pixels. That transcription supplies Studio's emulated LCD font. [L2]

### Why eight custom characters?

The model confirmed on the S-70 uses **64 bytes of CGRAM**, organised as **8 patterns of 8 rows**. Visible characters occupy five columns and seven rows; the eighth row contributes to the triangles beneath the letters. Codes **0 through 7** select these eight patterns, and **8 through 15** repeat them: changing a pattern changes all its occurrences and its alias. [L2]

Accents already present in the fixed font use their own codes and keep all eight custom slots available. BASIC's cursor also uses native solid block 171. You can therefore display several accents alongside your own pictures on the same screen.

### What the experiments established

CGRAM writes and subsequent reads preserve all eight bits of the tested bytes, while **the five least significant bits** produce visible dots. Writes **64 bytes** apart reached the same cells: this wraparound explains the retained capacity. These observations helped refine Studio. [L2]

The processor accesses LCD commands and status at hexadecimal address **&H0038**, and data at **&H0039**. The logical area for 32 characters and the lower strip have separate uses on the glass. BASIC provides PRINT, LCDCHAR, LCDTRI, LCDLINE and ICON to control them. [L2]

The HD44780U data sheet describes horizontal display shifting. On the studied IC5, research established memory and indicator accesses; a hardware vertical-scroll command remains unknown. BASIC's console updates its content by rewriting characters. [L1] [L2]

## LCD codes 0 to 127

![LCD characters 0 to 127, from Studio's palette, with decimal and hexadecimal codes.](../images/lcd-catalogue-00-7f.png)

**0 to 7** select eight custom patterns; **8 to 15** alias them. Their appearance depends on the program and is blank here. Positions **16 to 31** are blank on the studied display. Ordinary space is **code 32**.

## LCD codes 128 to 255

![LCD characters 128 to 255: accents, letters and native symbols on the studied display.](../images/lcd-catalogue-80-ff.png)

The range **128 to 159** appears blank on the S-70; extended characters begin at **160, Ç**. Solid block **171** serves as BASIC's cursor. Grid **172** and symbol **192** form Pocket Duel's terrain and mines. Choose patterns visible in the catalogue.

## Using a drawing from the table

```basic
10 CLS:CURSOR 4
20 PRINT CHR$(160);" ";CHR$(172);" ";CHR$(192)
```

This displays three native characters separated by spaces. **CHR$ belongs outside quotation marks**: `PRINT "CHR$(172)"` would simply display the text CHR$(172).

```basic
10 CLS:CURSOR 4
20 PRINT "GRID ";CHR$(172);"  MINE ";CHR$(192)
```

![Actual execution in Studio's HD6301 core: two native codes in a sentence.](images/lcd-symboles-natifs.png)

Common accents can also be entered directly into a Studio string, for example `PRINT "Accents: café, Noël"`. The tool converts supported characters to native codes. For symbols without a corresponding key, CHR$ remains the clearest approach. The table describes the reference S-70 display; another variant may contain different drawings.

## What about paper?

**PRINT and LPRINT have their own fonts.** LPRINT uses the 95 printable ASCII codes **32 to 126**, including space. To reproduce an LCD pattern such as grid 172 on paper, define it with GLYPH.

![The 95 LPRINT characters, decoded by the firmware in Studio. Numbers are decimal codes; 32 is space.](../images/lprint-characters.png)

```basic
10 LPRINT "Backslash: ";CHR$(92)
20 LPRINT "Vertical bar: ";CHR$(124)
```

Prepare GLYPH patterns for accents and additional signs. A full LPRINT character list and a program to print it are in the [LPRINT reference](caracteres-lprint.md). Custom drawings are explained in [the paper chapter](08-papier-dessins.md#glyph).

[P1]: https://ajd.sh/posts/canon-typestar-part-1/
[L1]: https://cdn-shop.adafruit.com/datasheets/HD44780.pdf#page=18
[L2]: references.md#lcd-ic5
