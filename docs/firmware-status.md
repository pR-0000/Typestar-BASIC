# Typestar BASIC 0.4.88-dev

| Ressource / Resource | Valeur / Value |
|---|---|
| ROM IC8 | 32 768 octets / bytes |
| RAM BASIC libre à vide / Free BASIC RAM at startup | 5 951 octets / bytes |
| Réserve ROM explicite / Explicit ROM reserve | 102 octets fragmentés / fragmented bytes |
| Police papier / Paper font | Courier 10, 95 glyphes ASCII / ASCII glyphs |
| Numéros de ligne / Line numbers | 1–65535 |
| Longueur de saisie / Input line length | 63 octets / bytes |
| Série par défaut / Default serial settings | 31250 bauds / baud, 7E1 |

La réserve ROM est répartie entre plusieurs plages. La RAM disponible est partagée par le programme tokenisé, les variables, les tableaux et les allocations temporaires.

ROM reserve is distributed across several regions. Available RAM is shared by the tokenized program, variables, arrays and temporary allocations.

Les commandes, fonctions et limites sont décrites dans le [manuel français](user-manual/README.md) et le [manuel anglais](user-manual/en/README.md).
