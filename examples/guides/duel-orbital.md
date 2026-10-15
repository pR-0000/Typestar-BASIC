# Typestar — Duel orbital 1.5

Programme : [Français](../duel-orbital-fr.bas), [English](../orbital-duel-en.bas). Utilisez le firmware courant et du papier thermique.

Vous commandez trois formations de satellites, de 3, 2 et 2 cases, sur une grille de 6 × 6. La Canon possède la même flotte et choisit ses tirs en fonction des résultats précédents. Le premier à toucher les sept satellites adverses gagne.

## Jouer

Appuyer sur Return à l’accueil. Pour chaque formation, saisir sa case de départ (par exemple A1), puis H pour horizontal vers la droite ou V pour vertical vers le bas. Valider chaque saisie avec Return ; les minuscules sont acceptées. Une formation ne doit ni dépasser du tableau ni en recouvrir une autre ; les formations peuvent se toucher. Une saisie invalide redemande la position ou l’orientation.

La grille **de gauche** contient vos satellites ; celle **de droite** conserve vos tirs. Les colonnes sont A à F, les lignes 1 à 6. Saisir une case telle que B3, puis Return. Q termine la partie et révèle les satellites adverses restants. Les erreurs de saisie et les tirs répétés ne consomment pas un tour.

Le satellite indique une case occupée. Une explosion pleine indique un impact ; à gauche, elle se superpose au satellite. Une couronne de particules signale un tir dans le vide. Les deux motifs sont définis dans le programme, en mode GLYPH 3. Lorsqu’une formation entière est détruite, le LCD annonce DETRUIT. Il n’y a aucune confirmation après les tirs : la Canon joue puis présente les deux résultats sur le papier. L’état final est imprimé sous les grilles.

Ne pas déplacer le papier à la main pendant la partie. Les coordonnées sont suivies par logiciel, sans capteur d’origine. Après BREAK ou une erreur, recommencer sur une nouvelle zone. La présentation est faite une seule fois par tour pour limiter les allers-retours.

## Dessin et programmation

Chaque grille est découpée en huit bandes de 32 unités logiques Y, soit les 16 rangées natives d'une passe. Une scène DRAW DEFERRED ne contient que les sept petits traits verticaux de sa bande et, si nécessaire, un trait horizontal. DRAW PRINT imprime cette bande avant de passer à la suivante. La dernière contient les 17 dernières unités logiques de la grille ; son avance complète est conservée. Cela évite de recalculer les traits de toute la grille pour chaque tuile. Les abscisses fixes sont écrites directement, et la position du prochain trait horizontal avance par additions ; les boucles de recherche et multiplications répétées ont été supprimées. Aucun cache supplémentaire ni modification de firmware n'est nécessaire.

Les deux grilles dépassent la largeur maximale d'une scène : elles restent deux impressions successives, afin de ne pas multiplier les retours papier. La géométrie reste identique : cases de 40 unités, contour de 240 unités, huit avances de 56 unités moteur par grille. Titres, labels, sprites, coordonnées de tir et interligne sont conservés. Les trois motifs sont définis dans les DATA hexadécimaux du jeu. GLYPH 3 double les colonnes pour obtenir des proportions approximativement carrées.

| Lignes | Fonction |
|---|---|
| 10–90 | Accueil, graine liée au délai du joueur, flotte adverse |
| 100–210 | Placement des formations au clavier |
| 220–390 | Tours, saisies et doublons |
| 400–480 | Révélation et résultat |
| 600–660 | Validation et enregistrement d’une formation |
| 700–762 | Arbitrage, sprites de tir, son |
| 800–920 | Saisie du placement et lecture clavier |
| 1000–1120 | Choix du tir adverse |
| 1200–1330 | Glyphes, deux grilles LINE, coordonnées imprimées |
| 1400–1410 | Position du glyphe dans une case |
| 1500–1580 | Déplacements bornés et suivi des positions |
| 1600 | Présentation du papier |
| 1700–1752 | Bitmaps satellite, raté et impact |

B(0,case) et B(1,case) sont les flottes : 0 représente le vide, 1–3 une formation ; un tir ajoute 4. C(case) contient seulement les informations publiques connues de l’adversaire : inconnu, raté, touche ou formation détruite. H compte les impacts. La recherche adverse (1000–1120) ne lit jamais B : elle privilégie les voisins d’une touche puis le prolongement de deux touches alignées, sinon elle choisit une case inconnue.

Les variables numériques B/C suivent Y/X sur le papier, G/K sont les cibles X/Y. Elles sont indépendantes des tableaux de mêmes noms. La routine 1500 découpe les mouvements dans les limites HEAD/FEED et déclare la position avec ORIGIN. Le mode GLYPH 3 avance de 56 unités moteur ; une grille haute de 241 points logiques occupe huit bandes, soit 448 unités moteur. Ces avances sont explicitement comptabilisées. Les mouvements ne dépendent pas d’un arrondi accumulé des coordonnées graphiques.

## Présentation de la feuille

La ligne 1600 place maintenant la feuille à Y=1428 au lieu de 756, soit 672 unités moteur supplémentaires (douze avances de glyphe). Cette avance vise à dégager le terrain d’environ quelques centimètres ; la conversion exacte en millimètres n’est pas calibrée. Le retour au terrain est calculé depuis cette position, sans modifier les coordonnées des cases. Pour ajuster la hauteur après essai, modifier uniquement la constante 1428 à la ligne 1600. La routine découpe automatiquement les mouvements en portions de 448 unités maximum.

## Mémoire et validation 1.5

Programme : [Français](../duel-orbital-fr.bas), [English](../orbital-duel-en.bas). Utilisez le firmware courant et du papier thermique.

`tools/validate_orbital_grid.py` compare une grille complète avec la 1.4 sur la ROM .87 : les **2 485 points natifs**, les 64 impressions de tuiles, la pile et la position finale sont identiques. L'aperçu ne présente aucun raccord manquant. Le travail passe de **10 464 623 à 4 835 783 étapes du cœur**, soit **54 % de moins**, avec les mêmes raccourcis raster actifs pour les deux versions. Ces étapes ne sont pas des cycles matériels. Le temps PC observé passe de 116 à 39 secondes, mais dépend de la charge du PC ; le gain réel sur Canon reste à mesurer. Rapport : `build/naval-duel/grid-validation.json`, aperçu : `grid-1.5.png`.

La réduction porte sur les calculs BASIC et raster ; les mouvements et la quantité imprimée ne changent pas. Charger simplement le nouveau programme, sans reflasher la ROM. Pour l'essai matériel, vérifier les deux grilles, leurs raccords et le placement d'un satellite, puis un impact superposé.

Les scénarios de logique exécutés séparément, sans sorties papier, passent : victoire 7–3, défaite 0–7, refus de placements invalides et quatre situations de ciblage adverse (voisin, alignement, bord, dernière case). Ils vérifient la logique inchangée du jeu ; le nouveau dessin est contrôlé par la comparaison de grille ci-dessus.
