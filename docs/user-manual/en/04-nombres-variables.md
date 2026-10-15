# 4 - Numbers, words and little boxes

A variable is like a box with a label. Put a value inside, then use the label to find it again. BASIC recognises numeric variables **A to Z** and text variables **A$ to Z$**. The `$` sign tells us that the box contains text.

![A variable: a box named A receives the value 5.](../images/illustration-variables.png)

<a id="let"></a>
## Giving a value: LET

```basic
A=5
PRINT A
```

The display shows 5. `A=5` is an **assignment**: it puts 5 into A. You may write `LET A=5`; `LET` is optional. To replace the value, simply write `A=8`.

```basic
10 A=5
20 A=A+1
30 PRINT A
```

Line 20 takes A's old value, adds 1, then stores the result in A. The program displays 6. Here, `=` means "receives the value of".

A numeric variable starts at zero. A text variable starts with empty text, written `""`. **Names are one letter long**: use P for price, N for number and T for total. Add a REM comment to explain each letter's purpose.

## Calculating with decimal numbers

Use a **point** in a decimal number: `2.5`. Commas separate parameters in certain commands.

| Sign | Operation | Example | Result |
|---|---|---|---:|
| `+` | Addition | `8+3` | 11 |
| `-` | Subtraction | `8-3` | 5 |
| `*` | Multiplication | `8*3` | 24 |
| `/` | Division | `8/4` | 2 |
| `^` | Power | `2^3` | 8 |

Here is a little budget:

```basic
10 P=2.5
20 N=4
30 T=P*N
40 PRINT "TOTAL=";T
```

Four items at 2.50 cost 10. The semicolon joins the message and number. **Your turn.** Change P and N, then run the program again.

Calculations provide **eight significant digits**, with at most seven digits after the point. This precision counts useful digits on both sides of the point. Some results are rounded: consider acceptable differences in long calculations.

Division by zero or an excessively large result causes an error. Enter numbers using digits and an optional point, such as `125.5`.

<a id="priorites"></a>
## In what order are calculations performed?

```basic
PRINT 2+3*4
```

The result is 14: BASIC multiplies before adding. To obtain 20, make the addition happen first:

```basic
PRINT (2+3)*4
```

**Parentheses** group operations. As an expression becomes harder to read, they are often more helpful than a shortcut.

From highest to lowest precedence, BASIC processes: power `^`; numeric signs `+` and `-`; `*` and `/`; `MOD`; `+` and `-`; comparisons; `NOT`; `AND`; `OR`. Powers associate to the right: `2^3^2` means `2^(3^2)`, giving 512. A minus sign follows exponentiation: `-2^2` gives -4; `(-2)^2` gives 4.

A negative base requires an integer exponent. `2^-3` gives 0.125. By this BASIC's convention, `0^0` gives 1; zero raised to a negative power is rejected.

<a id="binaire-hexadecimal"></a>
## Counting in binary and hexadecimal

Ordinary numbers use ten digits, 0 to 9. **Binary** uses two, 0 and 1. Put `%` before a binary number:

```basic
PRINT %10101
```

You obtain 21. From right to left, the positions are worth 1, 2, 4, 8 and 16. In 10101, positions 16, 4 and 1 are present: 16+4+1=21. Leading zeros can align patterns without changing the value.

Binary is handy for drawing pixels: 1 means on, 0 means off. **Hexadecimal** groups values in sixteens and also uses A, B, C, D, E and F. Its prefix is `&H`:

```basic
PRINT &H1F
```

The result is 31. `%11111`, `&H1F` and `31` denote the same value. Always use `&H` for hexadecimal.

## Text in variables

```basic
10 A$="HELLO"
20 B$=A$+" !"
30 PRINT B$
```

The `+` sign joins two strings: this is **concatenation**. Here the result is HELLO !. Quotation marks delimit the string's text.

Each string or string-expression result holds **at most 63 bytes**. Computer files use UTF-8; **Typestar BASIC Studio** converts recognised accents inside quotation marks into the machine's characters. Each then occupies one byte in BASIC memory. LCD accents and paper-font characters are different sets.

Keywords, variable names and `REM` comments use ASCII characters. `CHR$` inserts a character by number. For example, `CHR$(34)` produces a quotation mark; use it to include quotation marks inside displayed text.

<a id="dim"></a>
## Several boxes under one name: DIM

An **array** is a row of numbered boxes. You could store five marks under five different letters. An array keeps them together:

```basic
10 DIM N(4)
20 N(0)=12:N(1)=15:N(2)=9
30 N(3)=18:N(4)=11
40 PRINT N(3)
```

The result is 18. `DIM N(4)` creates **five** cells: N(0), N(1), N(2), N(3) and N(4). The number is the last allowed index, rather than the number of cells. All cells start at zero.

A two-dimensional array resembles a board. `DIM M(2,3)` creates three rows and four columns, twelve cells altogether. This manual uses `M(row,column)` for drawings, with the first row and column numbered zero.

```basic
10 DIM M(2,3)
20 M(1,2)=7
30 PRINT M(1,2)
```

The result is 7. A variable A, a string A$ and an array A(...) are separate. Declare **one array per statement**: `DIM A(9):DIM B(2,3)` works; each DIM describes its own one- or two-dimensional numeric array.

## Leaving room for the program

An array occupies memory as soon as it is declared. Each numeric cell uses five bytes, plus nine management bytes for the whole array. `DIM A(9)` therefore uses 9+10*5, or 59 bytes. A numeric variable uses six bytes. A string variable reserves 73 bytes at its first non-empty assignment; the reserve remains allocated after assigning `""`. `CLEAR`, `RUN` and `NEW` reset allocations according to their roles.

Try this at the prompt to see an array's effect:

```basic
CLEAR
PRINT FRE(0)
DIM A(9)
PRINT FRE(0)
```

The second free-memory figure should be 59 bytes smaller. Motors, drawings and printing also use temporary workspace. A program that nearly fills RAM may load successfully, then run short of space for arrays or printing. Leave a reserve appropriate to its work.
