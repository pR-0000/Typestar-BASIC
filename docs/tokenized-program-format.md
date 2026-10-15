# Format des programmes Typestar BASIC

Référence : **0.4.88-dev**. Le codec partagé par Studio et les transferts est `tools/native_program.py`.

## Enregistrements en RAM

| Champ | Taille | Rôle |
|---|---|---|
| Longueur totale | 1 octet | En-tête inclus ; zéro termine le programme |
| Numéro de ligne | 2 octets | Entier 1–65535, poids fort en premier |
| Corps de ligne | Variable | Texte et mots-clés tokenisés |

Les lignes sont triées par numéro et suivies d'un seul octet zéro. L'arène occupe $20C0–$37FF : 5952 octets, dont **5951** disponibles pour les enregistrements. Les variables et allocations réduisent ensuite l'espace disponible.

Chaque ligne coûte trois octets d'en-tête. Les mots-clés du dictionnaire ci-dessous occupent un octet. Les autres instructions et fonctions gardent leur forme textuelle : toutes les fonctions du langage ne correspondent pas à un token dédié.

Les chaînes entre guillemets restent du texte natif, y compris leurs caractères accentués. Les commentaires REM conservent leur texte. Le format se restitue en source lisible par LIST et SAVE ; le PC conserve les fichiers BASIC en UTF-8.

## Dictionnaire courant

| Token | Mot-clé |
|---|---|
| $80 | `PRINT` |
| $81 | `LET` |
| $82 | `REM` |
| $83 | `RUN` |
| $84 | `LIST` |
| $85 | `NEW` |
| $86 | `GOTO` |
| $87 | `IF` |
| $88 | `THEN` |
| $89 | `END` |
| $8A | `LLIST` |
| $8B | `LOCATE` |
| $8C | `CLS` |
| $8D | `FOR` |
| $8E | `NEXT` |
| $8F | `TO` |
| $90 | `STEP` |
| $91 | `GOSUB` |
| $92 | `RETURN` |
| $93 | `INPUT` |
| $94 | `PEEK` |
| $95 | `POKE` |
| $96 | `ABS` |
| $97 | `SGN` |
| $98 | `MEM` |
| $99 | `SAVE` |
| $9A | `LOAD` |
| $9B | `BEEP` |
| $9C | `SOUND` |
| $9D | `KEYS` |
| $9E | `CURSOR` |
| $9F | `ICON` |
| $A0 | `LCDTRI` |
| $A1 | `LCDLINE` |
| $A2 | `INT` |
| $A3 | `DIM` |
| $A4 | `RND` |

Les identifiants sont persistants. Le code partagé conserve les codecs antérieurs comme dépendances internes ; les applications utilisent `native_program` pour le format courant.

## Python API

- `read_source(text)` lit les lignes numérotées.
- `pack(records)` produit les enregistrements tokenisés.
- `unpack(data)` vérifie puis restitue les lignes.
- `native_text.encode_source` et `decode_source` convertissent le texte natif et Unicode.

See the [English manual](user-manual/en/02-presentation-firmware.md) for an introduction to firmware memory and tokenization.
