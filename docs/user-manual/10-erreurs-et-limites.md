# 10 - Trouver une erreur et améliorer son programme

Une erreur fait partie de l’apprentissage. La machine indique où elle attend une correction ; il reste à comprendre l’instruction demandée. Gardez une copie de votre programme avant de modifier plusieurs lignes à la fois.

<a id="erreurs"></a>
![Printy mène l’enquête : relire une instruction aide à retrouver une erreur.](images/printy-debug.png)

## Le numéro de ligne est votre premier repère

Si l'écran montre `?SYNTAX @120`, commencez par `LIST 120`. Un guillemet est-il fermé ? Manque-t-il une virgule entre les paramètres ? Le nom de variable est-il bien une seule lettre ? Après avoir lu le message, Return permet de retrouver la console.

Le numéro désigne la ligne où l'erreur a été **détectée**. Sa cause peut être plus ancienne : un RETURN sans GOSUB, par exemple, résulte parfois d'un saut qui a amené le programme au mauvais endroit.

| Message ou famille de messages | Ce qu'il faut vérifier |
|---|---|
| `?SYNTAX` | Ponctuation, parenthèses, nom de commande et forme de l'instruction. |
| `?RANGE` | Paramètre hors limites ou décimal là où un entier est exigé. |
| `?MODE` | Revenir au mode adapté à cette commande. |
| `?UNDEFINED LINE` | Destination de GOTO, GOSUB ou IF absente. |
| `?LINE TOO LONG` | Ligne BASIC dépassant sa capacité de saisie. |
| `?PROGRAM FULL`, `?PROGRAM RAM`, `?ARRAY RAM` | Mémoire insuffisante ou problème du programme conservé. |
| `?REDIM` | Tableau déjà déclaré ; vérifier vos DIM et l'initialisation. |
| `?DECIMAL MATH` | Division par zéro, domaine d'une fonction ou résultat non représentable. |
| `?EXPR DEPTH` | Expression trop imbriquée ; la décomposer en plusieurs calculs. |
| `?FOR/NEXT`, `?FOR DEPTH`, `?FOR VARIABLE` | Boucles mal appariées, trop imbriquées ou compteur déjà utilisé. |
| `?GOSUB/RETURN`, `?GOSUB DEPTH` | RETURN sans appel correspondant ou trop d'appels imbriqués. |
| `?LCD CHAR` | Triangle demandé sur une lettre native au lieu d'un espace ou d'un motif personnel. |
| `?LCD SLOTS` | Les huit emplacements de motifs personnalisés sont encore référencés. |
| `?DRAW PENDING` | Composition en attente : l'imprimer ou l'annuler avant de changer de mode. |
| `?DRAW`, `?MOTOR` | Vérifier la composition, le repère, la mémoire de travail et les paramètres. |
| `?TX TIMEOUT`, `?RX...`, `?SERIAL`, `?BAD ACK` | Port, câble, réglages série, session et protocole du logiciel PC. |
| `?BREAK` | Interruption demandée par le joueur ou le programme. |

Ce tableau rassemble les messages utiles. Une même difficulté peut être détectée à plusieurs étapes ; les variantes détaillées de RX décrivent l’état de la réception série.

## Une méthode en quatre petits essais

Commencez par prévoir le résultat d'un cas simple. Pour un total, prenez deux objets à 3 : vous attendez 6. Exécutez ensuite ce cas et comparez. Si le résultat diffère, affichez les valeurs intermédiaires avec PRINT. Enfin, changez une seule ligne et recommencez le même essai.

Pour garder plusieurs traces sans perdre une valeur sur le LCD, vous pouvez les imprimer avec LPRINT. Pour un calcul long, commencez par vérifier un seul passage de la boucle. Pour un dessin, imprimez le contour avant d'ajouter les autres formes.

Une comparaison exacte entre nombres décimaux calculés peut être trop exigeante, surtout après SIN, COS, LOG ou EXP. Si vous cherchez à savoir si un tir est proche de sa cible, comparez une distance à une tolérance : `IF ABS(A-B)<1 THEN ...`. La bonne tolérance dépend des unités du jeu.

<a id="limites"></a>
## Les limites à garder près du clavier

| Élément | Capacité ou règle |
|---|---|
| Programme | Un seul en RAM ; mémoire partagée avec les variables. |
| RAM disponible à vide | 5 951 octets. |
| Numéros de ligne | 1 à 65535. |
| Ligne source | 63 caractères natifs, numéro et espaces compris. |
| Variables | A..Z et A$..Z$ ; noms d'une seule lettre. |
| Chaîne ou résultat chaîne | 63 octets. |
| Tableaux | Numériques, une ou deux dimensions, indices à partir de zéro. |
| Nombres | 8 chiffres significatifs, au plus 7 décimales. |
| FOR et GOSUB | 8 niveaux actifs chacun. |
| Écran | 1 ligne physique de 32 caractères ; historique de 8 lignes. |
| Motifs LCD | 8 emplacements partagés. |
| Texte papier | 72 colonnes ; LLOCATE sur 64 lignes. |
| Composition de dessin | 32 formes. |
| Repère graphique | X 0..247 ; Y 0..255 ; entiers. |
| Session série BASIC | 7 bits, codes 0..127 ; réception sans file logicielle longue. |

Une ligne source accepte plusieurs instructions séparées par `:` dans son même enregistrement. Entre guillemets, le deux-points est un caractère du texte. La tokenisation raccourcit le stockage **en mémoire** ; la saisie conserve sa limite de **63 caractères natifs par ligne**.

## Adapter un programme trouvé dans un autre manuel

Typestar BASIC s’inspire des BASIC classiques et possède sa propre syntaxe. Avant de reprendre un listing, consultez les noms de variables, les formes de DIM, les unités des dessins et les fonctions du clavier.

Pour adapter les petits programmes, construisez les boucles avec **FOR/NEXT ou IF/GOTO**, les choix avec **IF/THEN/ELSE sur une ligne**, et la saisie avec **INPUT vers une variable simple**. RESTORE revient au début des DATA. Le programme et ses données partagent la RAM de la machine. Les structures WHILE/WEND, REPEAT/UNTIL, IF/ENDIF, ON…GOTO et STOP/CONT, ainsi que RENUM, DELETE par plage, les tableaux de chaînes, INKEY$ et les fichiers, demandent une adaptation avec ces outils. Le support des cartouches RAM est envisagé pour la suite.
