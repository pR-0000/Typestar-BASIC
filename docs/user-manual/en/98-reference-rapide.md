# Language quick reference

Use this section to find statement forms after the workshops. Lowercase names such as x or variable stand for your values. Square brackets mark optional elements; type the chosen form directly. Commas, semicolons and parentheses are part of the syntax. The following glossary explains technical terms; the final index gives lesson pages.

## Programs and data

| Form | Purpose |
|---|---|
| `RUN` | Start the program, resetting working data. |
| `LIST [start[,end]]` | No argument: all; one number: that line; two: inclusive range. |
| `LLIST [start[,end]]` | Print all, one line or an inclusive range; direct command. |
| `NEW` | Clear program and working data. |
| `CLEAR` | Release working data, retain the program. |
| `MEM` | Display free bytes. |
| `LOAD` ; `SAVE` | Console only: receive a program from the computer or send it. |
| `[LET] variable=expression` | Assign a variable or numeric array cell. |
| `INPUT ["prompt";]variable` | Within RUN: read a numeric scalar or string. |
| `DIM A(last)` | Declare a 1D array, indices zero through last inclusive. |
| `DIM A(row,column)` | Declare a 2D numeric array, inclusive bounds. |
| `DATA value[,value...]` | Prepare numeric constants or quoted strings. |
| `READ destination[,destination...]` | Read DATA into scalars or numeric array cells. |
| `RESTORE` | Return to the first DATA. |
| `REM comment` | Ignore the rest of the line. |

## Execution control

| Form | Purpose |
|---|---|
| `GOTO line` | Go to an existing line. |
| `GOSUB line` ; `RETURN` | Call a subroutine and return. |
| `IF condition THEN branch [ELSE branch]` | Select a branch on the same line; branch is a number or statement(s). |
| `FOR A=start TO end [STEP step]` | Prepare a loop, non-zero step; default 1. |
| `NEXT [A]` | Repeat or finish the innermost loop. |
| `END` | End the program. |

Separate statements with `:`; the whole line remains limited to 63 native characters including number. Line numbers range from 1 to 65535. Variables are A..Z or A$..Z$; arrays are numeric. Comparisons give -1 for true and 0 for false.

## Display and keyboard

| Form | Purpose |
|---|---|
| `PRINT [value...]` | LCD; `;` joins, `,` adds a space, final `;` continues the line. |
| `CLS` | Clear text, composed triangles and LCDLINE lines. |
| `LOCATE 1,column` | Output at column 1 to 32. |
| `CURSOR mode` | Mode 0..4; default 0, disabled 4. |
| `LCDCHAR p,r1,r2,r3,r4,r5,r6,r7,t` | Position 1..32; seven rows and triangle, masks 0..31. |
| `LCDTRI p,mask` | Triangle on a space or custom character; mask 0..31. |
| `LCDLINE p,mask` | Independent five-pixel line; mask 0..31. |
| `ICON index,code` | Raw cell 0..31, code 0..255. |
| `KEYS` | Diagnose physical keyboard codes. |

Eight pattern slots are shared. Cursor 0 uses a native block, leaving them available. INKEY returns translated codes, which may differ from KEYS physical codes.

## Paper

| Form | Purpose |
|---|---|
| `LLIST [start[,end]]` | Print the whole listing, one line or an inclusive range; console. |
| `LPRINT [value...]` | Paper, 72 columns, ASCII 32..126; separators as PRINT. |
| `LSPACING 1` ; `1.5` ; `2` | Shared LPRINT/LLOCATE spacing; default 1.5, origin redeclared. |
| `LLOCATE row,column` | Text grid 1..64 and 1..72. |
| `POINT x,y[,size]` | Square point, size 1..16; default 1. |
| `LINE x1,y1,x2,y2,thickness` | Line segment, thickness 1..16. |
| `BOX x1,y1,x2,y2,thickness,fill` | Rectangle, ordered corners; fill 0 or 1. |
| `CIRCLE x,y,radius,thickness,fill` | Circle or disc; positive integer radius, fill 0 or 1. |
| `DRAW INSTANT` | Print shapes immediately. |
| `DRAW DEFERRED` | Prepare up to 32 shapes together. |
| `DRAW PRINT` ; `DRAW CANCEL` | Print or discard composition, then return to INSTANT. |
| `GLYPH A(indices),width,height[,mode]` | 1D/2D bitmap; modes 1 native, 2 double X/Y, 3 double X. |
| `ORIGIN [x[,y]]` | Declare current position without moving. |
| `MOVE x,y` | Absolute motor position in the declared reference. |
| `HEAD dx` ; `FEED dy` | Relative head and paper movement. |

Graphics: integer X 0..247, Y 0..255; corrected proportions, native row `INT(Y/2)`. Motors: X 0..128, Y 0..448, different units. Redeclare motor origin after printing. GLYPH: height 1..16; width 1..16 for 1D masks, 1..31 for a 2D matrix. The 2D width matches the column count and starts at column zero.

## Sound, randomness, serial and memory

| Form | Purpose |
|---|---|
| `BEEP [duration]` | 0..2000 ms; default 100 ms. |
| `SOUND modulation,duration` | 60..750 Hz modulation, or 0 for silence; 0..2000 ms. |
| `RANDOMIZE seed` | Required integer seed 1..65535. |
| `BAUD rate` | 1200, 2400, 7812, 15625 or 31250. |
| `SERCFG format` | 7N1, 7N2, 7E1, 7E2, 7O1 or 7O2; unquoted. |
| `SEROPEN rate` | Open a session with the selected format. |
| `SEROUT code` | Send code 0..127. |
| `SERCLOSE` | Complete transmission and close the session. |
| `POKE address,value` | Write byte 0..255 at CPU address 0..65535. |

LOAD/SAVE, sessions and graphics printing share serial settings; default 31250/7E1. Graphics mode starts through CODE+P at the console; this is a console-only shortcut.

## Functions and constant

| Form | Returned value |
|---|---|
| `ABS(x)` ; `SGN(x)` | Absolute value; sign -1, 0 or 1. |
| `INT(x)` ; `FIX(x)` | Floor; truncation towards zero. |
| `SQR(x)` | Square root, x positive or zero. |
| `PI` | 3.1415927; no parentheses. |
| `SIN(x)` ; `COS(x)` ; `TAN(x)` | Trigonometry in radians, x -1000 to 1000. |
| `ATN(x)` | Arctangent, result in radians. |
| `LOG(x)` ; `EXP(x)` | Natural logarithm and exponential. |
| `RND(1)` | Pseudorandom 0..0.9999; only argument 1. |
| `FRE(0)` | Free bytes. |
| `INKEY(0)` | Available key code; 0 if none. |
| `SERIN(0)` | Available serial code 0..127; -1 if none. |
| `PEEK(address)` | Byte read at CPU address 0..65535. |
| `LEN(s)` ; `ASC(s)` | Length; first character's code, non-empty string for ASC. |
| `CHR$(n)` | One-byte string, code 0..255. |
| `STR$(x)` ; `VAL(s)` | Number as text; text constant converted to number. |
| `LEFT$(s,n)` ; `RIGHT$(s,n)` | Up to n characters from left or right. |
| `MID$(s,start[,n])` | Substring, first position 1; to end when n omitted. |

Use functions in expressions: `PRINT RND(1)` or `A=RND(1)`. Numbers have eight significant digits and at most seven decimal places; trigonometry, LOG and EXP are approximate. Supply integers directly where required.

## Operators and signs

| Sign or word | Role |
|---|---|
| `+` ; `-` ; `*` ; `/` ; `^` | Arithmetic; `+` also joins two strings. |
| `MOD` | Integer division remainder, dividend's sign. |
| `=` ; `<>` ; `<` ; `<=` ; `>` ; `>=` | Compare values of matching types. |
| `NOT` ; `AND` ; `OR` | 16-bit operations; both operands evaluated. |
| `%` ; `&H` | Binary and hexadecimal constant prefixes. |
| `:` | Statement separator outside quotes and REM. |
| `;` ; `,` | Output separators; commas also separate parameters. |
| `$` | Suffix for string variables and functions. |

Order: power; unary sign; multiplication/division; MOD; addition/subtraction; comparisons; NOT; AND; OR. Parentheses impose grouping. Bitwise and MOD operands are integers from -32768 to 65535; bitwise results are interpreted as signed.
