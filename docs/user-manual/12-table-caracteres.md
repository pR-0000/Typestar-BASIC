# Choisir ses caractères

La palette **Caractères** de Studio donne accès aux 256 codes du LCD. Sélectionnez un dessin puis utilisez **Insérer l’expression au curseur** : Studio écrit CHR$(code) dans votre programme. Vous pouvez ainsi choisir un symbole sans le chercher sur le clavier de la Canon.

**Les deux tables suivantes reprennent les dessins de la palette Studio**, transcrits par observation de l’écran de la S-70. Elles permettent de choisir une lettre, un cadre, un symbole ou une petite pièce de décor.

## Codes LCD 0 à 127

![Caractères LCD de 0 à 127 : représentation de la palette Studio, avec codes décimaux et hexadécimaux.](images/lcd-catalogue-00-7f.png)

**0 à 7** désignent les huit motifs personnalisés ; **8 à 15** sont leurs alias. Leur dessin dépend de ce que le programme a défini. Ils apparaissent vides ici. Les positions **16 à 31** sont vides sur l'écran étudié. L'espace habituel est le **code 32**.

## Codes LCD 128 à 255

![Caractères LCD de 128 à 255 : accents, lettres et symboles natifs de l'écran étudié.](images/lcd-catalogue-80-ff.png)

La plage **128 à 159** apparaît vide sur la S-70 ; les caractères étendus commencent à **160, Ç**. Le rectangle plein **171** sert au curseur BASIC. La grille **172** et le symbole **192** composent le terrain et les mines de Pocket Duel. Choisissez les motifs visibles dans le catalogue.

## Utiliser un dessin de la table

```basic
10 CLS:CURSOR 4
20 PRINT CHR$(160);" ";CHR$(172);" ";CHR$(192)
```

Le programme affiche trois caractères natifs séparés par des espaces. **CHR$ se place hors des guillemets** : `PRINT "CHR$(172)"` écrirait simplement le texte CHR$(172).

```basic
10 CLS:CURSOR 4
20 PRINT "GRILLE ";CHR$(172);"  MINE ";CHR$(192)
```

![Affichage réel du programme dans le cœur HD6301 de Studio : deux codes natifs dans une phrase.](images/lcd-symboles-natifs.png)

Les accents courants peuvent aussi être écrits directement dans une chaîne de Studio, par exemple `PRINT "Flèches, café, Noël"`. L'outil convertit les caractères pris en charge vers leurs codes natifs. Pour un symbole ou un caractère sans touche correspondante, CHR$ reste la méthode la plus claire. Le tableau décrit l'écran S-70 de référence : une autre variante de machine peut posséder des dessins différents.

## Et sur le papier ?

**PRINT et LPRINT possèdent leurs propres polices.** LPRINT utilise les 95 caractères ASCII imprimables, de **32 à 126**, espace compris. Pour reproduire sur papier un motif LCD, comme la grille 172, définissez son dessin avec GLYPH.

![Les 95 caractères de LPRINT, décodés par le firmware dans Studio. Les nombres indiquent leurs codes décimaux ; 32 est l’espace.](images/lprint-characters.png)

```basic
10 LPRINT "Antislash : ";CHR$(92)
20 LPRINT "Barre verticale : ";CHR$(124)
```

Pour les accents et les signes supplémentaires, préparez un motif GLYPH. La liste complète des caractères LPRINT et un programme pour l’imprimer sont disponibles dans [la référence LPRINT](caracteres-lprint.md). Les dessins personnalisés sont expliqués dans [le chapitre papier](08-papier-dessins.md#glyph).
