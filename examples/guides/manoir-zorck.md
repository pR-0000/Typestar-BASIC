# Le Manoir du comte Zorck / Count Zorck's Manor — Typestar BASIC

## Français

Première adaptation française, entièrement sur LCD. Ouvrir `manoir-zorck-fr.bas` dans Studio, puis exécuter dans l’émulateur ou envoyer à la Canon avec LOAD. Utiliser le firmware courant ; la validation initiale utilisait la 0.4.85-dev. Aucun papier ni changement de firmware n’est nécessaire.

### Votre mission

Vous quittez le village avec 80 à 100 points de vie. Explorez les alentours, trouvez le manoir, franchissez ses trois protections, prenez des trésors dans le donjon et revenez vivant au village. Il n’est pas nécessaire de tout ramasser : sachez rentrer avant d’épuiser vos forces ! Une touche passe les messages. La durée d’attente au titre initialise le hasard.

### Exploration

N et S vont au nord et au sud ; E et O vont à l’est et à l’ouest. Les flèches gauche et droite conviennent également. I affiche la vie et le butin, Q abandonne. Les coordonnées X,Y apparaissent après le nom du terrain ; le village est au départ, près de 0,0. Les eaux et les murs bloquent le passage. Les rencontres déclenchent un combat automatique ; le LCD indique votre vie et celle de l’adversaire.

### Les trois portes

Vous disposez de **50 essais au total** pour les trois énigmes.

1. **La porte cachée.** Cherchez deux coordonnées entières, X entre −200 et 200, Y entre −100 et 100. L’écran donne la distance à votre dernier essai. Appuyez sur une touche puis saisissez chaque coordonnée, validée par Return. Comparer plusieurs distances permet de localiser la porte ; ce n’est pas une direction à suivre sur la carte extérieure.
2. **Le mot de passe.** Proposez une lettre au clavier. Toutes ses occurrences sont révélées. Les tirets représentent les lettres manquantes. Chaque lettre proposée coûte un essai, même répétée.
3. **Le code.** Saisissez une chaîne de quatre à six chiffres **tous différents**, éventuellement commençant par zéro. BIEN indique les chiffres bien placés, MAL les chiffres présents à une autre place. Une saisie de longueur incorrecte, contenant des lettres ou des doublons est refusée sans consommer d’essai.

### Le donjon

Cinq étages, numérotés 0 à 4, partagent ce plan. Chaque coin contient un trésor gardé, récupérable une seule fois par étage. Le centre contient l’escalier.

```text
       X=1 2 3 4 5
Y=1      T . . . T
Y=2      . # . # .
Y=3      . . E . .
Y=4      . # . # .
Y=5      T . . . T
```

Utilisez le pavé numérique : 8 nord, 2 sud, 4 ouest, 6 est, 7/9/1/3 pour les diagonales. Les flèches gauche/droite fonctionnent aussi. Une diagonale ne traverse pas un coin de mur. Au centre (3,3), M monte, D descend. I affiche l’état. **5 quitte le donjon**, même loin de l’escalier, et vous dépose devant son entrée. Rejoignez ensuite le village par la carte extérieure pour gagner.

### Origine et choix d’adaptation

D’après *Le Manoir du comte Zorck*, attribué à **Pascal Prioux (1983)** dans la transcription, publié dans **Hebdogiciel n°18**. Sources : [index Sharp PC-1211](http://www.hebdogiciel.free.fr/PC1211.htm) et [archive du listing](http://www.hebdogiciel.free.fr/hd-roms/PC1211/le%20manoir%20du%20comte%20zorck%20%5BPC1211_18%5D.zip).

L’index classe le jeu sous PC-1211, tandis que le texte de présentation mentionne PC-1251. La transcription réunit plusieurs programmes, avec des erreurs et des données de donjon incomplètes. Cette version est donc une **adaptation**, pas une reproduction exacte : la carte extérieure et la liste des mots sont reprises ; les parties sont réunies sans CHAIN ; les cinq étages sont reconstruits ; les combats et les messages sont simplifiés. Le budget commun des énigmes, la recherche par distance, le mot à découvrir, le code à positions et le retour au village sont conservés. Les trésors déjà pris restent vides.

L’auteur original reste crédité ; cette adaptation ne prétend pas changer les droits sur le jeu d’origine. Les scans et archives sources ne sont pas ajoutés à la ludothèque distribuable.

### Vérification

`tools/validate_zorck.py` exécute le code sur le modèle CPU avec la ROM BASIC réelle. Des secrets déterministes et l’absence de rencontres sur la carte extérieure rendent le parcours reproductible ; le combat du gardien reste exécuté. Le rapport est produit dans `build/zorck-validation.json`. Une partie sur machine réelle reste nécessaire pour valider le confort des messages et des saisies.

Parcours automatisé réussi : trois portes, refus des codes invalides, changement d’étage, combat du gardien, trésor et retour victorieux au village. **681 octets libres au minimum observé** sur ce parcours déterministe ; ce n’est pas une garantie de minimum pour tous les tirages. La génération aléatoire d’un code à chiffres distincts a également été vérifiée séparément.

## English

First French adaptation, entirely on the LCD. Open the [French program](../games/manoir-zorck-fr.bas) in Studio, then run it in the emulator or send it to the Canon with LOAD. Use the current firmware, 0.4.85-dev in the original validation. No paper or firmware change is needed.

### Your mission

You leave the village with 80 to 100 health points. Explore the surroundings, find the manor, pass its three defences, collect treasures in the dungeon and return to the village alive. You can leave some treasure behind: return before exhausting your strength! A key passes messages. The time spent at the title seeds randomness.

### Exploration

N and S move north and south; E and O move east and west. The left and right arrows also work. I shows health and loot; Q quits. X,Y coordinates appear after the terrain name; the village is the starting point, near 0,0. Water and walls block movement. Encounters trigger automatic combat; the LCD shows your health and your opponent's.

### The three gates

You have **50 attempts in total** for the three puzzles.

1. **The hidden gate.** Find two integer coordinates: X between −200 and 200, Y between −100 and 100. The display gives the distance from your last attempt. Press a key, then enter each coordinate, confirming with Return. Comparing several distances helps locate the gate; this is separate from choosing a direction on the outdoor map.
2. **The password.** Type a letter. All its occurrences are revealed. Dashes represent missing letters. Every proposed letter costs an attempt, including repeats.
3. **The code.** Enter a string of four to six **different digits**, optionally starting with zero. BIEN counts digits in the correct position; MAL counts present digits in another position. Wrong-length input, letters or repeated digits are rejected without using an attempt.

### The dungeon

Five floors, numbered 0 to 4, share this layout. Each corner contains a guarded treasure, collectable once per floor. The stairs are in the centre.

```text
       X=1 2 3 4 5
Y=1      T . . . T
Y=2      . # . # .
Y=3      . . E . .
Y=4      . # . # .
Y=5      T . . . T
```

Use the number keys: 8 north, 2 south, 4 west, 6 east, and 7/9/1/3 for diagonals. Left/right arrows also work. Diagonal movement cannot cut through a wall corner. At the centre (3,3), M goes up and D goes down. I shows status. **5 leaves the dungeon**, even away from the stairs, and places you outside its entrance. Reach the village on the outdoor map to win.

### Origin and adaptation choices

Based on *Le Manoir du comte Zorck*, attributed to **Pascal Prioux (1983)** in the transcription, published in **Hebdogiciel issue 18**. Sources: [Sharp PC-1211 index](http://www.hebdogiciel.free.fr/PC1211.htm) and [listing archive](http://www.hebdogiciel.free.fr/hd-roms/PC1211/le%20manoir%20du%20comte%20zorck%20%5BPC1211_18%5D.zip).

The index lists the game under PC-1211, while its introduction mentions PC-1251. The transcription combines several programs, with errors and incomplete dungeon data. This version is therefore an **adaptation**, not an exact reproduction: the outdoor map and word list are retained; the parts are joined without CHAIN; five floors are reconstructed; combat and messages are simplified. The shared puzzle budget, distance search, hidden word, positional code and return to the village are preserved. Collected treasures remain empty.

The original author remains credited; this adaptation makes no claim to alter the original game's rights. Source scans and archives are not included in the distributed game collection.

### Verification

`tools/validate_zorck.py` runs the code on the CPU model with the real BASIC ROM. Deterministic secrets and the absence of outdoor encounters make the route reproducible; guardian combat still runs. The report is written to `build/zorck-validation.json`. A game on real hardware is still needed to assess message and input comfort.

The automated route passed: three gates, rejection of invalid codes, changing floors, guardian combat, treasure and a victorious return to the village. **681 free bytes was the observed minimum** on this deterministic route; this does not guarantee a minimum for every random outcome. Random generation of a code containing distinct digits was also verified separately.
