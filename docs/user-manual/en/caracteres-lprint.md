# LPRINT characters

LPRINT uses 95 printable ASCII characters, codes 32 through 126, including space. This is separate from the LCD character table.

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789
! " # $ % & ' ( ) * + , - . /
: ; < = > ? @
[ \ ] ^ _ `
{ | } ~
```

```text
 32–47  | !"#$%&'()*+,-./
 48–63  |0123456789:;<=>?
 64–79  |@ABCDEFGHIJKLMNO
 80–95  |PQRSTUVWXYZ[\]^_
 96–111 |`abcdefghijklmno
112–126 |pqrstuvwxyz{|}~
```

Use CHR$(34) for a quotation mark, CHR$(92) for a backslash and CHR$(124) for a vertical bar. Accents and extended LCD codes require GLYPH patterns on paper. End lines with LPRINT alone or without a final semicolon. Maximum text width is 72 columns.

![LPRINT paper font, codes 32 to 126.](../images/lprint-characters.png)
