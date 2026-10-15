# 3 - À vous de donner les instructions

Allumez la machine. Pendant la vérification du programme conservé en mémoire, le message `BOOTING` vous indique que le démarrage est en cours. Le nom **Typestar BASIC**, accompagné de sa version, apparaît ensuite. Appuyez sur une touche pour voir la mémoire disponible, puis sur une autre pour commencer. Avec un programme vide, vous disposez de **5 951 octets** : cet espace servira à ranger votre programme et les informations qu'il utilisera.

Le signe `>` est l'invite de commande. Il signifie : « Je suis prêt. Quelle instruction dois-je suivre ? » Dans les exemples, l’invite sert de repère. Tapez seulement ce qui est indiqué dans le cadre, puis appuyez sur **Return**.

![Printy découvre son premier résultat : quelques instructions suffisent pour commencer.](images/printy-premiers-pas.png)

## Un premier calcul

```basic
PRINT 2+3
```

La machine affiche `5`. Le mot `PRINT` lui demande d'afficher quelque chose sur son écran. Ici, ce quelque chose est le résultat d'une addition.

![Vue du LCD dans Studio : PRINT 2+3 affiche 5](images/lcd-calcul.png)

Appuyez sur une touche pour retrouver l'invite, puis essayez :

```basic
PRINT "BONJOUR"
```

Cette fois, les guillemets disent au BASIC : « Voici du texte. » La machine affiche les lettres au lieu de chercher un calcul à effectuer. À la fin d'un affichage ou d'un programme, le résultat reste visible jusqu'à l'appui sur une touche. Vous avez donc le temps de le lire.

**À vous de jouer.** Changez les deux nombres de l'addition. Essayez ensuite de faire afficher votre prénom, entre guillemets. Vous venez d'utiliser le BASIC comme une petite calculatrice et comme un panneau d'affichage.

## Se déplacer dans la ligne

Les flèches gauche et droite déplacent le curseur dans la ligne que vous préparez. Le curseur est le rectangle qui clignote à l'emplacement de la prochaine saisie. **Backspace** retire le caractère situé à sa gauche. Cela fonctionne aussi lorsque les majuscules sont verrouillées.

Pour supprimer d'un coup tout le début de la ligne, placez le curseur après ce que vous souhaitez retirer, puis utilisez **CODE + Backspace**. Les caractères situés à droite sont conservés. Pour effacer toute la ligne, placez d'abord le curseur à sa fin.

Les touches **LEFT MARGIN** et **RIGHT MARGIN** permettent de revoir, respectivement, la ligne précédente et la ligne suivante de la console. L’historique conserve huit lignes, consultables une à une sur le LCD. Pour relire le programme, utilisez `LIST`.

Dans l'éditeur BASIC, **CODE + flèche gauche** insère `<` et **CODE + flèche droite** insère `>`. Ces deux signes seront utiles pour comparer des nombres. La touche **KB - I/II** change la table de caractères du clavier.

## Interrompre un essai

La touche **MARGIN RELEASE**, en haut à gauche, joue le rôle de **BREAK**. Si un programme semble tourner sans fin, appuyez dessus. Elle sert aussi à interrompre une saisie ou certaines opérations longues. Une opération mécanique peut avoir besoin de terminer son étape en cours avant de s'arrêter.

Après une erreur ou une interruption, le texte de l'écran est effacé et le curseur retrouve son mode habituel. Le message reste affiché jusqu'à **Return**. Lorsque l'erreur se produit dans un programme, `@` est suivi du numéro de la ligne concernée : par exemple, `?SYNTAX @20` vous invite à relire la ligne 20.

Une erreur de syntaxe indique souvent un guillemet, une virgule ou une parenthèse oubliés. Elle vous invite à préciser votre instruction. Comparez tranquillement votre ligne à l'exemple, corrigez-la, puis recommencez.

<a id="run"></a>
## De l'ordre immédiat au programme : RUN

Une instruction sans numéro est exécutée tout de suite. Une instruction précédée d'un numéro est conservée pour plus tard. C'est ainsi que l'on construit un programme.

Avant de saisir un nouvel exercice, sauvegardez tout programme que vous voulez garder. L'instruction suivante efface le programme en mémoire :

```basic
NEW
```

Saisissez ensuite chaque ligne séparément :

```basic
10 PRINT "BONJOUR"
20 PRINT 6*7
30 END
```

Les lignes sont enregistrées dans l'ordre de leurs numéros. Tapez :

```basic
RUN
```

Le BASIC affiche d'abord BONJOUR, puis 42. Le LCD affichant une seule ligne, le deuxième affichage remplace le premier. Pour laisser lire chaque étape, nous apprendrons à demander une réponse ou à attendre une touche. `END` indique la fin du programme ; atteindre la dernière ligne termine aussi l'exécution.

`RUN` recommence au début et remet à zéro les variables numériques, les tableaux et les données de travail. Les variables de texte redeviennent vides. Chaque RUN prépare ainsi une nouvelle partie ou un nouveau calcul.

<a id="list"></a>
## Relire et corriger : LIST

```basic
LIST
```

`LIST` montre le programme ligne par ligne. **Return** fait apparaître la suivante ; **BREAK** quitte la lecture. Une ligne source peut être plus longue que les 32 cases visibles du LCD : le listing doit composer avec cette largeur. Studio permet de relire confortablement le texte complet sur le PC.

Vous pouvez demander seulement la ligne 20 :

```basic
LIST 20
```

Ou une plage, bornes comprises :

```basic
LIST 10,30
```

Pour remplacer une ligne, saisissez son numéro et son nouveau texte. `20 PRINT 7*8` remplace la ligne 20 et laisse les autres intactes. Pour supprimer une ligne, tapez son numéro seul : `20`. Les numéros peuvent aller de **1 à 65535**. Choisir 10, 20, 30 laisse de la place pour insérer une ligne 15.

Pour garder le programme sur papier, utilisez [LLIST](08-papier-dessins.md#llist). La sélection d’une ligne ou d’une plage suit le même principe que LIST.

<a id="new"></a>
<a id="clear"></a>
<a id="mem"></a>
<a id="fre"></a>
## Ranger la mémoire : NEW, CLEAR, MEM et FRE

`NEW` efface le programme et ses données de travail. `CLEAR` efface seulement les variables, les chaînes et les tableaux : les lignes du programme restent en place. Si vous préparez un dessin différé, imprimez-le ou annulez-le avant `CLEAR`.

`MEM` affiche le nombre d'octets disponibles. Un **octet** est une petite unité de mémoire. Pour utiliser ce nombre dans un calcul, demandez-le avec la fonction `FRE(0)` :

```basic
PRINT FRE(0)
```

Le programme et les variables partagent les 5 951 octets disponibles à vide. Les mots-clés usuels sont rangés sous une forme abrégée, appelée **token**, et les numéros de ligne sur deux octets. Vous saisissez toujours les mots habituels : `LIST` et `SAVE` vous rendent le texte habituel.

L'ajout, la suppression ou la modification acceptée d'une ligne réinitialise les variables. Gardez donc vos valeurs initiales dans le programme, par des affectations ou des instructions `DATA`, plutôt que de compter sur un ancien calcul fait au clavier.

Le firmware vérifie le programme conservé au redémarrage. La RAM alimentée conserve le programme ; une sauvegarde sur PC offre une copie durable. Les variables sont recréées à l’exécution. Cette version gère un programme à la fois dans la mémoire de la machine.

## Comment lire les exemples

Les mots-clés sont écrits en majuscules pour être faciles à repérer. Les virgules, parenthèses, guillemets et points-virgules montrés dans un exemple font partie de l'instruction. Dans une description de syntaxe, les noms comme `nombre` ou `colonne` indiquent ce que vous devez remplacer par votre propre valeur.

Les crochets signalent une partie facultative. Ainsi, `BEEP [duree]` signifie que l'on peut écrire `BEEP` ou `BEEP 200`. Tapez directement la forme choisie, comme `BEEP 200`. Tous les programmes encadrés ci-dessous sont des exercices distincts : utilisez `NEW` avant d'en saisir un autre, après avoir sauvegardé ce que vous souhaitez garder.
