# Typestar — Duel orbital / Orbital Duel 2.0

[Programme français / French program](../games/duel-orbital-fr.bas) · [English program](../games/orbital-duel-en.bas)

## Français

Vous commandez trois formations de satellites, de **3, 2 et 2 cases**, sur une grille de 6 × 6. La Canon possède la même flotte. Le premier à toucher les sept satellites adverses gagne. Utilisez **Typestar BASIC 0.4.99-dev** et du papier thermique.

### Jouer

`RUN` lance directement le dessin. Les tableaux sont désormais accolés : **VOUS**, à gauche, contient vos satellites ; **CANON**, à droite, conserve vos tirs. Les colonnes A–F sont indiquées au-dessus de chaque moitié ; les numéros 1–6 à gauche servent aux deux tableaux.

![Duel orbital, grands glyphes — aperçu aux coordonnées nominales](images/duel-orbital-grands-glyphes.png)

Cet aperçu représente la disposition et les motifs du programme. La durée et l'alignement mécaniques se vérifient sur le papier réel.

La Canon prépare sa flotte après le dessin. Pour placer chacune des vôtres, indiquez une case de départ, comme **A1**, puis **H** pour aller vers la droite ou **V** pour aller vers le bas. Return valide chaque saisie ; les minuscules sont acceptées. Les formations occupent des cases libres et peuvent se toucher. Une saisie invalide redemande la position ou l'orientation.

Pour tirer, saisissez une case comme **B3**, puis Return. **Q** termine la partie et révèle les satellites adverses restants. Les erreurs et les tirs répétés préservent le tour. La Canon joue immédiatement après vous, puis le papier présente les deux résultats. Les règles et le ciblage adverse restent ceux de la version 1.7 : recherche autour d'une touche, puis dans son prolongement.

Un satellite représente une case occupée ; l'explosion pleine est superposée à un satellite touché ; la couronne de particules marque un tir dans le vide. Les trois dessins ont maintenant **le double de la largeur et de la hauteur**, avec les grands pixels carrés de GLYPH. Les cases gardent une marge autour des motifs. Le LCD annonce **DETRUIT** lorsqu'une formation entière est touchée. Le bilan est imprimé sous les grilles.

Laissez les moteurs conserver le repère du papier pendant la partie. Pour reprendre après BREAK ou une erreur, commencez une nouvelle partie sur une nouvelle zone.

Les satellites et les impacts utilisent désormais une palette de petits motifs en **GLYPH mode 5**. Une formation horizontale complète est imprimée en **deux passes**, avec les espaces entre ses cases conservés. Les formations verticales et les tirs isolés conservent leurs coordonnées ; chaque dessin garde exactement les pixels du modèle 16 × 16.

### Impression continue et mémoire

Les deux tableaux sont préparés **ensemble, bande par bande**. Le tableau temporaire `Q(100)` contient une palette de traits et une rangée de **37 petits motifs** : trois par case pour les douze colonnes, puis un dernier pour la **bordure droite**. `GLYPH Q(0),37,8,5` imprime toute cette rangée dans la même passe horizontale. Les bandes suivantes ajoutent les traits horizontaux au bon niveau. La bordure droite fait donc partie du dessin continu.

Les tableaux occupent seize bandes. Trois petits motifs distincts au maximum sont nécessaires par bande ; leur cache et la sauvegarde matérielle occupent jusqu'à **508 octets**. Le tableau Q utilise **514 octets**, libérés par `CLEAR` après la grille. Un second `CLEAR` prépare la création des données de jeu. Le programme reste en mémoire pendant ces deux opérations.

Les cases sont espacées de **48 unités HEAD** et **140 unités FEED**. Le tableau adverse commence 288 unités HEAD après le vôtre. Les glyphes emploient le même repère physique que la grille, pour garder les colonnes éloignées alignées.

La ligne 1600 présente la feuille à Y=1484. B/C conservent les positions Y/X et G/K les cibles ; la routine 1500 découpe les déplacements selon les limites HEAD/FEED.

La grille complète et ses treize traits verticaux sont vérifiés dans l'émulateur, jusqu'à la demande de placement des satellites. Le firmware 0.4.99 corrige aussi la boucle qui bloquait les anciens `BOX` après l'intégration des rangées de glyphes. Le temps et l'alignement du nouveau tracé restent à confirmer sur la machine réelle.

Le programme français occupe **3 850 octets tokenisés**, l'anglais **3 839**. Les tableaux de jeu B, C, H et Z utilisent **981 octets**, en-têtes compris. B conserve les flottes et les tirs, C les informations connues de la Canon, H les impacts et Z la palette des trois dessins et la rangée à imprimer.

## English

Command three satellite formations of **3, 2 and 2 cells** on a 6 × 6 grid. The Canon has the same fleet. Hit all seven enemy satellites first to win. Use **Typestar BASIC 0.4.99-dev** and thermal paper.

### Playing

`RUN` starts drawing immediately. The boards now adjoin: **YOU**, on the left, contains your satellites; **CANON**, on the right, records your shots. Columns A–F appear above each half; row numbers 1–6 at the left apply to both boards.

![Orbital Duel with large glyphs: preview at nominal coordinates, French version](images/duel-orbital-grands-glyphes.png)

This preview shows the program's layout and motifs. Mechanical timing and alignment are checked on real paper.

The Canon prepares its fleet after drawing. Place each of yours by entering a starting cell such as **A1**, then **H** for rightwards or **V** for downwards. Return confirms each entry; lowercase is accepted. Formations occupy free cells and may touch. Invalid input requests another position or orientation.

Enter a cell such as **B3**, then Return to fire. **Q** ends the game and reveals remaining enemy satellites. Invalid entries and repeated shots preserve your turn. The Canon plays immediately after you, then the paper presents both results. Rules and enemy targeting remain those of version 1.7: search around a hit, then along its direction.

A satellite marks an occupied cell; a solid explosion overprints a hit satellite; a particle ring marks a miss. All three drawings now have **twice the width and height**, using GLYPH’s large square pixels. Cells retain margins around the motifs. **DESTROYED** on the LCD identifies a fully hit formation. The final result is printed below the boards.

Let the motors preserve the paper reference during play. After BREAK or an error, start a new game on a fresh area.

Satellites and impacts now use a small-tile palette in **GLYPH mode 5**. A complete horizontal formation prints in **two passes**, preserving gaps between its cells. Vertical formations and individual shots retain their coordinates; each picture keeps the original 16 × 16 artwork exactly.

### Continuous printing and memory

Both boards are prepared **together, one band at a time**. Temporary array `Q(100)` holds a line palette and a row of **37 small tiles**: three per cell across twelve columns, followed by one for the **right border**. `GLYPH Q(0),37,8,5` prints that entire row in one horizontal sweep. Later bands insert horizontal lines at the correct height. The right border is therefore part of continuous printing.

Sixteen bands form the boards. At most three distinct tiles are needed per band; their cache and saved hardware workspace take up to **508 bytes**. Array Q uses **514 bytes**, released by `CLEAR` after the grid. A second `CLEAR` prepares for creation of game data. Both operations preserve the program in memory.

Cells are spaced **48 HEAD units** and **140 FEED units** apart. The enemy board begins 288 HEAD units after yours. Glyph placement uses the same physical coordinates as grid drawing, keeping distant columns aligned.

Line 1600 presents the paper at Y=1484. B/C retain Y/X positions and G/K hold targets; routine 1500 divides movements into HEAD/FEED limits.

The complete grid and all thirteen vertical edges are checked in the emulator, through to satellite placement. Firmware 0.4.99 also fixes the loop that blocked the former `BOX` commands after tile-row integration. Timing and alignment of the new drawing still require confirmation on real hardware.

The French program uses **3,850 tokenized bytes**, the English **3,839**. Game arrays B, C, H and Z use **981 bytes**, including headers. B stores fleets and shots, C information known to the Canon, H hits, and Z the three-picture palette and the row to print.
