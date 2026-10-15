# 6 - A toolbox for numbers and text

A **statement** does something: PRINT displays, INPUT asks a question. A **function** provides a value that you can display, store or use in a calculation. Write `PRINT SQR(9)` or `A=SQR(9)` to use its result.

In the descriptions below, x stands for a number and s for a string. Replace them with constants, variables or expressions.

![Printy considers a calculation: a function supplies a value your program can reuse.](../images/illustration-calculs.png)

<a id="abs"></a>
<a id="sgn"></a>
## ABS and SGN: magnitude and sign

`ABS(x)` gives x's distance from zero, without its sign: `ABS(-8)` and `ABS(8)` both give 8. Two players at positions A and B are `ABS(A-B)` apart.

`SGN(x)` gives -1 for a negative number, 0 for zero and 1 for a positive number. It can indicate which direction leads towards a target.

```basic
10 A=4:B=9
20 PRINT "DISTANCE=";ABS(A-B)
```

The result is DISTANCE=5. Change A and B: the distance stays positive or zero.

<a id="int"></a>
<a id="fix"></a>
## INT and FIX: keeping an integer

`INT(x)` gives the greatest integer less than or equal to x. `FIX(x)` removes the part after the point, towards zero. They agree for positive numbers and differ for negative numbers.

| Expression | Result |
|---|---:|
| `INT(3.8)` | 3 |
| `FIX(3.8)` | 3 |
| `INT(-3.8)` | -4 |
| `FIX(-3.8)` | -3 |

Round a **positive** number to the nearest integer with `INT(x+0.5)`. INT alone rounds down. Coordinates and pixel masks expect exact integers: use INT or FIX when a calculation gives a decimal.

<a id="sqr"></a>
## SQR: finding a square's side

`SQR(x)` gives x's square root. Since 5*5 is 25, `SQR(25)` gives 5. The number must be positive or zero.

```basic
10 A=9:B=12
20 PRINT SQR(A*A+B*B)
```

The result is 15: the diagonal length of a rectangle with sides 9 and 12. Decimal roots use the available precision; `SQR(2)` gives a decimal number.

<a id="rnd"></a>
<a id="randomize"></a>
## RND and RANDOMIZE: making an unpredictable choice

`RND(1)` gives a number from 0 to 0.9999, in steps of 0.0001. To make a six-sided die:

```basic
PRINT INT(RND(1)*6)+1
```

Multiplication gives a value below 6, INT keeps an integer from 0 to 5, and adding 1 changes the range to 1 through 6. Replace 6 with N to choose among N possibilities numbered 1 to N.

The generator is **pseudorandom**: it follows a rule from a starting value called a seed. `RANDOMIZE 1234` selects that seed. It must be an integer from **1 to 65535**. The same seed repeats the same sequence, which helps compare experiments.

```basic
10 RANDOMIZE 1234
20 FOR I=1 TO 5
30 PRINT INT(RND(1)*6)+1:SOUND 0,500
40 NEXT I
```

This BASIC accepts only **1** as RND's argument. RANDOMIZE requires an explicit seed. To vary a game, its program can change a seed while waiting for the player's key. The timing of that key then helps select the game.

<a id="pi"></a>
<a id="sin"></a>
<a id="cos"></a>
<a id="tan"></a>
<a id="atn"></a>
## PI, SIN, COS, TAN and ATN: exploring angles

`PI` is the constant 3.1415927, written without parentheses. A complete circle is 2*PI **radians**. Trigonometric functions use radians, while school angles are often measured in degrees. Multiply degrees by PI/180 to convert them.

```basic
10 A=30*PI/180
20 PRINT SIN(A)
```

The result is close to 0.5. `SIN` gives the sine, `COS` the cosine and `TAN` the tangent. `ATN` reverses the tangent: it gives an angle in radians from a ratio. `ATN(1)` is close to PI/4, or 45 degrees.

These tools calculate trajectories or points on circles. CIRCLE prepares a circle directly from its centre and radius.

SIN, COS and TAN accept arguments between **-1000 and 1000 radians**. TAN is rejected when the calculated cosine is too close to zero. Results are approximate and calculations take longer than additions. Test with a small tolerance, such as `ABS(A-B)<0.001`, rather than exact equality.

<a id="log"></a>
<a id="exp"></a>
## LOG and EXP: tools for going further

`LOG(x)` gives x's natural logarithm; x must be strictly positive. `EXP(x)` gives the exponential. The functions complement each other: `EXP(LOG(2))` is close to 2.

They help with growth calculations and some powers. For a first encounter, try:

```basic
PRINT LOG(1)
PRINT EXP(0)
```

The results are 0, then 1. EXP rejects arguments above 18; below -18, it returns zero at the chosen precision. Like trigonometry, these calculations are approximate and relatively slow.

<a id="len"></a>
<a id="left"></a>
<a id="right"></a>
<a id="mid"></a>
## LEN, LEFT$, RIGHT$ and MID$: cutting up words

`LEN(s)` counts a string's bytes. In a string converted for the machine, each recognised character counts as one. `LEN("CATS")` gives 4 and `LEN("")` gives 0.

`LEFT$(s,n)` takes up to n characters from the left; `RIGHT$(s,n)` does the same from the right. `MID$(s,start,n)` takes a piece from a specified position. In a string, **the first position is 1**; array indices begin at zero.

```basic
10 A$="TYPESTAR"
20 PRINT LEFT$(A$,4)
30 SOUND 0,1000
40 PRINT RIGHT$(A$,4)
50 SOUND 0,1000
60 PRINT MID$(A$,3,3)
```

You read TYPE, then STAR, then PES. If n exceeds the remaining text, BASIC takes only what is available. Zero length gives an empty string. MID$ starts at position 1 or above. With no third parameter, `MID$(A$,5)` takes everything from the fifth position, here STAR.

**Your turn.** Replace TYPESTAR with another word and predict the three results before running.

<a id="asc"></a>
<a id="chr"></a>
## ASC and CHR$: characters and their codes

`ASC(s)` gives the first character's code. Supply a string containing at least one character. `CHR$(n)` makes a one-byte string with code n, from 0 to 255.

```basic
PRINT ASC("A")
PRINT CHR$(65)
```

The results are 65, then A. Extended codes belong to the Canon LCD table. `CHR$(171)` produces the native black block, useful for a cursor or obstacle. Pocket Duel uses codes 172 and 192 for terrain and mines.

To display quotation marks in a sentence:

```basic
PRINT "IT SAYS ";CHR$(34);"HELLO";CHR$(34)
```

Inside an LCD string, codes such as 10 and 13 also select glyphs: they represent controller characters. Use PRINT alone or without a final semicolon to finish an output line. Select codes from the LCD catalogue or LPRINT table according to the destination.

<a id="str"></a>
<a id="val"></a>
## STR$ and VAL: linking numbers and text

`STR$(x)` writes a number as text. VAL reads a complete constant: `VAL("12.5")` gives 12.5 and `VAL("&H1F")` gives 31. INPUT also accepts expressions. This example displays PRICE=12.5:

```basic
10 A=12.5:B$="PRICE="+STR$(A)
20 PRINT B$
```
