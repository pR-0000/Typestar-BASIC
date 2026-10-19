# Typestar — Duel orbital / Orbital Duel 1.8

[Programme français / French program](../games/duel-orbital-fr.bas) · [English program](../games/orbital-duel-en.bas)

## Français

Vous commandez trois formations de satellites, de **3, 2 et 2 cases**, sur une grille de 6 × 6. La Canon possède la même flotte. Le premier à toucher les sept satellites adverses gagne. Utilisez **Typestar BASIC 0.4.93-dev** et du papier thermique.

### Jouer

`RUN` lance directement le dessin. Les tableaux sont désormais accolés : **VOUS**, à gauche, contient vos satellites ; **CANON**, à droite, conserve vos tirs. Les colonnes A–F sont indiquées au-dessus de chaque moitié ; les numéros 1–6 à gauche servent aux deux tableaux.

![Duel orbital, grands glyphes — aperçu aux coordonnées nominales](images/duel-orbital-grands-glyphes.png)

Cet aperçu représente la disposition et les motifs du programme. La durée et l'alignement mécaniques se vérifient sur le papier réel.

La Canon prépare sa flotte après le dessin. Pour placer chacune des vôtres, indiquez une case de départ, comme **A1**, puis **H** pour aller vers la droite ou **V** pour aller vers le bas. Return valide chaque saisie ; les minuscules sont acceptées. Les formations occupent des cases libres et peuvent se toucher. Une saisie invalide redemande la position ou l'orientation.

Pour tirer, saisissez une case comme **B3**, puis Return. **Q** termine la partie et révèle les satellites adverses restants. Les erreurs et les tirs répétés préservent le tour. La Canon joue immédiatement après vous, puis le papier présente les deux résultats. Les règles et le ciblage adverse restent ceux de la version 1.7 : recherche autour d'une touche, puis dans son prolongement.

Un satellite représente une case occupée ; l'explosion pleine est superposée à un satellite touché ; la couronne de particules marque un tir dans le vide. Les trois dessins ont maintenant **le double de la largeur et de la hauteur**, avec le mode `GLYPH 4`. Les cases gardent une marge autour des motifs. Le LCD annonce **DETRUIT** lorsqu'une formation entière est touchée. Le bilan est imprimé sous les grilles.

Laissez les moteurs conserver le repère du papier pendant la partie. Pour reprendre après BREAK ou une erreur, commencez une nouvelle partie sur une nouvelle zone.

### Impression continue et mémoire

Les deux tableaux sont préparés **ensemble, bande par bande**. Une matrice temporaire `Q(7,23)` décrit un fragment de case. `GLYPH Q(0,0),24,8,4,12` répète ce fragment pour les **douze colonnes dans la même passe horizontale**. Le firmware prépare un seul fragment, puis réutilise son tampon pour les copies. Les bandes suivantes ajoutent les traits horizontaux au bon niveau. Le bord droit est fermé par deux bandes verticales `BOX` étroites.

Les tableaux occupent seize bandes. Chaque fragment utilise trois blocs natifs ; le tampon d'impression et la sauvegarde matérielle occupent **412 octets**, quel que soit le nombre de répétitions. La matrice utilise **969 octets**, libérés par `CLEAR` après la grille. Un second `CLEAR` libère la composition graphique avant la création des données de jeu. Le programme reste en mémoire pendant ces deux opérations.

Les cases sont espacées de **48 unités HEAD** et **140 unités FEED**. Le tableau adverse commence 288 unités HEAD après le vôtre. Le placement des glyphes emploie les mêmes coordonnées physiques que le tracé : les colonnes éloignées conservent leur alignement.

La présentation du papier à la ligne 1600 utilise Y=1484. L'espace entre le bas du dessin et la position de lecture diminue de **448 unités FEED**, soit un grand segment de mouvement. La hauteur absolue tient compte de l'agrandissement du tableau. B/C conservent les positions Y/X et G/K les cibles ; la routine 1500 découpe chaque mouvement dans les limites HEAD/FEED.

La mise en commun réduit les préparations et les retours entre tableaux. Le dessin et le jeu ont été validés sur machine. Les grands dessins augmentent aussi la surface imprimée ; le gain de temps reste à mesurer précisément. Les vérifications dans l'émulateur portent sur une vraie bande de douze colonnes, les seize phases de la matrice, la libération du tampon et le placement du grand glyphe en colonne F.

Le programme français occupe **3 828 octets tokenisés**, l'anglais **3 817**. Les tableaux de jeu B, C, H et Z utilisent **856 octets**, en-têtes compris. B conserve les flottes et les tirs, C seulement les informations connues de la Canon, H les impacts et Z les trois bitmaps.

## English

Command three satellite formations of **3, 2 and 2 cells** on a 6 × 6 grid. The Canon has the same fleet. Hit all seven enemy satellites first to win. Use **Typestar BASIC 0.4.93-dev** and thermal paper.

### Playing

`RUN` starts drawing immediately. The boards now adjoin: **YOU**, on the left, contains your satellites; **CANON**, on the right, records your shots. Columns A–F appear above each half; row numbers 1–6 at the left apply to both boards.

![Orbital Duel with large glyphs: preview at nominal coordinates, French version](images/duel-orbital-grands-glyphes.png)

This preview shows the program's layout and motifs. Mechanical timing and alignment are checked on real paper.

The Canon prepares its fleet after drawing. Place each of yours by entering a starting cell such as **A1**, then **H** for rightwards or **V** for downwards. Return confirms each entry; lowercase is accepted. Formations occupy free cells and may touch. Invalid input requests another position or orientation.

Enter a cell such as **B3**, then Return to fire. **Q** ends the game and reveals remaining enemy satellites. Invalid entries and repeated shots preserve your turn. The Canon plays immediately after you, then the paper presents both results. Rules and enemy targeting remain those of version 1.7: search around a hit, then along its direction.

A satellite marks an occupied cell; a solid explosion overprints a hit satellite; a particle ring marks a miss. All three drawings now have **twice the width and height**, using `GLYPH 4`. Cells retain margins around the motifs. **DESTROYED** on the LCD identifies a fully hit formation. The final result is printed below the boards.

Let the motors preserve the paper reference during play. After BREAK or an error, start a new game on a fresh area.

### Continuous printing and memory

Both boards are prepared **together, one band at a time**. A temporary `Q(7,23)` matrix describes a cell fragment. `GLYPH Q(0,0),24,8,4,12` repeats it across **all twelve columns in one horizontal sweep**. The firmware prepares one fragment, then reuses its buffer for the copies. Later bands insert horizontal lines at the correct height. Two narrow vertical `BOX` sections close the right border.

Sixteen bands form the boards. Each fragment uses three native blocks; the print buffer and saved hardware workspace take **412 bytes**, regardless of repeat count. The matrix uses **969 bytes**, released by `CLEAR` after the grid. A second `CLEAR` releases the graphics composition before the game data is created. Both operations preserve the program in memory.

Cells are spaced **48 HEAD units** and **140 FEED units** apart. The enemy board begins 288 HEAD units after yours. Glyph placement uses the same physical coordinates as grid drawing, keeping distant columns aligned.

Line 1600 presents the paper at Y=1484. The gap between the drawing's bottom and its reading position is reduced by **448 FEED units**, one large movement segment. The absolute position accounts for the enlarged boards. B/C retain Y/X positions and G/K hold targets; routine 1500 divides each movement into HEAD/FEED limits.

Sharing bands reduces preparation and returns between boards. Drawing and gameplay have been validated on hardware. Larger artwork also increases printed area; the time saving still needs precise measurement. Emulator checks cover a real twelve-column band, all sixteen matrix phases, buffer release and placement of the large glyph in column F.

The French program uses **3,828 tokenized bytes**, the English **3,817**. Game arrays B, C, H and Z use **856 bytes**, including headers. B stores fleets and shots; C stores only information known to the Canon; H stores hits and Z the three bitmaps.
