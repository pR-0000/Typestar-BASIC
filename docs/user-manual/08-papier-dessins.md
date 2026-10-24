# 8 - Votre programme laisse une trace sur le papier

L'écran montre le résultat du moment. Le papier peut garder le journal d'une partie, une carte ou une figure. Préparez une feuille bien engagée dans les rouleaux. Pour les dessins et les essais nombreux, le **papier thermique A4, de préférence sans BPA**, permet d'économiser le ruban de transfert ; le papier ordinaire demande ce ruban.

Commencez par de petits motifs, loin des bords. Choisissez une origine et vérifiez que le dessin tiendra sur votre feuille. **Les traits restent imprimés** : chaque nouveau motif se superpose aux traces déjà présentes.

![Le personnage présente un carré, un cercle et un trait : votre feuille devient un terrain de dessin](images/illustration-dessins-papier.png)

<a id="lprint"></a>
## LPRINT : afficher sur le papier

```basic
10 LPRINT "MON PREMIER PROGRAMME"
20 LPRINT "2+3=";2+3
```

LPRINT utilise le même principe que PRINT : texte entre guillemets, valeurs calculées, point-virgule pour accoler et virgule pour ajouter un espace. Le premier L rappelle que cette sortie s'adresse à l'imprimante. La commande s'écrit **LPRINT**, avec un seul L au début.

Un point-virgule final conserve la ligne papier pour la suite :

```basic
10 LPRINT "JOUR ";1;" - ";
20 LPRINT "SCORE ";25
30 LPRINT
```

Les deux premières instructions écrivent JOUR 1 - SCORE 25 sur une seule ligne. La troisième ajoute une ligne vide. Sans point-virgule final, la ligne est terminée et le papier avance selon l'interligne sélectionné.

La largeur maximale est **72 caractères**. Vous choisissez les fins de ligne de vos paragraphes ; une instruction dépassant l’espace restant est refusée avant l’impression. Plusieurs chaînes courtes peuvent composer une longue ligne papier : plusieurs lignes BASIC de 63 caractères peuvent contribuer à une même ligne imprimée.

### La police papier et la police LCD

La police est le **Courier 10 du firmware Canon d’origine**, comprimé sans perte pour tenir dans la ROM BASIC. Quelques signes de ponctuation ont été adaptés à la table ASCII. LPRINT propose les **95 caractères ASCII imprimables**, de 32 à 126 : lettres, chiffres et ponctuation. Cela comprend l'antislash, la barre verticale et les crochets. `CHR$(92)` imprime l'antislash et `CHR$(124)` la barre verticale. `CHR$(34)` permet d'insérer un guillemet.

![Les caractères disponibles dans la police papier LPRINT](images/lprint-characters.png)

Pour vos premiers textes papier, utilisez les lettres de cette table, comme « Cafe ». Les codes acceptés vont de **32 à 126** ; une autre valeur déclenche une erreur. GLYPH et les commandes géométriques permettent de créer des signes particuliers, des accents ou des dessins.

<a id="llist"></a>
## LLIST : garder son programme sur papier

Vous avez écrit quelques lignes et souhaitez les relire tranquillement ? Tapez **LLIST** au prompt `>` : la machine imprime les numéros et les instructions du programme en mémoire.

```basic
LLIST
```

Pour retrouver seulement une ligne, indiquez son numéro. Pour choisir un passage, donnez le premier et le dernier numéro, séparés par une virgule :

```basic
LLIST 20
LLIST 10,100
```

Les deux limites sont comprises dans la plage. Les lignes absentes sont simplement sautées. Le listing utilise **Courier 10** et l’interligne choisi par **LSPACING**. Les lignes s’impriment à la suite ; **MARGIN RELEASE / BREAK** permet d’interrompre l’impression. Une ligne papier déjà commencée avec LPRINT et un point-virgule est terminée avant le listing.

LLIST est une **commande de la console**, comme LIST. Votre programme et ses variables restent en mémoire. Sur le papier, les caractères propres au LCD qui sortent de la table ASCII apparaissent sous la forme **?** : par exemple, « été » donne « ?t? ». Le listing continue normalement. Le texte complet reste disponible avec LIST et SAVE dans Studio. Une petite réserve de RAM libre permet au pilote de préparer les glyphes, comme pour LPRINT.

> **À essayer :** chargez Piano dans Studio, envoyez-le à la machine, puis tapez `LSPACING 1.5` et `LLIST 10,100`. Vous obtenez le début de son listing, prêt à être annoté au crayon.

<a id="lspacing"></a>
## LSPACING : choisir l'interligne

```basic
LSPACING 1.5
```

Les trois choix sont **1**, **1.5** et **2**. Le réglage habituel est 1.5. Un interligne de 1 est serré ; 1.5 laisse un peu d'air ; 2 double le pas de ligne. Ces valeurs règlent à la fois l'avance de LPRINT et la grille utilisée par LLOCATE.

Choisissez l’interligne **avant** de préparer votre bloc de texte. LSPACING déclare la position physique courante comme nouvelle origine du texte. Changer le réglage au milieu d’une mise en page change donc son point de départ. Les dessins et FEED conservent leurs propres unités.

<a id="llocate"></a>
## LLOCATE : revenir à une case du texte

`LLOCATE ligne,colonne` place le prochain texte dans une grille de **64 lignes et 72 colonnes**, numérotées à partir de 1. Sa première position correspond à la position physique lors de l’établissement du repère texte. Placez donc la feuille à l’endroit voulu avant de définir votre repère.

```basic
10 LSPACING 1.5
20 LPRINT "NOM       SCORE"
30 LPRINT "ALICE"
40 LLOCATE 2,11:LPRINT 25;
```

La ligne ALICE a été imprimée, puis le score est ajouté en colonne 11 de cette même ligne. Le papier se repositionne pour atteindre la cible. Revenir sur un texte permet de **superposer** des signes : les marques existantes restent sur le papier.

LLOCATE et LPRINT partagent le même repère. Après une opération de dessin, de glyphe ou de moteur, établissez un nouveau bloc de texte avec LSPACING ou ORIGIN, à une position connue. Vous retrouverez ainsi un repère cohérent pour les prochaines lignes.

Des allers-retours répétés peuvent introduire une petite dérive mécanique, observée pendant les essais. La calibration dépend de la machine et du papier utilisés. Pour un journal, avancez autant que possible dans un seul sens ; pour un jeu qui réimprime sur une grille, vérifiez le résultat sur votre exemplaire.

<a id="repere-graphique"></a>
## Avant de dessiner : trois unités différentes

Le texte utilise des **lignes et des colonnes**. Les formes utilisent des **coordonnées graphiques**. Les moteurs utilisent des **unités de déplacement**. Chaque repère possède sa propre unité.

Dans un dessin, X augmente vers la droite et Y vers le bas de la figure. Les coordonnées autorisées sont **X de 0 à 247** et **Y de 0 à 255**. L'unité graphique corrige la différence de taille physique des points sur les deux axes : une largeur et une hauteur égales donnent approximativement un carré.

![Un repère graphique : X vers la droite, Y vers le bas](images/repere-graphique.png)

Ces coordonnées définissent une fenêtre logique de dessin sur la feuille. La tête imprime sur des rangées natives : Y est converti en `INT(Y/2)`. Deux ordonnées consécutives peuvent tomber sur la même rangée. Les petites courbes montrent les marches de cette grille de points.

Pour un dessin complet, définissez les formes dans le même repère avec DRAW DEFERRED. Pour placer plusieurs dessins sur la feuille, utilisez les moteurs entre les compositions, en tenant compte de leurs propres unités.

<a id="point"></a>
<a id="line"></a>
## POINT et LINE : les premiers traits

`POINT x,y` imprime un point. `POINT x,y,taille` imprime un point carré, dont la taille vaut de **1 à 16** ; le défaut est 1.

`LINE x1,y1,x2,y2,epaisseur` relie deux points. L'épaisseur, obligatoire, est un entier de **1 à 16**. Les coordonnées doivent également être des entiers.

```basic
10 LINE 0,0,60,40,2
```

Le trait va du premier point au second. Pour une ligne horizontale, gardez la même valeur Y ; pour une ligne verticale, gardez la même valeur X. Augmentez l'épaisseur pour un trait plus visible, sans dépasser 16.

<a id="box"></a>
## BOX : un rectangle vide ou plein

```basic
10 BOX 0,0,60,40,2,0
```

Les deux couples de coordonnées désignent les coins opposés du rectangle. Placez le premier coin à gauche et au-dessus du second, avec **x1 ≤ x2 et y1 ≤ y2**. L’avant-dernier nombre est l’épaisseur. Le dernier choisit le remplissage : **0 pour le contour**, **1 pour un rectangle plein**.

`BOX 0,0,40,40,2,0` donne un carré. Pour une forme pleine, indiquez quand même l'épaisseur : `BOX 0,0,40,40,1,1`.

<a id="circle"></a>
## CIRCLE : un cercle ou un disque

```basic
10 CIRCLE 30,30,20,2,0
```

Les deux premiers nombres donnent le centre, le troisième le rayon, puis viennent l'épaisseur et le remplissage. Le rayon doit être entier et positif ; l'épaisseur va de 1 à 16. Le dernier paramètre vaut 0 pour un contour et 1 pour un disque plein.

Le cercle entier doit tenir dans les limites du dessin. Avec un centre 30,30 et un rayon 20, la figure reste entre 10 et 50 sur les deux axes. Un très petit cercle ressemble parfois à un polygone arrondi : c’est l’effet du nombre limité de points.

<a id="draw"></a>
## DRAW : imprimer maintenant ou préparer une composition

Le mode habituel est **DRAW INSTANT**. Chaque POINT, LINE, BOX ou CIRCLE s’imprime aussitôt. L’impression peut faire avancer le papier ; la commande suivante utilise la position physique courante. Pour superposer plusieurs formes dans un même repère, préparez une composition différée.

Pour combiner un rectangle, sa diagonale et un cercle, préparez-les ensemble :

```basic
10 DRAW DEFERRED
20 BOX 0,0,60,60,2,0
30 LINE 0,0,60,60,2
40 CIRCLE 30,30,20,2,0
50 DRAW PRINT
```

DRAW DEFERRED ouvre une composition. Les commandes ajoutent leurs formes à la liste, sans impression immédiate. DRAW PRINT imprime l'ensemble, ferme la composition et revient au mode immédiat. DRAW CANCEL abandonne le dessin sans l'imprimer et revient également au mode immédiat.

Une composition contient au maximum **32 formes**. POINT compte comme une forme, même si sa taille est 1. DRAW DEFERRED appelé une deuxième fois conserve la liste déjà ouverte. Pour repartir de zéro, annulez-la d'abord. Le passage à INSTANT est refusé tant que des formes restent en attente ; imprimez ou annulez la composition.

La composition réduit aussi les déplacements et les impressions répétées sur les mêmes bandes. Les zones vides en fin de bande et les bandes entièrement vides sont sautées lorsqu'elles peuvent l'être. Préparer les éléments ensemble reste souvent plus rapide que lancer un dessin pour chaque petit trait.

<a id="origin"></a>
<a id="move"></a>
<a id="head"></a>
<a id="feed"></a>
## ORIGIN, MOVE, HEAD et FEED : commander les moteurs

Ces commandes servent au positionnement. **ORIGIN déclare les coordonnées de la position physique courante**. MOVE, HEAD et FEED effectuent les mouvements ; c’est vous qui choisissez le point de départ du repère.

| Commande | Signification | Limites |
|---|---|---|
| `ORIGIN` | Déclare la position courante comme 0,0. | Définition du repère. |
| `ORIGIN x,y` | Lui attribue les coordonnées indiquées. | X 0..128 ; Y 0..448. |
| `MOVE x,y` | Va à une position absolue dans ce repère. | X 0..128 ; Y 0..448. |
| `HEAD dx` | Déplace la tête relativement. | dx -128..128. |
| `FEED dy` | Déplace le papier relativement. | dy -448..448. |

ORIGIN avec X seul donne Y=0. Une **unité moteur représente deux changements de phase** ; les repères texte et graphique emploient leurs propres unités. La position finale doit rester dans les limites. Une valeur négative de FEED inverse le mouvement ; une valeur positive fait avancer le papier dans le sens de progression de l’impression.

```basic
ORIGIN:HEAD 8:HEAD -8
ORIGIN:FEED 112:FEED -112
```

Le firmware applique automatiquement une **compensation fractionnaire des reculs du papier**, commune à FEED, MOVE et LLOCATE. Les essais sur S-60 et S-70 ont retenu une petite avance séparée répartie à raison d'une unité toutes les quatre opérations de recul admissibles. Le repère logique reste celui du programme. L'état des rouleaux et le maintien de la feuille déterminent aussi la précision des retours.

Le premier essai décale la tête et la ramène. Le second effectue un aller-retour du papier. Préparez la feuille pour qu’elle reste engagée pendant les deux mouvements. Ces commandes entraînent seulement les moteurs ; la chauffe est commandée par l’impression.

Pour reculer depuis la position courante, attribuez-lui une coordonnée positive connue : `ORIGIN 0,112:FEED -56`. ORIGIN déclare la position estimée à 112, puis FEED commande le recul de 56 unités.

Une impression, une erreur ou BREAK invalide le suivi moteur. Redéclarez ORIGIN avant une nouvelle séquence et fermez les compositions graphiques avant de commander les moteurs. Laissez le programme entraîner le papier pour conserver son repère.

<a id="glyph"></a>
## GLYPH : imprimer votre propre dessin

Un **glyphe** est un dessin de pixels. Dans une liste, chaque rangée contient un masque binaire, hexadécimal ou décimal. Largeur et hauteur vont de **1 à 16** ; le bit largeur-1 représente le pixel de gauche.

```basic
10 DIM A(7)
20 DATA %00111100,%01000010,%10100101,%10000001
30 DATA %10100101,%10011001,%01000010,%00111100
40 FOR I=0 TO 7:READ A(I):NEXT I
50 GLYPH A(0),8,8,3
```

Ce visage possède huit rangées de huit pixels. A(0) indique la première rangée à utiliser ; 8,8 donne les dimensions ; 3 choisit le mode de proportions.

| Mode | Effet |
|---:|---|
| 1 | Points natifs, un point par pixel déclaré ; défaut si le mode est omis. |
| 2 | Doublement horizontal et vertical. |
| 3 | Doublement horizontal seulement, pour des proportions approximativement carrées. |
| 4 | Grands pixels carrés : deux fois la largeur et la hauteur du mode 3. |

Les points natifs sont plus hauts que larges : le **mode 3** donne des proportions approximativement carrées. Le **mode 2** double les deux dimensions en conservant le rapport natif. Indiquez toujours les dimensions de la source.

### Répéter un motif dans une même passe

Pour imprimer cinq visages côte à côte, remplacez la ligne 50 du programme précédent par :

```basic
50 GLYPH A(0),8,8,4,5
```

Le dernier nombre choisit **1 à 16 répétitions**. Le firmware prépare le dessin une seule fois par bande, puis enchaîne les copies avec un tampon de taille constante. La touche **MARGIN RELEASE/BREAK** interrompt le groupe entre deux blocs.

Un motif de **16 × 16 en mode 4** occupe 32 unités HEAD de large et deux bandes de 56 unités FEED. Dix copies demandent deux passes : leurs moitiés hautes, puis leurs moitiés basses. Les cadres de répétition sont arrondis à la largeur d'un bloc natif ; un petit motif peut donc laisser un espace entre les copies. Les dimensions indiquées restent celles de la source. Pour dessiner une rangée de murs, la forme complète est `GLYPH A(0),16,16,4,10`.

### Une rangée de motifs différents

Le **mode 5** imprime de **1 à 40 motifs de 8 × 8** en un passage, avec les grands pixels carrés du mode 4. Les cases vides gardent leur place dans la rangée et la tête reste engagée entre les dessins.

Le tableau commence par une palette de **16 motifs**, chacun décrit par **quatre nombres de 16 bits** : les huit bits de gauche donnent une ligne, les huit suivants la ligne du dessous. Les **64 premiers éléments** contiennent cette palette. Les éléments suivants choisissent les motifs de la rangée, par leurs numéros **0 à 15**.

```basic
10 DIM G(67)
20 G(4)=%1111111110000001
30 G(5)=%1000000110000001
40 G(6)=%1000000110000001
50 G(7)=%1000000111111111
60 G(64)=1:G(65)=0:G(66)=1:G(67)=1
70 LSPACING 1:GLYPH G(0),4,8,5
```

DIM prépare les éléments à zéro : le motif **0** reste vide. Les lignes 20 à 50 dessinent un cadre dans le motif **1**. La dernière ligne imprime **cadre, vide, cadre, cadre**. Dans cette forme particulière de GLYPH, le deuxième argument compte les **motifs** ; le troisième vaut **8**. L'avance papier suit LSPACING : **1** rapproche les rangées en bandes de 56 unités, **1.5** ou **2** ajoutent de l'espace. Chaque rangée utilise un seul retour de tête. Le firmware adapte le cache à la RAM libre ; il emprunte au minimum 316 octets en plus du tableau et des variables.


### Une matrice pour les pixels

Une matrice contient **0 ou 1 par pixel**, sur **1 à 31 colonnes** et **1 à 16 rangées**. La largeur donnée doit correspondre au tableau ; la colonne de départ est zéro.

```basic
10 DIM M(3,3)
20 FOR I=0 TO 3
30 M(I,I)=1
40 NEXT I
50 GLYPH M(0,0),4,4,3
```

Le programme imprime une diagonale ; les autres cellules restent à zéro. Une cellule numérique occupe cinq octets : une liste de masques économise la mémoire.

GLYPH imprime immédiatement une source complète. Fermez d’abord toute composition différée ou ligne de texte. Le pilote avance par bandes de 16 points natifs, y compris pour un motif plus court.

**À vous de jouer.** Imprimez le visage en modes 1, 2, 3 et 4. Comparez ses proportions pour choisir le mode de votre prochain jeu.
