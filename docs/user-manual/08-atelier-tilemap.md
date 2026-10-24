# Atelier : une carte faite de petits dessins

Une **tilemap** est une carte composée de petites cases. Nous préparons quelques dessins dans une **palette**, puis nous indiquons leurs numéros pour composer le plan. Pensez à une mosaïque : le mur est le motif **1**, le coffre le motif **2**, et **0** laisse du papier blanc.

Ouvrez [tilemap-fr.bas](../../examples/graphics/tilemap-fr.bas) dans **Typestar BASIC Studio**. Le programme utilise un seul tableau, **G**, pour préparer une carte de **6 colonnes et 4 rangées**. Voici d'abord comment les données arrivent jusqu'à l'imprimante.

## DATA prépare les valeurs ; READ les prend une par une

**DATA contient des constantes dans le texte du programme.** Une constante peut être un nombre, comme 1, ou un dessin binaire, comme `%11111111`. Le programme choisit leur destination avec **READ**.

Imaginez toutes les valeurs DATA alignées sur un long ruban. Un petit repère indique la prochaine valeur à lire. Au lancement par RUN, le repère se trouve au début. Chaque READ prend la valeur suivante et avance le repère. Avec plusieurs valeurs sur une ligne DATA, la lecture se fait de gauche à droite, puis continue dans le DATA suivant. Les commentaires sont sautés.

Les **numéros de ligne BASIC classent les DATA dans leur ordre de lecture**. On peut les renuméroter en gardant cet ordre et obtenir le même dessin. Le nom du tableau choisi par READ décide où ranger les valeurs : `READ A,B` remplit A puis B ; `READ G(64)` remplit directement la cellule G(64).

Les DATA peuvent se trouver après END, comme ici : READ cherche les valeurs dans le programme complet. END termine l'exécution des instructions. `RESTORE` ramène le repère au premier DATA ; GOTO, lui, choisit la prochaine instruction à exécuter. Dans cet atelier, nous conservons le repère entre la lecture des dessins et celle du plan, pour parcourir tout le ruban dans l'ordre.

## Pourquoi partager le même tableau ?

Le **mode rapide 5 de GLYPH attend un format précis** : d'abord les pixels d'une palette de 16 dessins, puis les numéros des dessins à imprimer dans une rangée. Le tableau G réunit ces deux parties côte à côte. La palette reste en place ; la petite partie décrivant la rangée est réutilisée quatre fois. Cela économise de la RAM et permet un balayage continu de la tête pour chaque rangée.

| Éléments du tableau | Rôle |
|---|---|
| G(0) à G(3) | Dessin 0 : sol vide, déjà à zéro après DIM. |
| G(4) à G(7) | Dessin 1 : mur, chargé une seule fois. |
| G(8) à G(11) | Dessin 2 : coffre, chargé une seule fois. |
| G(12) à G(63) | Place pour 13 autres dessins, laissée à zéro. |
| G(64) à G(69) | Les 6 numéros de dessins de la rangée à imprimer maintenant. |

Les **64 premières valeurs** décrivent donc les dessins. Les **6 suivantes** sont des choix dans cette palette : 0 pour le sol, 1 pour le mur, 2 pour le coffre. Le numéro d'un dessin désigne sa place dans la palette ; le numéro d'une ligne BASIC désigne sa place dans le programme.

## Le programme complet

Chaque dessin est écrit sur **8 lignes DATA de 8 bits**, une par rangée de pixels. Les quatre dernières lignes DATA décrivent le plan. Lisez les commentaires, puis suivez le parcours des valeurs expliqué après le listing.

```basic
10 REM UNE CARTE DE 6 COLONNES ET 4 RANGEES
20 REM G(0) A G(63) : PALETTE DE 16 MOTIFS
30 REM G(64) A G(69) : LES 6 CASES A IMPRIMER
40 DIM G(69)
50 REM MOTIF 0 : LE SOL RESTE VIDE GRACE A DIM
60 REM MOTIF 1 : LE MUR OCCUPE G(4) A G(7)
70 REM MOTIF 2 : LE COFFRE OCCUPE G(8) A G(11)
80 REM READ LIT LES DATA DANS LEUR ORDRE
90 FOR I=4 TO 11
100 READ A,B
110 G(I)=256*A+B
120 NEXT I
130 REM LSPACING 1 RAPPROCHE LES BANDES DE LA CARTE
140 LSPACING 1
150 REM READ CONTINUE : 6 NUMEROS POUR 1 RANGEE
160 FOR Y=1 TO 4
170 FOR X=0 TO 5
180 READ G(64+X)
190 NEXT X
200 REM 6 MOTIFS DE 8 PIXELS DE HAUT, MODE 5
210 GLYPH G(0),6,8,5
220 NEXT Y
230 REM PRESENTER LE DESSIN AU-DESSUS DE LA TETE
240 ORIGIN:FEED 128
250 END
260 REM MOTIF 1 : MUR, 1 LIGNE DATA PAR RANGEE
270 DATA %11111111
280 DATA %10001000
290 DATA %10001000
300 DATA %11111111
310 DATA %00100010
320 DATA %00100010
330 DATA %11111111
340 DATA %10001000
350 REM MOTIF 2 : COFFRE, LU DE HAUT EN BAS
360 DATA %00000000
370 DATA %00111100
380 DATA %01000010
390 DATA %01111110
400 DATA %01011010
410 DATA %01000010
420 DATA %01111110
430 DATA %00000000
440 REM LA CARTE : 0 SOL, 1 MUR, 2 COFFRE
450 DATA 1,1,1,1,1,1
460 DATA 1,0,0,0,0,1
470 DATA 1,0,2,0,0,1
480 DATA 1,1,1,1,1,1
```

![La carte imprimée : des murs, du sol et un coffre. Chaque rangée est imprimée en une passe.](images/atelier-tilemap.png)

## Suivre les données jusqu'au papier

### 1. Préparer le tableau

La ligne **40**, `DIM G(69)`, crée **70 cellules**, numérotées de 0 à 69, toutes à zéro. Le dessin 0 représente ainsi le sol vide. Nous allons remplir les dessins 1 et 2, puis les six cases de la rangée à imprimer.

### 2. Lire les pixels du mur et du coffre

La boucle **90 à 120** fait varier I de 4 à 11, soit **8 tours**. À chaque tour, la ligne **100**, `READ A,B`, lit **2 valeurs** : une rangée de pixels dans A, puis la suivante dans B. Elle consomme ainsi les **16 valeurs DATA des lignes 270 à 430**, dans leur ordre.

La ligne **110**, `G(I)=256*A+B`, range cette paire dans G. Le pilote attend deux rangées de huit pixels par valeur. Multiplier A par **256**, soit **2 puissance 8**, place ses huit pixels devant ceux de B. Les deux premières lignes du mur, `%11111111` et `%10001000`, deviennent ainsi `%1111111110001000` dans G(4).

| Tour de boucle | Valeurs lues par READ A,B | Destination préparée par la ligne 110 |
|---|---|---|
| I = 4 | DATA des lignes 270 et 280 | G(4), début du mur. |
| I = 5 | DATA des lignes 290 et 300 | G(5), suite du mur. |
| I = 7 | DATA des lignes 330 et 340 | G(7), fin du mur. |
| I = 8 | DATA des lignes 360 et 370 | G(8), début du coffre. |
| I = 11 | DATA des lignes 420 et 430 | G(11), fin du coffre. |

Un **1** imprime un point noir ; un **0** laisse le papier blanc. Regardez les huit lignes du coffre de haut en bas : vous pouvez reconnaître sa forme directement dans les bits. Les zéros placés à gauche gardent les rangées alignées.

### 3. Continuer la lecture avec le plan

Après ces 16 valeurs, le repère de lecture attend **le premier 1 de la ligne 450**. La boucle **170 à 190** fait varier X de 0 à 5. La ligne **180**, `READ G(64+X)`, range directement les six prochaines valeurs dans G(64) à G(69).

| Rangée Y | DATA lus | Contenu de G(64) à G(69) |
|---|---|---|
| 1 | Ligne 450 | 1, 1, 1, 1, 1, 1 |
| 2 | Ligne 460 | 1, 0, 0, 0, 0, 1 |
| 3 | Ligne 470 | 1, 0, 2, 0, 0, 1 |
| 4 | Ligne 480 | 1, 1, 1, 1, 1, 1 |

Ces nouvelles valeurs remplacent uniquement les six cases de travail. Les dessins de G(0) à G(63) restent prêts à servir. La boucle extérieure Y nous fait lire puis imprimer chacune des quatre rangées.

### 4. Donner le tableau à GLYPH

La ligne **210**, `GLYPH G(0),6,8,5`, signifie : « utilise le tableau à partir de G(0), imprime **6 dessins de 8 pixels de haut**, avec le **mode 5** ». G(0) indique ici le point de départ du tampon.

GLYPH lit les pixels dans les 64 premières cellules et les choix de la rangée dans les six suivantes. Il dessine alors les motifs dans leur ordre. **READ a chargé les données ; la ligne 110 a assemblé les pixels ; GLYPH imprime le tableau préparé.** Le lien entre DATA et l'impression est donc écrit explicitement par ces instructions.

`LSPACING 1` rapproche les bandes pour former une carte continue. Le mode 5 conserve les grands pixels carrés du mode 4 et enchaîne les motifs, y compris les cases vides, dans une même passe. Enfin, la ligne 240 présente le dessin au-dessus de la tête.

## À vous de jouer !

Remplacez un **1** du bord par **0** pour ouvrir une porte. Déplacez le **2** dans les DATA du plan pour changer la place du coffre. Les numéros de ligne peuvent évoluer : gardez les DATA des dessins avant ceux du plan, dans le même ordre que leurs READ.

Pour créer le dessin **3**, ajoutez ses **8 lignes DATA** entre le coffre et le plan. Étendez la boucle de chargement à `FOR I=4 TO 15` : le nouveau dessin remplira G(12) à G(15). Placez ensuite des **3** dans le plan.

Pour passer à huit colonnes, utilisez `DIM G(71)`, remplacez `FOR X=0 TO 5` par `FOR X=0 TO 7`, ajoutez deux valeurs dans chaque rangée du plan et appelez `GLYPH G(0),8,8,5`. Une rangée accepte jusqu'à **40 dessins** ; réservez autant de cellules après les 64 valeurs de la palette.

Un dessin de **16 × 16** se partage en quatre motifs de 8 × 8 : haut gauche, haut droit, bas gauche et bas droit. On imprime les parties hautes de toute la rangée, puis les parties basses. **Les Ruines** et **Duel Orbital** utilisent ce principe pour garder leurs grands dessins en réduisant les retours de tête.
