# Référence rapide du langage

Cette partie sert à retrouver une forme d'instruction après les ateliers. Les noms en minuscules, comme x ou variable, doivent être remplacés. Les crochets indiquent un élément facultatif : tapez directement la forme choisie. Les virgules, points-virgules et parenthèses font partie de la syntaxe. Le lexique qui suit explique les mots techniques ; l'index final donne les pages des leçons.

## Programme et données

| Forme | Usage |
|---|---|
| `RUN` | Lance le programme, avec remise à zéro des données de travail. |
| `LIST [debut[,fin]]` | Sans argument : tout ; un numéro : cette ligne ; deux : plage inclusive. |
| `LLIST [debut[,fin]]` | Imprime tout le programme, une ligne ou une plage inclusive ; commande directe. |
| `NEW` | Efface programme et données de travail. |
| `CLEAR` | Libère les données de travail, conserve le programme. |
| `MEM` | Affiche les octets libres. |
| `LOAD` ; `SAVE` | Console seulement : reçoit du PC ou lui envoie le programme. |
| `[LET] variable=expression` | Affecte une valeur à une variable ou une cellule numérique. |
| `INPUT ["message";]variable` | Dans RUN : lit un scalaire numérique ou une chaîne. |
| `DIM A(dernier)` | Déclare un tableau 1D, indices de zéro à dernier inclus. |
| `DIM A(rangée,colonne)` | Déclare un tableau numérique 2D, bornes inclusives. |
| `DATA valeur[,valeur...]` | Prépare des constantes numériques ou chaînes entre guillemets. |
| `READ destination[,destination...]` | Lit dans les DATA vers scalaires ou cellules numériques. |
| `RESTORE` | Revient au premier DATA. |
| `REM commentaire` | Ignore le reste de la ligne. |

## Contrôle de l'exécution

| Forme | Usage |
|---|---|
| `GOTO ligne` | Va à une ligne existante. |
| `GOSUB ligne` ; `RETURN` | Appelle un sous-programme et en revient. |
| `IF condition THEN branche [ELSE branche]` | Choisit une branche sur la même ligne ; branche = numéro ou instruction(s). |
| `FOR A=debut TO fin [STEP pas]` | Prépare une boucle, pas non nul ; défaut 1. |
| `NEXT [A]` | Répète ou termine la boucle intérieure. |
| `END` | Termine le programme. |

Plusieurs instructions se séparent par `:` ; la ligne entière reste limitée à 63 caractères natifs, numéro compris. Les nombres de ligne vont de 1 à 65535. Les noms de variables sont A..Z ou A$..Z$ ; les tableaux sont numériques. Les comparaisons donnent -1 pour vrai et 0 pour faux.

## Écran et clavier

| Forme | Usage |
|---|---|
| `PRINT [valeur...]` | LCD ; `;` accole, `,` ajoute un espace, `;` final poursuit la ligne. |
| `CLS` | Efface texte, triangles composés et lignes LCDLINE. |
| `LOCATE 1,colonne` | Place la sortie à une colonne de 1 à 32. |
| `CURSOR mode` | Mode 0..4 ; 0 par défaut, 4 sans curseur. |
| `LCDCHAR p,r1,r2,r3,r4,r5,r6,r7,t` | Position 1..32 ; sept rangées et un triangle, masques 0..31. |
| `LCDTRI p,masque` | Triangle d'un espace ou caractère personnel ; masque 0..31. |
| `LCDLINE p,masque` | Ligne indépendante de cinq pixels ; masque 0..31. |
| `ICON index,code` | Cellule brute 0..31, code 0..255. |
| `KEYS` | Diagnostic des codes physiques du clavier. |

Huit emplacements de motifs sont partagés. Le curseur 0 utilise le bloc natif et laisse ces motifs disponibles. INKEY donne un code traduit, qui peut différer du code physique montré par KEYS.

## Papier

| Forme | Usage |
|---|---|
| `LLIST [debut[,fin]]` | Imprime le listing complet, une ligne ou une plage inclusive ; console. |
| `LPRINT [valeur...]` | Papier, 72 colonnes, police ASCII 32..126 ; séparateurs comme PRINT. |
| `LSPACING 1` ; `1.5` ; `2` | Interligne commun à LPRINT/LLOCATE ; défaut 1.5, origine redéclarée. |
| `LLOCATE ligne,colonne` | Grille texte 1..64 et 1..72. |
| `POINT x,y[,taille]` | Point carré, taille 1..16 ; défaut 1. |
| `LINE x1,y1,x2,y2,epaisseur` | Segment, épaisseur 1..16. |
| `BOX x1,y1,x2,y2,epaisseur,plein` | Rectangle, coins ordonnés ; plein 0 ou 1. |
| `CIRCLE x,y,rayon,epaisseur,plein` | Cercle ou disque ; rayon entier positif, plein 0 ou 1. |
| `DRAW INSTANT` | Formes imprimées immédiatement. |
| `DRAW DEFERRED` | Prépare jusqu'à 32 formes ensemble. |
| `DRAW PRINT` ; `DRAW CANCEL` | Imprime ou abandonne la composition, puis revient à INSTANT. |
| `GLYPH A(indices),largeur,hauteur[,mode]` | Bitmap 1D ou 2D ; modes 1 natif, 2 double X/Y, 3 double X. |
| `ORIGIN [x[,y]]` | Déclare la position présente, sans déplacement. |
| `MOVE x,y` | Position moteur absolue dans le repère déclaré. |
| `HEAD dx` ; `FEED dy` | Déplacements relatifs de tête et de papier. |

Dessin : X 0..247, Y 0..255, entiers ; correction de proportions et rangée native `INT(Y/2)`. Moteurs : X 0..128, Y 0..448, autres unités. Après impression, redéclarer le repère moteur. GLYPH : hauteur 1..16 ; largeur 1..16 en masques 1D, 1..31 en matrice 2D. La largeur 2D correspond au nombre de colonnes et part de la colonne zéro.

## Sons, hasard, série et accès mémoire

| Forme | Usage |
|---|---|
| `BEEP [duree]` | 0..2000 ms ; défaut 100 ms. |
| `SOUND modulation,duree` | 60..750 Hz de modulation, ou 0 pour le silence ; 0..2000 ms. |
| `RANDOMIZE graine` | Graine entière 1..65535, obligatoire. |
| `BAUD debit` | 1200, 2400, 7812, 15625 ou 31250. |
| `SERCFG format` | 7N1, 7N2, 7E1, 7E2, 7O1 ou 7O2 ; sans guillemets. |
| `SEROPEN debit` | Ouvre une session au format choisi. |
| `SEROUT code` | Envoie un code 0..127. |
| `SERCLOSE` | Termine l'émission et ferme la session. |
| `POKE adresse,valeur` | Écrit un octet 0..255 à une adresse CPU 0..65535. |

LOAD/SAVE, sessions et impression graphique partagent les réglages série ; défaut 31250/7E1. Le mode graphique se lance par CODE+P depuis la console. Ce raccourci est réservé à la console.

## Fonctions et constante

| Forme | Valeur produite |
|---|---|
| `ABS(x)` ; `SGN(x)` | Valeur absolue ; signe -1, 0 ou 1. |
| `INT(x)` ; `FIX(x)` | Entier inférieur ; troncature vers zéro. |
| `SQR(x)` | Racine carrée, x positif ou nul. |
| `PI` | 3.1415927 ; sans parenthèses. |
| `SIN(x)` ; `COS(x)` ; `TAN(x)` | Trigonométrie en radians, x entre -1000 et 1000. |
| `ATN(x)` | Arctangente, résultat en radians. |
| `LOG(x)` ; `EXP(x)` | Logarithme naturel et exponentielle. |
| `RND(1)` | Pseudo-aléatoire 0..0.9999 ; argument 1 seulement. |
| `FRE(0)` | Octets libres. |
| `INKEY(0)` | Code de touche disponible ; 0 si rien. |
| `SERIN(0)` | Code série disponible 0..127 ; -1 si rien. |
| `PEEK(adresse)` | Octet lu à une adresse CPU 0..65535. |
| `LEN(s)` ; `ASC(s)` | Longueur ; code du premier caractère, chaîne non vide pour ASC. |
| `CHR$(n)` | Chaîne d'un octet, code 0..255. |
| `STR$(x)` ; `VAL(s)` | Nombre écrit en texte ; constante texte convertie en nombre. |
| `LEFT$(s,n)` ; `RIGHT$(s,n)` | Jusqu'à n caractères pris à gauche ou à droite. |
| `MID$(s,debut[,n])` | Sous-chaîne, première position 1 ; sans n, jusqu'à la fin. |

Une fonction s'emploie dans une expression : `PRINT RND(1)` ou `A=RND(1)`. Les nombres ont huit chiffres significatifs et au plus sept décimales ; les fonctions trigonométriques, LOG et EXP sont approchées. Saisissez directement une valeur entière pour les paramètres qui l’exigent.

## Opérateurs et signes

| Signe ou mot | Rôle |
|---|---|
| `+` ; `-` ; `*` ; `/` ; `^` | Arithmétique ; `+` réunit aussi deux chaînes. |
| `MOD` | Reste d'une division entière, signe du dividende. |
| `=` ; `<>` ; `<` ; `<=` ; `>` ; `>=` | Comparaisons de valeurs du même type. |
| `NOT` ; `AND` ; `OR` | Opérations sur 16 bits ; évaluation des deux opérandes. |
| `%` ; `&H` | Préfixes des constantes binaires et hexadécimales. |
| `:` | Séparateur d'instructions, en dehors des guillemets et de REM. |
| `;` ; `,` | Séparateurs d'affichage ; virgule aussi entre paramètres. |
| `$` | Suffixe des variables et fonctions qui donnent du texte. |

Ordre : puissance ; signe unaire ; multiplication/division ; MOD ; addition/soustraction ; comparaisons ; NOT ; AND ; OR. Les parenthèses imposent un regroupement. Les opérandes bit à bit et MOD sont des entiers de -32768 à 65535 ; les résultats bit à bit sont interprétés signés.
