# Typestar BASIC at a glance

**An 8-bit computer with a keyboard, LCD and A4 printer**, built around the Hitachi **HD6301Y0P** inside the Canon Typestar 7 / S-70. The original processor really runs your programs: replacing ROM IC8 gives it BASIC while retaining the services in Canon's internal ROM.

> **32 display characters - 5,951 bytes free - a built-in printer.** Calculate, write a game, create your characters, then give them a place on paper!

| Resource | Typestar BASIC 0.4.93-dev on the S-70 |
|---|---|
| **Processor** | 8-bit HD6301Y0P; system clock approximately **1 MHz**, derived from a 4 MHz crystal. |
| **Memory** | **8 KB external RAM**; **5,951 bytes free when empty**, shared by the tokenised program and its data. **32 KB** BASIC ROM; original 16 KB internal Canon ROM retained. |
| **Programs and data** | One program; line numbers 1 to 65535, 63 native characters per line, multiple statements separated by `:`. Numeric and string variables; one- and two-dimensional numeric arrays. |
| **Calculations** | Decimal numbers with **eight significant digits**; random numbers, PI, square roots, trigonometry, logarithms, exponentials and logical operators. |
| **Display and keyboard** | **32 characters of 5 × 7 pixels**, eight custom patterns, triangles, lower pixel lines and indicators. Multilingual **44-key** keyboard, according to Canon's specification; INKEY reads keys. |
| **Printed text** | Canon **Courier 10**, 72 columns and 95 ASCII characters; LLIST, adjustable line spacing and LLOCATE positioning. Plain paper with a ribbon, or direct printing on thermal paper. |
| **Printed graphics** | Points, lines, rectangles, circles, outlines and filled shapes. Custom glyphs, large square pixels, 1–16 copies in continuous bands, print-head and paper movement. |
| **Sound** | BEEP and SOUND: pauses, beeps and effects produced by amplitude modulation of the buzzer; modulation from 60 to 750 Hz, duration up to 2000 ms. |
| **Computer connection** | USB cable adapted to the 5 V TTL port; LOAD/SAVE, transmission and reception. Up to **31,250 baud**; default **31250 / 7E1**. |
| **Typestar BASIC Studio** | Editor, transfers, glyph design, LCD, paper and sound emulation; monochrome image printing through CODE+P. |

## The original hardware beneath BASIC

These are the main specifications of the Typestar 7 running Canon's software. BASIC calculation and drawing speeds depend on the program and on mechanical movement. [C1]

| Feature | Canon specification |
|---|---|
| Printing | **32 × 26-dot** thermal head; advertised speed of 18 characters per second with the original software. |
| Paper | Maximum width **241 mm**; maximum printing width **203 mm**. An A4 sheet measures 210 × 297 mm. |
| Keyboard | 44 multilingual keys; 19.05 mm pitch, 4 mm travel. The 80-character buffer belongs to Canon's firmware. |
| Power | Four **D / R20** batteries, 6 V; optional Canon AD-6 adapter or rechargeable pack. |
| Size and weight | **315 × 277 × 55.5 mm**; approximately **2.7 kg**, including batteries and ribbon cassette. |

The physical head, the glyphs used by BASIC and the LCD cells are three distinct things.

The machine accepts BASIC through a programmed ROM in IC8. The cable and Studio make communication with a computer easier. BASIC startup and serial program loading at up to 31250 baud are also validated on an S-60 / Typestar 6 with PCB NG3-0672 / NH1-0159-065, after fitting its interface components: see [the tested revision in the Installation chapter](02-installation-firmware.md#s60-serial). The S-90 / Typestar 7-II requires a BASIC version adapted to its ROMs.

## An unusual processor for a personal computer

Most familiar microcomputers use a Z80, a 6502 or another well-known family. **Typestar BASIC lets you program a real HD6301**, more often found in embedded electronics. It joins a small group of personal machines using this Hitachi family.

The **Epson HX-20** uses two CMOS 6301 processors. [E1] The **Psion Organiser I** uses an HD6301X at 0.9216 MHz. [I1] The **Organiser II** uses an **HD6303XFP**: this relative reads its program from external ROM, whereas the Typestar's HD6301 contains internal ROM. The families share the core instruction set; variants mainly differ in their integrated memory and peripherals. [I2] Electronic chess computers also use HD6301 variants, including the V1.

## Some neighbours with LCD screens

These machines show what a single display line and a little memory could offer. **The table compares their resources and uses.** The memory column distinguishes total capacity from the advertised program area.

| Machine | Processor | LCD | Stated memory | Printing and programming |
|---|---|---|---|---|
| **Typestar BASIC / S-70** | Hitachi HD6301Y0P | 1 × 32 | 8 KB external; **5,951 bytes free** when empty | BASIC; built-in A4 text and graphics printer. |
| **Sharp PC-1251** | Sharp SC61860 | 1 × 24 | 4 KB RAM; **3,486 bytes** in the program/data area [S1] | BASIC; optional CE-125 printer and microcassette. |
| **Psion Organiser I** | Hitachi HD6301X | 1 × 16 | 2 KB RAM; 4 KB ROM and EPROM Datapak [I1] | Data and calculations; programming through suitable modules. |
| **VTech Laser 50** | Z80A [V3] | 1 × 16 | Advertised 2,192 bytes RAM; 16 KB expansion [V1] | BASIC, ten programs P0 to P9; optional cassette and printer. |

The PC-1251 also reserves RAM for fixed variables and a separate small area. The Laser 50 figure follows its brochure. Its processor belongs to the Z80 family; photographs of its circuit board show Toshiba T7812/T7813 components. [V2] [V3]

## Reading the BASIC figures

Here, 1 KB means **1,024 bytes**. The 5,951 free bytes are shared between your program and its data. Tokenisation shortens keywords: **MEM** measures actual RAM use, while the `.bas` file remains readable text on the computer.

Drawings use a logical window of **248 × 256 coordinates**, with quantised vertical positioning. Custom glyphs and motor commands extend your compositions across the sheet; the paper chapter explains their units.

SOUND modulates a buzzer with a fixed carrier frequency. Serial rates describe communication with the computer; calculations and motors have their own pace. RAM cartridge support is planned for a later version.

[C1]: https://site.xavier.edu/polt/typewriters/CanonTypestar7.pdf
[E1]: https://electrickery.hosting.philpem.me.uk/comp/hx20/doc/om7-11ABC.pdf
[I1]: https://www.jaapsch.net/psion/p1manorg.htm
[I2]: https://www.jaapsch.net/psion/tech02.htm
[S1]: https://lastin.dti.supsi.ch/VET/sys/SHARP/PC-1251/PC-1250-PC-1251-Service_Manual.pdf
[V1]: references.md
[V2]: https://oldvcr.blogspot.com/2021/03/those-mysterious-toshiba-t-chips-plus.html
[V3]: https://sites.google.com/site/jamesskingdom/Home/computers-exposed/vtech-computers
