# Lexique

Ce lexique explique les mots rencontrés dans le manuel. Les liens conduisent à la leçon correspondante. Dans le PDF, leurs numéros de page sont calculés à chaque génération : ils suivent donc les ajouts de texte et d'illustrations. L'index alphabétique des commandes et fonctions se trouve à la fin du volume.


## Affectation

Action de ranger une valeur dans une variable. Dans `A=A+1`, le BASIC calcule d'abord A+1, puis remplace la valeur de A par ce résultat. Voir [LET](04-nombres-variables.md#let).

## Argument ou paramètre

Valeur donnée à une instruction ou à une fonction pour préciser son travail. Dans `SOUND 300,100`, 300 est la modulation et 100 la durée. Voir [SOUND](09-sons-serie-memoire.md#sound).

## ASCII

Table de codes qui associe des nombres aux lettres, chiffres et signes usuels. La police papier utilise les codes imprimables de 32 à 126 ; les accents du LCD ont d'autres codes. Voir [LPRINT](08-papier-dessins.md#lprint).

## BASIC

Langage de programmation conçu pour apprendre en donnant des instructions simples. Son nom vient de l'anglais « Beginner's All-purpose Symbolic Instruction Code ». Typestar BASIC en est une version adaptée à notre machine. Voir [les premiers pas](03-premiers-pas.md).

## Bauds

Unité du débit de la liaison série. Dans notre liaison, un symbole transporte un bit ; un caractère demande plusieurs bits de données et d'encadrement. Le nombre de caractères par seconde est donc inférieur au nombre de bauds. Voir [BAUD et SERCFG](09-sons-serie-memoire.md#baud).

## Binaire

Écriture des nombres avec les chiffres 0 et 1. En BASIC, `%10101` vaut 21. Cette écriture montre bien les pixels allumés et éteints d'une rangée. Voir [binaire et hexadécimal](04-nombres-variables.md#binaire-hexadecimal).

## Bit

Information qui peut valoir 0 ou 1. Un masque de cinq bits commande cinq pixels. Huit bits forment un octet. Voir [LCDCHAR](07-ecran-clavier.md#lcdchar).

## Boucle

Partie du programme que l'on répète. FOR/NEXT prépare une répétition comptée ; IF/GOTO peut recommencer jusqu'à ce qu'une condition change. Voir [FOR et NEXT](05-decisions-boucles.md#for).

## BREAK

Interruption demandée par l'utilisateur. La touche MARGIN RELEASE joue ce rôle. Le programme s'arrête et le message attend Return. Voir [les erreurs](10-erreurs-et-limites.md#erreurs).

## Broche

Patte métallique qui relie un circuit à son support. La broche 1 sert à repérer son orientation : placez-la du côté indiqué par le support et le guide. Voir [le remplacement de la ROM](02-installation-firmware.md#installation).

## Caractère

Lettre, chiffre, signe ou motif visible. Un code désigne un caractère, mais ce code peut avoir un dessin différent selon la police du LCD ou du papier. Voir [ASC et CHR$](06-fonctions-nombres-chaines.md#chr).

## Chaîne

Suite de caractères traitée comme du texte. Une constante chaîne s'écrit entre guillemets ; une variable chaîne se termine par `$`, comme A$. Voir [les fonctions de texte](06-fonctions-nombres-chaines.md#len).

## Clip

Attache en plastique qui retient une coque sans vis. Une petite pression dans le bon sens permet de la dégager. Voir [le démontage](02-installation-firmware.md#installation).

## Commentaire

Explication placée dans le programme pour son lecteur. REM fait ignorer au BASIC tout le reste de la ligne. Voir [REM](05-decisions-boucles.md#rem).

## Comparaison

Question qui rapproche deux valeurs : égales, différentes, plus petites ou plus grandes. Le résultat numérique est -1 pour vrai et 0 pour faux. Voir [les comparaisons](05-decisions-boucles.md#comparaisons).

## Composition différée

Préparation de plusieurs formes dans un même repère, avant leur impression ensemble. Voir [DRAW](08-papier-dessins.md#draw).

## Concaténation

Réunion de deux chaînes avec `+`. `"TYPE"+"STAR"` donne TYPESTAR. Voir [STR$ et VAL](06-fonctions-nombres-chaines.md#str).

## Condition

Expression qui permet de choisir une action. Zéro signifie faux ; une valeur non nulle signifie vrai. Voir [IF, THEN et ELSE](05-decisions-boucles.md#if).

## Console

Dialogue au clavier avec l'invite `>`. On y tape des commandes immédiates ou des lignes numérotées destinées au programme. Voir [la prise en main](03-premiers-pas.md).

## Constante

Valeur écrite directement dans le programme, comme 12, PI ou "BONJOUR". Elle se distingue d'une variable dont le contenu peut changer. Voir [les valeurs](04-nombres-variables.md).

## Coordonnées

Nombres qui décrivent une position. Le texte, le dessin et les moteurs possèdent chacun leurs unités. Voir [les repères papier](08-papier-dessins.md#repere-graphique).

## Curseur

Repère qui montre où se fera la saisie ou l'affichage suivant. Voir [CURSOR](07-ecran-clavier.md#cursor).

## Débogueur

Outil pour observer la mémoire et le travail du processeur pendant l'exécution d'un programme. Dans Studio, les registres, les flags et les instructions désassemblées complètent la vue des octets. Voir [le débogueur de Studio](02-studio.md#debogueur).

## Décimal

Nombre écrit avec un point pour sa partie fractionnaire, comme 2.5. Les résultats ont une précision limitée. Voir [les nombres](04-nombres-variables.md).

## DIP

Boîtier de circuit possédant deux rangées de broches. Un DIP de 28 broches en a 14 de chaque côté. La compatibilité demande aussi les mêmes fonctions et niveaux électriques sur les broches. Voir [le choix de la ROM](02-installation-firmware.md#installation).

## Éditeur

Espace de travail où l'on écrit et modifie le texte d'un programme. Celui de Studio colore les mots selon leur rôle et aide à vérifier les limites de la machine. Voir [l'éditeur de Studio](02-studio.md#editeur).

## Émulateur

Logiciel qui reproduit le fonctionnement d'une machine. Celui de Studio exécute les ROM choisies avec un processeur HD6301 et des périphériques simulés : LCD, clavier, papier et buzzer. Voir [la Typestar virtuelle](02-studio.md#emulateur).

## Encoche

Petit creux à une extrémité d'un circuit DIP, utilisé pour retrouver le côté de la broche 1. Dans IC8, l'encoche est à gauche lorsque le clavier est devant vous. Voir [le sens de la ROM](02-installation-firmware.md#installation).

## EPROM

Mémoire programmable qui conserve son contenu sans alimentation. Une EPROM à fenêtre se réutilise après un effacement aux ultraviolets ; la W27C512 proposée ici s'efface électriquement avec un programmateur. Voir [la préparation de la ROM](02-installation-firmware.md#installation).

## Expression

Ensemble de valeurs, fonctions et opérateurs qui produit un résultat. Dans `P*N+2`, le BASIC calcule la multiplication, puis l'addition. Voir [les priorités](04-nombres-variables.md#priorites).

## Firmware

Programme interne de la machine. Typestar BASIC remplace une partie du firmware dans la ROM externe et réutilise des services de la ROM interne Canon. Voir [le HD6301](02-hd6301.md). Voir aussi [son installation](02-installation-firmware.md#installation).

## Fonction

Outil du BASIC qui produit une valeur utilisable dans une expression. `SQR(9)` donne 3 ; PRINT peut ensuite afficher ce résultat. Voir [les fonctions](06-fonctions-nombres-chaines.md).

## Glyphe

Petit dessin d'un caractère ou d'un sprite. Il est décrit par des rangées de pixels. Voir [GLYPH](08-papier-dessins.md#glyph).

## Graine

Valeur de départ d'une suite pseudo-aléatoire. La même graine permet de reproduire la même suite. Voir [RND et RANDOMIZE](06-fonctions-nombres-chaines.md#rnd).

## Hexadécimal

Écriture des nombres en base seize, avec 0 à 9 et A à F. `&H1F` vaut 31. Voir [binaire et hexadécimal](04-nombres-variables.md#binaire-hexadecimal).

## Indice

Numéro d'une cellule de tableau. Les indices commencent à zéro et la borne donnée à DIM est comprise. Voir [DIM](04-nombres-variables.md#dim).

## Instruction

Ordre donné au BASIC, comme PRINT, INPUT ou MOVE. Une ligne peut contenir plusieurs instructions séparées par `:`. Voir [la prise en main](03-premiers-pas.md).

## Interligne

Distance entre deux lignes de texte sur le papier. Voir [LSPACING](08-papier-dessins.md#lspacing).

## Invite

Message par lequel le programme demande quelque chose. L'invite de la console est `>` ; INPUT peut afficher sa propre question. Voir [INPUT](05-decisions-boucles.md#input).

## LCD

Écran à cristaux liquides, comme la ligne d'affichage de la Typestar. Ce sigle vient de l'anglais « Liquid Crystal Display ». Notre écran possède 32 cases de caractères. Voir [l'écran et le clavier](07-ecran-clavier.md).

## Masque

Nombre dont les bits commandent plusieurs éléments : pixels, segments ou indicateurs. Un bit à 1 allume l'élément correspondant. Voir [LCDLINE](07-ecran-clavier.md#lcdline).

## Listing

Copie lisible d’un programme avec ses numéros de ligne. LIST la présente sur le LCD ; [LLIST](08-papier-dessins.md#llist) l’imprime sur papier.

## Matrice

Tableau à deux dimensions, semblable à un damier. Une cellule est repérée par deux indices. Voir [DIM](04-nombres-variables.md#dim).

## Mémoire RAM

Mémoire dans laquelle se trouvent votre programme et ses données de travail. Elle peut perdre son contenu après une interruption de son alimentation. Voir [MEM et FRE](03-premiers-pas.md#mem).

## Mémoire ROM

Mémoire contenant le firmware. Elle conserve son contenu sans l'alimentation de la machine ; sa programmation demande un dispositif adapté à la puce. Voir [le HD6301](02-hd6301.md).

## Microcontrôleur

Composant qui réunit un processeur, de la mémoire et des circuits pour communiquer avec le matériel. Le HD6301 de la S-70 exécute les instructions du firmware. Voir [le HD6301](02-hd6301.md).

## Modulation

Variation appliquée au fonctionnement du buzzer. SOUND module sa porte, sans choisir directement son volume ou sa fréquence propre. Voir [SOUND](09-sons-serie-memoire.md#sound).

## Octet

Groupe de huit bits. Un octet peut représenter une valeur de 0 à 255. Le BASIC mesure sa mémoire libre en octets. Voir [MEM](03-premiers-pas.md#mem).

## Opérateur et opérande

Un opérateur indique une opération ; ses opérandes sont les valeurs qu'il combine. Dans `A+3`, `+` est l'opérateur, A et 3 sont les opérandes. Voir [les priorités](04-nombres-variables.md#priorites).

## Origine

Point choisi comme référence d'un repère. ORIGIN déclare la position présente ; placez la feuille au point choisi avant de la déclarer. Voir [ORIGIN](08-papier-dessins.md#origin).

## Parité

Bit de vérification ajouté à un caractère série. Le PC et la machine doivent employer le même réglage. Voir [SERCFG](09-sons-serie-memoire.md#sercfg).

## Pixel

Petit élément visible d'un dessin. Le LCD et la tête d’impression possèdent chacun leur taille de point. Voir [LCDCHAR](07-ecran-clavier.md#lcdchar) et [GLYPH](08-papier-dessins.md#glyph).

## Programmateur

Appareil qui écrit un fichier dans une mémoire, puis relit son contenu pour le vérifier. Il faut sélectionner la référence exacte de la puce. Voir [l'installation](02-installation-firmware.md#installation).

## Programme

Suite d'instructions conservées sous des numéros de ligne et exécutées avec RUN. Voir [RUN et LIST](03-premiers-pas.md#run).

## Repère absolu et déplacement relatif

Une position absolue est donnée depuis une origine ; un déplacement relatif est donné depuis la position courante. MOVE utilise le premier principe, HEAD et FEED le second. Voir [les moteurs](08-papier-dessins.md#move).

## Scalaire

Variable simple qui contient une seule valeur, comme A ou A$. Un tableau contient plusieurs cellules. INPUT demande une variable simple ; vous pouvez ensuite copier sa valeur dans un tableau. Voir [INPUT](05-decisions-boucles.md#input).

## Série

Liaison qui transmet les bits les uns après les autres. Notre câble dispose d'un sens d'émission et d'un sens de réception. Voir [SEROPEN et SERIN](09-sons-serie-memoire.md#seropen).

## Sous-programme

Tâche appelée par GOSUB, qui revient ensuite avec RETURN. Voir [GOSUB](05-decisions-boucles.md#gosub).

## Support

Connecteur fixé sur la carte électronique, dans lequel une puce peut être retirée et remplacée sans soudure. La ROM IC8 est montée sur un support. Voir [l'installation du BASIC](02-installation-firmware.md#installation).

## Syntaxe

Règles d'écriture d'une instruction : ordre des mots, signes et paramètres. Une faute de syntaxe empêche le BASIC de reconnaître ce que vous demandez. Voir [les erreurs](10-erreurs-et-limites.md#erreurs).

## Tableau

Ensemble de cellules numériques rangées sous un même nom. Un tableau peut avoir une ou deux dimensions. Voir [DIM](04-nombres-variables.md#dim).

## Tokenisation

Remplacement interne de certains mots-clés par des codes courts pour économiser la mémoire. Vous continuez à saisir et à relire les mots habituels. Voir [la mémoire](03-premiers-pas.md#mem).

## Variable

Nom auquel le programme associe une valeur qu'il peut changer. A contient un nombre ; A$ contient une chaîne ; A(0) est une cellule de tableau. Voir [LET et DIM](04-nombres-variables.md#let).
