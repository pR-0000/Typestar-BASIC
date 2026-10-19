# Château / Castle — Typestar BASIC 1.0

## Français

Adaptation LCD du jeu d’**Alain Dubus**, publié dans **Hebdogiciel n°20** pour le Sharp PC-1211. Ouvrir `chateau-fr.bas` dans Studio, puis lancer l’émulateur ou envoyer le programme à la Canon avec LOAD. Aucun changement de firmware ni papier nécessaire.

### Sauvez la reine !

Vous commencez en salle 1 avec 100 pièces d’or. La reine est prisonnière dans une des 35 autres salles. Trouvez-la puis ramenez-la en salle 1. Le mot REINE apparaît dans l’état affiché lorsqu’elle vous accompagne.

Chaque déplacement valide coûte **8 pièces**, même pour revenir sur vos pas. À moins de zéro pièce, la partie est perdue ; zéro reste autorisé. La carte est un carré de six salles de côté :

```text
 1  2  3  4  5  6
 7  8  9 10 11 12
13 14 15 16 17 18
19 20 21 22 23 24
25 26 27 28 29 30
31 32 33 34 35 36
```

| Action | Touches |
|---|---|
| Nord | 8 ou N |
| Sud | 2 ou S |
| Ouest | Flèche gauche, 4 ou O |
| Est | Flèche droite, 6 ou E |
| Abandonner depuis l’écran de salle | Q |
| Passer un message | Une touche quelconque |

Maintenez les directions seulement le temps d’un déplacement : il faut relâcher puis appuyer pour avancer à nouveau. La salle et l’or restent affichés jusqu’à votre prochaine action. La durée d’attente au titre initialise le hasard, puis les treize rencontres sont placées sans chevauchement, hors de la salle 1. Elles restent aux mêmes endroits durant la partie.

### Les rencontres

- **Ours, ogre, lion, Dracula, dragon** : C combat, F fuite. Un combat a 60 % de chances d’être gagné. Il rapporte respectivement 20, 25, 30, 35 ou 40 pièces ; une défaite fait perdre cette somme. Fuir coûte 10 pièces. Un monstre vaincu disparaît ; après fuite ou défaite, il pourra vous affronter lors d’une prochaine visite. Vous restez dans la salle et pouvez ensuite choisir votre direction.
- **Trésor et rubis** : rapportent 60 et 50 pièces, une seule fois.
- **Reine** : elle vous accompagne désormais ; retournez à l’entrée.
- **Deux catapultes** : vous projettent dans une salle de 2 à 36. L’atterrissage coûte lui aussi 8 pièces et déclenche l’éventuelle rencontre de destination. Chaque catapulte ne fonctionne qu’une fois.
- **Deux coffres** : contiennent de 10 à 59 pièces. Avec un tirage inférieur à 15, le coffre explose et vous perdez deux fois ce montant. Un coffre ne peut être ouvert qu’une fois.
- **Informateur** : O accepte, N refuse. Il révèle la salle de la reine, mais vous facture ensuite une somme aléatoire, pouvant prendre tout votre or ! Il ne propose son service qu’une fois. Si la reine vous accompagne déjà, il ne vous fait rien payer.

Prenez note mentalement des salles visitées. Le trajet le plus court vers la reine ne suffit pas toujours : il faut également financer le retour. Les rencontres peuvent vous enrichir ou compromettre toute l’expédition.

### Adaptation et provenance

Sources : [index Hebdogiciel PC-1211](http://www.hebdogiciel.free.fr/PC1211_1.htm), [listing et notice de Château](http://www.hebdogiciel.free.fr/hd-roms/PC1211/HEB20_Chateau.zip). L’auteur original est Alain Dubus ; cette adaptation ne change pas les droits sur le jeu d’origine.

Les règles, montants et treize rencontres sont repris. Les particularités du Sharp (variables utilisées comme tableau, sauts calculés, générateur pseudo-aléatoire maison, SHIFT en mode DEF) sont remplacées par les fonctions de Typestar BASIC. Les coquilles de transcription sont corrigées. Contrairement au listing, aller à l’est de la salle 6 ne conduit pas à la salle 7 : les quatre bords du carré sont bien des murs. L’insolvabilité est vérifiée avant la victoire, et les messages restent lisibles jusqu’à une touche. Les sons du listing ne sont pas repris dans cette première version.

### Taille et validation

Le programme utilise **2 140 octets tokenisés**, laissant **3 811 octets avant allocation des variables**. `tools/validate_chateau.py` exécute des scénarios déterministes avec la ROM BASIC dans le modèle CPU : retour avec la reine, murs, combat gagné, fuite et défaite, trésors, coffre, informateur, catapulte, explosion et manque d’or. Les positions et certains tirages sont imposés uniquement dans le test ; le jeu distribué reste aléatoire. Le rapport est enregistré dans `build/chateau-validation.json`. Le confort d’utilisation reste à confirmer sur machine réelle.

Les quatre scénarios passent : sauvetage, fuite/défaite, catapulte/explosion et insolvabilité. Le minimum observé est de 3 501 octets libres sur les scénarios testés (avant le dernier raccourcissement cosmétique du message de défaite).

## English

LCD adaptation of **Alain Dubus's** game, published in **Hebdogiciel issue 20** for the Sharp PC-1211. Open the [French program](../games/chateau-fr.bas) in Studio, then run the emulator or send it to the Canon with LOAD. It requires no firmware change or paper.

### Rescue the queen!

You start in room 1 with 100 gold pieces. The queen is imprisoned in one of the other 35 rooms. Find her, then bring her back to room 1. REINE appears in the status display when she accompanies you.

Every valid move costs **8 gold pieces**, including retracing your steps. A balance below zero loses the game; zero is allowed. The map is a square six rooms on each side:

```text
 1  2  3  4  5  6
 7  8  9 10 11 12
13 14 15 16 17 18
19 20 21 22 23 24
25 26 27 28 29 30
31 32 33 34 35 36
```

| Action | Keys |
|---|---|
| North | 8 or N |
| South | 2 or S |
| West | Left arrow, 4 or O |
| East | Right arrow, 6 or E |
| Quit from the room screen | Q |
| Pass a message | Any key |

Hold a direction only long enough for one move: release and press again to move once more. Your room and gold remain visible until the next action. Time spent at the title seeds randomness, then the thirteen encounters are placed without overlap, outside room 1. Their locations remain fixed for the game.

### Encounters

- **Bear, ogre, lion, Dracula, dragon:** C fights, F flees. A fight has a 60% chance of success. Victory gains 20, 25, 30, 35 or 40 gold respectively; defeat loses that amount. Fleeing costs 10 gold. A defeated monster disappears; after fleeing or losing, it can confront you on a later visit. You remain in the room and can then choose a direction.
- **Treasure and ruby:** give 60 and 50 gold, once each.
- **Queen:** she now accompanies you; return to the entrance.
- **Two catapults:** throw you into a room from 2 to 36. Landing also costs 8 gold and triggers any encounter at the destination. Each catapult works once.
- **Two chests:** contain 10 to 59 gold. If the random amount is below 15, the chest explodes and you lose twice that amount. Each chest can be opened once.
- **Informant:** O accepts, N refuses. He reveals the queen's room, then charges a random amount that can take all your gold! He offers the service once. If the queen already accompanies you, he charges nothing.

Keep track of visited rooms. The shortest route to the queen may be insufficient: you also need to fund the return journey. Encounters may enrich you or jeopardise the entire expedition.

### Adaptation and provenance

Sources: [Hebdogiciel PC-1211 index](http://www.hebdogiciel.free.fr/PC1211_1.htm), [Château listing and instructions](http://www.hebdogiciel.free.fr/hd-roms/PC1211/HEB20_Chateau.zip). The original author is Alain Dubus; this adaptation does not alter the original game's rights.

The rules, amounts and thirteen encounters are retained. Sharp-specific techniques (variables used as an array, computed jumps, a home-made pseudorandom generator and SHIFT in DEF mode) are replaced with Typestar BASIC features. Transcription errors are corrected. Unlike the listing, moving east from room 6 does not lead to room 7: all four edges of the square are walls. Insolvency is checked before victory, and messages remain readable until a key is pressed. The listing's sounds are not included in this first version.

### Size and validation

The program uses **2,140 tokenized bytes**, leaving **3,811 bytes before variable allocation**. `tools/validate_chateau.py` runs deterministic scenarios using the BASIC ROM in the CPU model: returning with the queen, walls, won combat, fleeing and losing, treasures, chests, the informant, catapults, explosions and running out of gold. Positions and some random outcomes are imposed only in the test; the distributed game remains random. The report is saved in `build/chateau-validation.json`. Ease of use still needs confirmation on real hardware.

All four scenarios pass: rescue, fleeing/losing, catapult/explosion and insolvency. The observed minimum is 3,501 free bytes in the tested scenarios, before the final cosmetic shortening of the defeat message.
