# Trésors et monstres

[Français](../games/tresors-et-monstres-fr.bas) · [English](../games/treasures-and-monsters-en.bas)

## Français

Un jeu de rôle pour **un à quatre joueurs**, chacun jouant à son tour sur le même clavier. Explorez un donjon, survivez aux rencontres et rapportez de l'or. Le jeu utilise le LCD ; une feuille peut servir à noter vos personnages.

### Commencer

Ouvrez le programme dans **Typestar BASIC Studio**, puis **Exécuter (F5)**, ou envoyez-le à la Canon et tapez `RUN`. Une touche passe le titre ; entrez ensuite le nombre de joueurs. L'attente au titre prépare automatiquement le hasard.

À chaque tour, **une touche** passe les trois écrans de votre personnage. Les questions attendent un nombre suivi d'**Entrée**.

| Indication | Signification |
|---|---|
| J1…J4 | Joueur auquel appartient ce tour. |
| Salle | Progression dans le donjon. |
| Vie actuelle / maximum | À zéro, le personnage meurt. |
| Vivres | Nourriture pour avancer et se soigner. |
| Force | Chances de combat et dégâts. |
| Or | Achète un passage et départage les survivants. |
| Fioles | Protègent d'un empoisonnement. |
| Monstres | Nombre de victoires au combat. |

### Avancer et se soigner

À **AVANCER 0-3**, choisissez le nombre de salles à franchir. Chaque tour apporte de un à six vivres, puis coûte **avance + 1 vivres**. Une réserve négative fait mourir le personnage de faim. Comparez donc vos réserves avant d'avancer.

Avec **0**, vous restez sur place. À **SOINS 0=NON 1=O**, répondre 1 consomme un vivre supplémentaire et rend de un à six points de vie, jusqu'au maximum du personnage. Rester immobile peut tout de même provoquer une rencontre.

### Rencontres

Les trésors apportent de la vie, des vivres, de l'or, de la force ou une fiole. Le poison retire trois points de vie ; utilisez une fiole lorsque le jeu vous le propose pour l'éviter.

Face à un monstre, choisissez **l'une des deux actions affichées** :

| Nombre | Action |
|---:|---|
| 0 | Se cacher ; en cas d'échec, le combat commence. |
| 1 | Attaquer en premier. |
| 2 | Se défendre avant de riposter. |
| 3 | Acheter le passage pour une pièce d'or. Avec une bourse vide, le combat continue. |

Orques, goules et dragons proposent 0 ou 1 ; zombies et démons proposent 2 ou 3 ; le troll propose 1 ou 3. Les dés et le combat sont automatiques. Les trolls et dragons vaincus rapportent de l'or ; chaque cinquième victoire augmente la vie maximale.

### Gagner

Le donjon contient un nombre secret de salles, de 1 à 50. Un survivant qui a franchi la sortie attend les autres. Quand tous les survivants ont terminé, **le plus riche gagne**, avec plusieurs gagnants possibles à égalité. Si tous meurent, la partie se termine sans vainqueur.

**Premier conseil :** une grande avance économise des tours, mais consomme davantage de vivres. Soignez-vous avant de prendre un risque et gardez une pièce pour une rencontre difficile.

### Origine

Adaptation pour Typestar BASIC de **Trésors et monstres**, de **Philippe Lesot**, pour **Sharp PC-1211**, publié dans **Hebdogiciel n°16, le 27 janvier 1984, page 2**. Le nom de la revue est bien *Hebdogiciel*. Cette version développe les messages et prépare automatiquement la graine aléatoire.

Sources : [numéro et sommaire numérisés](https://abandonware-magazines.org/affiche_mag.php?infos=oui&mag=7&num=1383), [scan du numéro 16](https://phenixinformatique.com/wp-content/uploads/ftp_cpcscene/Librairie/Magazines/Mags-Commercial/French/Hebdogiciel/HEBDOGICIEL_016%5BOCR%5D.pdf), [catalogue PC-1211](http://www.hebdogiciel.free.fr/PC1211.htm).

## English

A role-playing game for **one to four players**, taking turns on the same keyboard. Explore a dungeon, survive encounters and bring back gold. The game uses the LCD; a sheet of paper can help you keep track of characters. Choose the English BASIC file linked above for the following messages.

### Getting started

Open the program in **Typestar BASIC Studio**, then choose **Run (F5)**, or send it to the Canon and type `RUN`. A key passes the title; enter the number of players next. The time spent at the title automatically seeds randomness.

On each turn, **a key** passes each of the character's three status screens. Questions expect a number followed by **Enter**.

| Display | Meaning |
|---|---|
| P1…P4 | Player whose turn it is. |
| ROOM | Progress through the dungeon. |
| HP: current / maximum | At zero health, the character dies. |
| FOOD | Food for moving and healing. |
| STR | Combat chances and damage. |
| GOLD | Gold buys passage and ranks survivors. |
| VIALS | Antidotes protect against poison. |
| KILLS | Number of combat victories. |

### Moving and healing

At **ADVANCE 0-3**, choose how many rooms to advance. Each turn adds one to six food, then costs **advance + 1 food**. A negative food balance makes the character starve. Check your reserves before moving.

With **0**, you stay where you are. At **HEAL 0=NO 1=YES**, answering 1 spends one extra food and restores one to six health points, up to the character's maximum. Staying still can still trigger an encounter.

### Encounters

Treasures give health, food, gold, strength or an antidote. Poison removes three health points; use an antidote when offered to avoid it.

When facing a monster, choose **one of the two displayed actions**:

| Number | Action |
|---:|---|
| 0 | Hide; if unsuccessful, combat begins. |
| 1 | Attack first. |
| 2 | Defend before striking back. |
| 3 | Buy passage for one gold piece. With an empty purse, combat continues. |

Orcs, ghouls and dragons offer 0 or 1; zombies and demons offer 2 or 3; the troll offers 1 or 3. Dice rolls and combat are automatic. Defeated trolls and dragons yield gold; every fifth victory increases maximum health.

### Winning

The dungeon contains a secret number of rooms, from 1 to 50. A survivor who has passed the exit waits for the others. Once all survivors have finished, **the richest wins**, with shared victory possible in a tie. If everyone dies, the game ends without a winner.

**First tip:** a longer advance saves turns but uses more food. Heal before taking a risk, and keep a gold piece for a difficult encounter.

### Origin

Adapted for Typestar BASIC from **Trésors et monstres**, by **Philippe Lesot**, for **Sharp PC-1211**, published in **Hebdogiciel issue 16, 27 January 1984, page 2**. The magazine's name is *Hebdogiciel*. This version expands the messages and seeds randomness automatically.

Sources: [digitised issue and contents](https://abandonware-magazines.org/affiche_mag.php?infos=oui&mag=7&num=1383), [issue 16 scan](https://phenixinformatique.com/wp-content/uploads/ftp_cpcscene/Librairie/Magazines/Mags-Commercial/French/Hebdogiciel/HEBDOGICIEL_016%5BOCR%5D.pdf), [PC-1211 catalogue](http://www.hebdogiciel.free.fr/PC1211.htm).
