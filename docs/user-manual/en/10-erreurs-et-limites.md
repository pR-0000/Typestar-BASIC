# 10 - Finding errors and improving your program

Errors are part of learning. The machine indicates where it expects a correction; your task is to understand the requested instruction. Keep a copy before changing several lines at once.

<a id="erreurs"></a>
![Printy investigates: reviewing an instruction helps locate an error.](../images/printy-debug.png)

## The line number is your first landmark

If the LCD shows `?SYNTAX @120`, start with `LIST 120`. Are quotation marks closed? Is a comma missing between parameters? Is the variable name one letter? After reading the message, Return restores the console.

The number identifies where the error was **detected**. Its cause may be earlier: a RETURN without GOSUB can result from a jump into the wrong place.

| Message or message family | What to check |
|---|---|
| `?SYNTAX` | Punctuation, parentheses, command name and statement form. |
| `?RANGE` | Out-of-range parameter, or decimal where an integer is required. |
| `?MODE` | Select the mode suitable for this command. |
| `?UNDEFINED LINE` | Missing GOTO, GOSUB or IF destination. |
| `?LINE TOO LONG` | BASIC line exceeds input capacity. |
| `?PROGRAM FULL`, `?PROGRAM RAM`, `?ARRAY RAM` | Insufficient memory or retained-program problem. |
| `?REDIM` | Array already declared; review DIM and initialisation. |
| `?DECIMAL MATH` | Division by zero, function domain or unrepresentable result. |
| `?EXPR DEPTH` | Expression nested too deeply; split the calculation. |
| `?FOR/NEXT`, `?FOR DEPTH`, `?FOR VARIABLE` | Mismatched loops, excessive nesting or reused counter. |
| `?GOSUB/RETURN`, `?GOSUB DEPTH` | RETURN without matching call, or excessive nesting. |
| `?LCD CHAR` | Triangle requested on a native letter rather than a space or custom pattern. |
| `?LCD SLOTS` | All eight custom-pattern slots still have references. |
| `?DRAW PENDING` | Pending composition: print or cancel before switching modes. |
| `?DRAW`, `?MOTOR` | Review composition, reference, workspace and parameters. |
| `?TX TIMEOUT`, `?RX...`, `?SERIAL`, `?BAD ACK` | Port, cable, serial settings, session and computer protocol. |
| `?BREAK` | Interruption requested by the player or program. |

These are the most useful messages. A difficulty may be detected at several stages; detailed RX variants describe serial reception state.

## A method in four small experiments

First predict a simple case: two items at 3 should total 6. Run it and compare. If the result differs, display intermediate values with PRINT. Finally change just one line and repeat the same experiment.

Use LPRINT to keep several traces without losing a value on the LCD. For long calculations, check one loop iteration first. For a drawing, print the outline before adding other shapes.

Exact equality between calculated decimals may be too demanding, especially after SIN, COS, LOG or EXP. To test whether a shot is near its target, compare distance with a tolerance: `IF ABS(A-B)<1 THEN ...`. The suitable tolerance depends on the game's units.

<a id="limites"></a>
## Limits to keep beside the keyboard

| Item | Capacity or rule |
|---|---|
| Program | One in RAM; memory shared with variables. |
| Free RAM when empty | 5,951 bytes. |
| Line numbers | 1 to 65535. |
| Source line | 63 native characters, including number and spaces. |
| Variables | A..Z and A$..Z$; one-letter names. |
| String or string result | 63 bytes. |
| Arrays | Numeric, one or two dimensions, zero-based indices. |
| Numbers | 8 significant digits, at most 7 decimal places. |
| FOR and GOSUB | 8 active levels each. |
| Display | 1 physical line of 32 characters; 8-line history. |
| LCD patterns | 8 shared slots. |
| Paper text | 72 columns; LLOCATE over 64 rows. |
| Drawing composition | 32 shapes. |
| Graphics reference | X 0..247; Y 0..255; integers. |
| BASIC serial session | 7 bits, codes 0..127; no long software reception queue. |

A source line accepts multiple statements separated by `:` in one record. Inside quotes, the colon is text. Tokenisation shortens storage **in memory**; entry remains limited to **63 native characters per line**.

## Adapting a program from another manual

Typestar BASIC draws on classic BASICs and has its own syntax. Check variable names, DIM forms, drawing units and keyboard functions before adapting a listing.

Build loops with **FOR/NEXT or IF/GOTO**, choices with **single-line IF/THEN/ELSE**, and input with **INPUT into a simple variable**. RESTORE returns to the first DATA. Programs and data share RAM. WHILE/WEND, REPEAT/UNTIL, IF/ENDIF, ON…GOTO and STOP/CONT, as well as RENUM, range DELETE, string arrays, INKEY$ and files, require adaptation using these tools. RAM cartridge support is planned for later.
