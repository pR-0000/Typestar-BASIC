# Glossary

This glossary explains terms used in the manual. Links lead to the relevant lessons. PDF page numbers are recalculated whenever the document is built, so they follow added text and illustrations. The alphabetical command and function index is at the back.

## Absolute reference and relative movement

An absolute position is measured from an origin; relative movement is measured from the current position. MOVE uses the first principle, HEAD and FEED the second. See [motors](08-papier-dessins.md#move).

## Argument or parameter

A value supplied to a statement or function to specify its work. In `SOUND 300,100`, 300 is modulation and 100 duration. See [SOUND](09-sons-serie-memoire.md#sound).

## Array

Numeric cells stored under one name. Arrays have one or two dimensions. See [DIM](04-nombres-variables.md#dim).

## ASCII

A code table associating numbers with ordinary letters, digits and signs. The paper font uses printable codes 32 to 126; LCD accents have other codes. See [LPRINT](08-papier-dessins.md#lprint).

## Assignment

Storing a value in a variable. In `A=A+1`, BASIC calculates A+1, then replaces A's value with the result. See [LET](04-nombres-variables.md#let).

## BASIC

A programming language designed for learning through simple instructions. Its name means "Beginner's All-purpose Symbolic Instruction Code". Typestar BASIC is adapted to this machine. See [first steps](03-premiers-pas.md).

## Baud

A unit of serial signalling rate. Here, one symbol carries one bit; a character requires data and framing bits. Characters per second are therefore fewer than baud. See [BAUD and SERCFG](09-sons-serie-memoire.md#baud).

## Binary

Writing numbers with 0 and 1. `%10101` is 21 in BASIC. Binary clearly shows on and off pixels in a row. See [binary and hexadecimal](04-nombres-variables.md#binaire-hexadecimal).

## Bit

Information with value 0 or 1. A five-bit mask controls five pixels. Eight bits form a byte. See [LCDCHAR](07-ecran-clavier.md#lcdchar).

## BREAK

An interruption requested by the user. MARGIN RELEASE performs this role. The program stops and its message waits for Return. See [errors](10-erreurs-et-limites.md#erreurs).

## Byte

A group of eight bits, representing values 0 to 255. BASIC measures free memory in bytes. See [MEM](03-premiers-pas.md#mem).

## Character

A visible letter, digit, sign or pattern. A code selects a character, whose drawing may differ between LCD and paper fonts. See [ASC and CHR$](06-fonctions-nombres-chaines.md#chr).

## Clip

A plastic catch holding a case without screws. A little pressure in the correct direction releases it. See [opening the case](02-installation-firmware.md#installation).

## Comment

An explanation in a program for its reader. REM makes BASIC ignore the rest of the line. See [REM](05-decisions-boucles.md#rem).

## Comparison

A question comparing values: equal, different, smaller or larger. Its numeric result is -1 for true and 0 for false. See [comparisons](05-decisions-boucles.md#comparaisons).

## Concatenation

Joining strings with `+`. `"TYPE"+"STAR"` gives TYPESTAR. See [STR$ and VAL](06-fonctions-nombres-chaines.md#str).

## Condition

An expression used to choose an action. Zero means false; non-zero means true. See [IF, THEN and ELSE](05-decisions-boucles.md#if).

## Console

Keyboard dialogue at the `>` prompt. Enter immediate commands or numbered program lines there. See [getting started](03-premiers-pas.md).

## Constant

A value written directly in a program, such as 12, PI or "HELLO". A variable's contents can change instead. See [values](04-nombres-variables.md).

## Coordinates

Numbers describing a position. Text, graphics and motors each have their own units. See [paper references](08-papier-dessins.md#repere-graphique).

## Cursor

A marker showing where the next input or output goes. See [CURSOR](07-ecran-clavier.md#cursor).

## Debugger

A tool for observing memory and processor activity during execution. Studio shows registers, flags and disassembled instructions alongside bytes. See [Studio's debugger](02-studio.md#debogueur).

## Decimal

A number using a point for its fractional part, such as 2.5. Results have limited precision. See [numbers](04-nombres-variables.md).

## Deferred composition

Preparing several shapes in one reference before printing them together. See [DRAW](08-papier-dessins.md#draw).

## DIP

An IC package with two rows of pins. A 28-pin DIP has fourteen per side. Compatibility also requires matching pin functions and electrical levels. See [choosing a ROM](02-installation-firmware.md#installation).

## Editor

The workspace for writing and modifying program text. Studio colours words by role and checks machine limits. See [Studio's editor](02-studio.md#editeur).

## Emulator

Software reproducing a machine's operation. Studio runs selected ROMs through an HD6301 processor and simulated LCD, keyboard, paper and buzzer. See [the virtual Typestar](02-studio.md#emulateur).

## EPROM

Programmable memory retaining content without power. Windowed EPROMs are reused after ultraviolet erasure; the W27C512 suggested here is electrically erased in a programmer. See [ROM preparation](02-installation-firmware.md#installation).

## Expression

Values, functions and operators producing a result. In `P*N+2`, BASIC multiplies, then adds. See [precedence](04-nombres-variables.md#priorites).

## Firmware

The machine's internal program. Typestar BASIC replaces external-ROM firmware and reuses internal Canon services. See [HD6301](02-hd6301.md) and [installation](02-installation-firmware.md#installation).

## Function

A BASIC tool supplying a value for an expression. `SQR(9)` gives 3; PRINT can display it. See [functions](06-fonctions-nombres-chaines.md).

## Glyph

A small character or sprite drawing, described by pixel rows. See [GLYPH](08-papier-dessins.md#glyph).

## Hexadecimal

Base-sixteen notation using 0 to 9 and A to F. `&H1F` is 31. See [binary and hexadecimal](04-nombres-variables.md#binaire-hexadecimal).

## Index

An array cell's number. Indices start at zero and DIM's upper bound is included. See [DIM](04-nombres-variables.md#dim).

## LCD

Liquid Crystal Display, such as the Typestar's single line. Our display has 32 character cells. See [display and keyboard](07-ecran-clavier.md).

## Line spacing

Distance between successive text lines on paper. See [LSPACING](08-papier-dessins.md#lspacing).

## Listing

A readable program copy with line numbers. LIST shows it on the LCD; [LLIST](08-papier-dessins.md#llist) prints it.

## Loop

A repeated program section. FOR/NEXT prepares counted repetition; IF/GOTO can repeat until a condition changes. See [FOR and NEXT](05-decisions-boucles.md#for).

## Mask

A number whose bits control several elements: pixels, segments or indicators. A 1 bit lights its element. See [LCDLINE](07-ecran-clavier.md#lcdline).

## Matrix

A two-dimensional array like a board. Two indices select each cell. See [DIM](04-nombres-variables.md#dim).

## Microcontroller

A component combining a processor, memory and hardware communication circuits. The S-70's HD6301 executes firmware instructions. See [HD6301](02-hd6301.md).

## Modulation

A variation applied to the buzzer. SOUND modulates its gate rather than directly selecting volume or carrier frequency. See [SOUND](09-sons-serie-memoire.md#sound).

## Notch

A small recess at one end of a DIP chip, locating the pin 1 end. In IC8, it faces left when the keyboard is towards you. See [ROM orientation](02-installation-firmware.md#installation).

## Operator and operand

An operator names an operation; operands are the values it combines. In `A+3`, `+` is the operator, A and 3 the operands. See [precedence](04-nombres-variables.md#priorites).

## Origin

A point chosen as a coordinate reference. ORIGIN declares the present position; position paper at your chosen point first. See [ORIGIN](08-papier-dessins.md#origin).

## Parity

A check bit added to a serial character. Computer and machine must use matching settings. See [SERCFG](09-sons-serie-memoire.md#sercfg).

## Pin

A metal leg connecting an IC to its socket. Pin 1 locates orientation; fit it on the side specified by socket and guide. See [ROM replacement](02-installation-firmware.md#installation).

## Pixel

A small visible element of a drawing. LCD and print head have their own dot sizes. See [LCDCHAR](07-ecran-clavier.md#lcdchar) and [GLYPH](08-papier-dessins.md#glyph).

## Program

Instructions stored under line numbers and executed with RUN. See [RUN and LIST](03-premiers-pas.md#run).

## Programmer

A device that writes a file to memory, then reads it back for verification. Select the exact chip reference. See [installation](02-installation-firmware.md#installation).

## Prompt

A message asking for something. The console prompt is `>`; INPUT can display its own question. See [INPUT](05-decisions-boucles.md#input).

## RAM

Memory holding your program and working data. It can lose contents when its power is interrupted. See [MEM and FRE](03-premiers-pas.md#mem).

## ROM

Memory holding firmware. It retains contents without machine power; programming requires equipment suitable for the chip. See [HD6301](02-hd6301.md).

## Scalar

A simple variable holding one value, such as A or A$. Arrays hold several cells. INPUT requests a simple variable whose value can then be copied into an array. See [INPUT](05-decisions-boucles.md#input).

## Seed

A pseudorandom sequence's starting value. The same seed reproduces the same sequence. See [RND and RANDOMIZE](06-fonctions-nombres-chaines.md#rnd).

## Serial

A connection transmitting bits one after another. Our cable has both transmit and receive directions. See [SEROPEN and SERIN](09-sons-serie-memoire.md#seropen).

## Socket

A board-mounted connector allowing a chip to be removed and replaced without soldering. IC8 is socketed. See [BASIC installation](02-installation-firmware.md#installation).

## Statement

An instruction to BASIC, such as PRINT, INPUT or MOVE. Several may share a line, separated by `:`. See [getting started](03-premiers-pas.md).

## String

A sequence of characters treated as text. String constants use quotation marks; string variables end in `$`, such as A$. See [text functions](06-fonctions-nombres-chaines.md#len).

## Subroutine

A task called with GOSUB and returning with RETURN. See [GOSUB](05-decisions-boucles.md#gosub).

## Syntax

Rules for writing statements: word order, signs and parameters. Syntax mistakes keep BASIC from recognising a request. See [errors](10-erreurs-et-limites.md#erreurs).

## Tokenisation

Internally replacing some keywords with short codes to save memory. You still type and read ordinary words. See [memory](03-premiers-pas.md#mem).

## Variable

A name associated with a value that the program can change. A holds a number; A$ a string; A(0) is an array cell. See [LET and DIM](04-nombres-variables.md#let).
