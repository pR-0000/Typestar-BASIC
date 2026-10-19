# Le trésor 4 × 4 / The 4 × 4 treasure

[Programme français / French program](../games/game-treasure-fr.bas)

## Français

Trouvez un trésor caché dans une grille de **quatre colonnes et quatre lignes** avec **trois vies**. Certaines cases contiennent un piège, qui retire une vie ; les autres sont vides ou cachent le trésor.

Lancez avec F5 ou `RUN`. À **X 1-4,0=FIN**, entrez la colonne puis **Entrée**, ensuite la ligne de 1 à 4. Vous pouvez fouiller n'importe quelle case. Une touche passe le résultat. Notez vos recherches sur une grille dessinée à la main : une case déjà visitée préserve le compteur de coups.

Le trésor gagne immédiatement la partie ; trois pièges la font perdre. **0**, à la question de colonne, permet de terminer. La carte est **fixe** : rejouer sert aussi à apprendre ses positions.

Les seize valeurs DATA, lues de gauche à droite puis de haut en bas, décrivent les cases : **0 vide, -1 piège, 9 trésor**. Changez-les pour créer une carte à faire découvrir à un ami. Le programme montre les tableaux à deux dimensions, `DATA`, `READ`, `INPUT` et les conditions.

## English

Find a treasure hidden in a **four-column, four-row grid** with **three lives**. Some cells contain a trap, costing one life; the others are empty or hold the treasure. The supplied program is in French.

Start with F5 or `RUN`. At **X 1-4,0=FIN**, enter the column followed by **Enter**, then a row from 1 to 4. You may search any cell. A key passes the result. Record your searches on a hand-drawn grid: searching an already visited cell preserves the move count.

Finding the treasure wins immediately; three traps lose the game. Enter **0** at the column prompt to finish. The map is **fixed**: playing again also helps you learn its positions.

The sixteen DATA values, read left to right and then top to bottom, describe the cells: **0 empty, -1 trap, 9 treasure**. Change them to make a map for a friend. The program demonstrates two-dimensional arrays, `DATA`, `READ`, `INPUT` and conditions.
