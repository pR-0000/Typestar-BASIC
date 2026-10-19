# Duel balistique / Ballistic Duel 0.6

## Français

Jeu d’artillerie sur papier pour Typestar BASIC. Une arène est imprimée au début de la partie ; chaque tir ajoute sa trajectoire et son impact sur cette même arène. Le relief et les canons restent fixes : il n’y a plus de cratères, pour éviter de confondre le sol actuel avec des contours impossibles à effacer.

### Jouer

Ouvrir `duel-balistique-fr.bas` dans Typestar BASIC Studio ou le charger sur la Canon. Firmware utilisé pour la vérification : **0.4.86-dev**. Cette version redemande les réponses numériques vides ou invalides au lieu d’arrêter le programme. Le dessin ×2 reste compatible avec la .85, mais elle ne possède pas cette correction d’INPUT.

Entrer une graine de 1 à 9999, puis **1** pour jouer contre la Canon ou **2** pour deux joueurs. J1 est à gauche, J2 à droite. Chacun vise vers son adversaire : angle de **10 à 80 degrés**, puissance de **20 à 100**. Un angle de **0** termine la partie. Les deux joueurs commencent avec 100 points de vie. L’adversaire informatique choisit ses tirs au hasard.

Pour un essai reproductible : graine **42**, mode **2**, puis angle **45**, puissance **90** pour chaque joueur. Les deux trajectoires en pointillés doivent se superposer au même terrain, sans nouvelle vignette. Une petite croix marque chaque impact au sol. La feuille avance après chaque tir pour rendre le résultat visible ; ne pas modifier manuellement sa position pendant la partie. Les vies restent sur le LCD.

Sous le terrain, chaque tir ajoute une ligne telle que `TIR 3 J1 ANGLE 45 PUISSANCE 90`. L’angle et la puissance saisis sont conservés avant les calculs, y compris leurs décimales ; les tirs de l’adversaire informatique sont consignés également. Les anciennes lignes restent sur papier. L’interligne vaut une ligne et demie. L’historique commence sous le relief le plus haut possible et descend progressivement ; la feuille avance davantage lorsque la dernière entrée le nécessite. Prévoir assez de papier pour les longues parties : le jeu n’effectue pas de pagination ni de changement de feuille automatique.

Un bref signal ascendant accompagne un tir qui endommage l’adversaire ; un tir raté ou qui ne blesse que son propre canon reste silencieux. Trois notes marquent la fin de la partie lorsque les vies d’un joueur atteignent zéro. La sortie volontaire avec un angle nul reste silencieuse. Ces sons utilisent la modulation SOUND du buzzer existant.

Préférer du papier thermique. Après BREAK, une erreur ou une manipulation manuelle de la feuille, recommencer sur une zone vierge : le jeu suit les déplacements commandés, il n’a pas de capteur de position absolue. La précision des superpositions dépend toujours du mécanisme papier ; la calibration Y expérimentale reste un sujet séparé.

### Accélérations

- **Un terrain par partie.** La scène initiale contient 16 segments de sol et quatre formes pour les canons. Le terrain reste inchangé ensuite.
- **Trajectoires en pointillés.** Neuf petits carrés pleins de 4×4 unités logiques remplacent les dix segments : ils occupent **4 colonnes ×2 rangées natives**, contre 2×1 dans la .4, soit le double de largeur et de hauteur. Ils utilisent BOX plutôt que POINT pour découper proprement ceux qui traversent une limite de zone ; aucun fragment n’est supprimé au raccord. Deux petits LINE forment la croix d’impact, à la place du cercle. Le canon matérialise le départ ; il n’est pas réimprimé pour fermer les pointillés. Les points sont calculés une seule fois, puis conservés dans deux tableaux pour être répartis entre les zones imprimables.
- **Suppression des bandes vides en tête de dessin.** Le jeu déplace directement la feuille jusqu’à la première bande utile, puis soustrait son décalage aux coordonnées. Ce décalage est un multiple de 32 unités Y BASIC, soit 16 rangées natives, pour conserver la même grille de pixels entre passages. La scène initiale bénéficie aussi de ce recadrage.
- **Petite table trigonométrique.** Dix-neuf valeurs de sinus en millièmes, espacées de 5°, remplacent les appels à SIN/COS. Une interpolation conserve les angles intermédiaires, y compris décimaux. Le cosinus utilise la même table en sens inverse.
- **Progression par additions.** À intervalles de temps égaux, X augmente d’une constante ; l’incrément de Y augmente lui aussi d’une constante. Le jeu utilise cette propriété pour parcourir le relief et placer les points, au lieu de refaire divisions et produits à chaque étape.
- **Aucune racine carrée.** Sur le segment touché, cinq subdivisions de l’intervalle recherchent l’impact. Les dégâts utilisent également une distance approchée, décrite ci-dessous.

Les calculs restants passent toujours par l’interpréteur et les routines décimales de la ROM : écrire des constantes entières ne transforme pas le BASIC en interpréteur entier rapide. La conversion des formes en pixels et les moteurs prennent aussi du temps. Les mesures d’émulation sont comparatives ; ce ne sont pas des durées promises sur machine réelle.

### Géométrie et physique

La simulation conserve X=0..240 et Y=0..220. **Le rendu double les deux axes** : terrain, canons, trajectoires et croix d’impact occupent deux fois la largeur et la hauteur précédentes. Le titre conserve sa taille normale. Les positions et dégâts sont calculés dans les anciennes coordonnées ; l’agrandissement ne change pas les règles ni la portée.

Chaque composition du firmware est limitée à X=0..247 et Y=0..255. Le jeu découpe donc le dessin en deux zones horizontales de 248 unités et, si nécessaire, deux zones verticales. Le raccord horizontal correspond à huit tuiles et à un déplacement HEAD de 128 unités moteur. Les zones verticales commencent sur une frontière de bande ; une zone vide est annulée sans impression. Les traits de sol et d’impact qui traversent une frontière sont découpés. Aucun effacement du terrain ni recalcul de la trajectoire n’est nécessaire.

Le pilote convertit Y en `INT(Y/2)`. Les unités logiques ont des longueurs physiques approximativement égales ; les points natifs sont environ deux fois plus hauts que larges. Il s’agit d’un agrandissement des coordonnées géométriques, pas d’une duplication pixel par pixel ; les traits très fins restent soumis à cette quantification. Les 17 sommets du relief, espacés de 15 unités de simulation, ont des hauteurs entre 120 et 180. Deux plateformes portent les canons aux abscisses 30 et 210.

La trajectoire conserve la forme `X=B(S)+U*T`, `Y=Z-V*T+T*T`, avec une vitesse initiale voisine de `P/5` et une gravité de 2. U et V utilisent maintenant la table interpolée : la portée à hauteur égale reste proche de 200 unités à puissance 100 et angle 45°, mais les résultats ne sont plus strictement identiques à ceux des SIN/COS du firmware. Les neuf points se situent à 10 %, 20 %, …, 90 % du temps de vol ; la sortie latérale reçoit un dernier point, l’impact au sol une croix.

Sur chaque segment de terrain, la différence entre la hauteur du projectile et celle du sol est une fonction quadratique convexe. Tant que cette différence reste négative aux deux extrémités traversées, il n’y a pas de collision entre elles. Au premier sommet atteint sous le sol, cinq subdivisions conservent l’encadrement de l’intersection. Le milieu final donne une erreur horizontale théorique maximale de `15/64 = 0,234375` unité pour **cette même parabole approchée**, hors arrondis BASIC. Cette borne n’inclut pas la différence avec l’ancienne trigonométrie. La hauteur d’impact est interpolée sur le terrain afin de placer la croix sur son contour. Le raisonnement dépend du départ au-dessus du sol, de la progression horizontale monotone et du relief sans cavernes.

Un impact au sol situé à six unités horizontales et huit unités verticales au plus de la base du canon inflige **100 dégâts** : un coup direct suffit désormais à gagner contre un canon intact. Ces tolérances utilisent les coordonnées de simulation, avant le rendu ×2. Elles accordent une marge autour du canon ; il ne faut pas viser un pixel précis. En dehors de cette zone, les dégâts valent `INT(100-3*distance)`, bornés à zéro, avec `distance=max(dx,dy)+3*min(dx,dy)/8`. Un joueur peut se blesser lui-même selon les mêmes règles. Les sorties de terrain sans impact ne causent aucun dégât. Il n’y a pas de vent ni de déplacement des joueurs.

La version précédente plafonnait à 60 dégâts : même un tir centré ne pouvait pas détruire un canon neuf. Les tests ROM de `tools/validate_ballistic_damage.py` contrôlent le centre, les limites incluses, les dégâts proches, un impact éloigné et l’absence d’impact.

Studio 0.2.33 accélère deux routines de rasterisation reconnues octet par octet dans la ROM BASIC. Un petit dessin mêlant rectangles et diagonale passe de 3,97 à 3,42 secondes sur le PC de test (environ 16 % plus rapide), avec des événements papier et un état CPU/RAM identiques. Le gain dépend du dessin ; ce chiffre ne prédit pas la durée d’une partie complète ni celle de la machine réelle.

Le suivi papier utilise `B` pour la position verticale courante et `G` pour la cible, en unités moteur ; `L` et `H` suivent de même la tête. Les tableaux `B()`, `H()` et `L()` sont distincts de ces scalaires. Une bande avance de 56 unités moteur ; la présentation au joueur vise au minimum la position 1680 et ramène la tête à zéro. L’historique commence à Y=840 puis utilise un pas de 84 par tir. Après LPRINT, la position est actualisée de 56 unités ; la présentation garantit ensuite 280 unités supplémentaires sous cette position. `ORIGIN` déclare la position avant chaque mouvement borné et ne déplace pas lui-même la feuille. Les déplacements ont lieu avant DRAW DEFERRED, jamais pendant une composition en attente.

### Validation de la version 0.5

Le programme occupe **3 898 octets tokenisés**, laissant **2 053 octets** avant les variables et les tampons. Aucun nouveau firmware n’est nécessaire : conserver la .86, puis recharger le programme. Les deux valeurs du dernier tir sont gardées dans X(10) et X(11), distinctes des dix positions dessinées.

Le test ROM ciblé vérifie les paramètres conservés par les chemins humain (47.5/88.25) et automatique (46/75 dans cet essai). Il vérifie ensuite une victoire et les cinq sons attendus (deux pour le tir réussi, trois pour la fin), puis imprime le tir 12 avec angle 47.5 et puissance 88.25. L’aperçu restitue ces valeurs ; le papier revient à la position de présentation calculée, `[0,4200]` phases. Quatre fragments de point à cheval sur les frontières sont également vérifiés dans la liste de formes réellement construite par le firmware. Outil : `tools/validate_ballistic_history.py` ; rapport et aperçu dans `build/ballistic-duel/history-checks.json` et `history-late-victory.png`. Ces essais ne remplacent pas la vérification mécanique et sonore sur la Canon.

Le contrôle intégré utilise la graine 42, le mode 2, un tir à 45°/90 puis la sortie volontaire. Il passe, avec vérification explicite des paramètres sauvegardés après le calcul balistique et du retour à la position de présentation après l’impression de l’historique. L’aperçu a été vérifié : `TIR 1 J1 ANGLE 45 PUISSANCE 90` figure sous le terrain. La marge programme/variables minimale est de 1 267 octets avant l’emprunt temporaire du tampon papier. Rapports et aperçu : `build/ballistic-duel/history.json` et `history.png`. Les plus gros points et le texte ajouté augmentent le travail d’impression ; les calculs balistiques sont conservés.

### Historique : validation de la version 0.4 ×2

Exécution de la ROM .86 : graine 42, mode deux joueurs, tirs 45°/90 dans les deux sens, retour au menu et sortie avec angle zéro. Les deux trajectoires et impacts sont superposés au même terrain. La position simulée revient à `[0,3360]` phases moteur à chaque présentation, soit 1680 unités Y. Le test porte sur les déplacements commandés ; il ne mesure pas la dérive mécanique réelle. Rapport et aperçu : `build/ballistic-duel/zoom.json` et `zoom.png`.

Trois essais ROM ciblés complètent cette partie : impact à une frontière de bande, sortie latérale gauche et croix centrée sur le raccord de quatre zones. Aucun dépassement de composition ni erreur de suivi papier ; les aperçus ont été vérifiés. Rapport : `build/ballistic-duel/zoom-edges.json`. Le dernier essai utilise une trajectoire synthétique pour isoler le découpage, pas pour valider la physique.

Source : **3 517 octets tokenisés**, soit **2 434 octets** avant variables. La marge programme/variables descend à **1 658 octets** pendant cet essai, avant l’emprunt temporaire du tampon papier (jusqu’à 732 octets). Le jeu tient donc dans la RAM sans NEW ni suppression des fonctions existantes.

Le calcul de trajectoire conserve exactement le même nombre d’étapes que la .3 pour ces tirs. L’impression agrandie coûte davantage : le premier tour passe de 5,39 à 9,62 millions d’étapes du cœur, le second de 6,18 à 10,95 millions ; la préparation du terrain passe de 6,40 à 14,32 millions. Ces comptes ne sont pas des durées sur machine. Le premier tir imprime 24 tuiles, le second 55. Les pointillés, le relief fixe et le calcul rapide restent actifs. L’agrandissement doit encore être vérifié sur papier réel.

### Historique : accélération de la version 0.3

`tools/validate_ballistic_duel.py` conserve la comparaison des collisions exactes de la 0.2 sur 8 000 cas. Il ajoute **10 000 cas pour la 0.3** : 100 reliefs, deux sens de tir, dix angles dont deux fractionnaires et cinq puissances. Résultat : 9 744 impacts et 256 sorties ; écart horizontal maximal de 0,234357 par rapport à la recherche exacte utilisant les mêmes vitesses tabulées. Tous les points restent dans les limites et au-dessus du terrain avant l’impact. La borne de la croix est aussi contrôlée après recadrage. Ces comparaisons utilisent l’arithmétique du PC et complètent les exécutions par le vrai code ROM.

Le même outil exécute le jeu dans le cœur HD6301 de Studio, produit des mesures par phase et un aperçu du papier dans `build/ballistic-duel/`. Il nécessite les ROM configurées localement pour les tests Studio. Aucun accès au port série, aucune impression physique ni écriture de firmware.

Exécution ROM vérifiée : graine 42, mode deux joueurs, tirs 45°/90 dans les deux sens, retour au menu et sortie avec angle 0. L’aperçu confirme la superposition sur une seule arène ; la position simulée revient à `[0,2240]` phases moteur à chaque présentation. Deux tests ROM supplémentaires ciblent une croix à cheval sur deux bandes et une sortie latérale gauche. Le comptage des bandes ne comprend plus le point de départ non imprimé : cela évite un déplacement fantôme après le dessin. Le mode contre la Canon et une partie complète restent à essayer. Cette validation ne mesure pas la dérive mécanique réelle.

Comparaison du **premier tour**, sans la préparation initiale ni la saisie (millions d’étapes du cœur d’émulation, pas millions de cycles matériels) :

| Phase | Version 0.1 | Version 0.2 | Version 0.3 |
|---|---:|---:|---:|
| Calcul de trajectoire et collision | 34,09 | 5,22 | 2,18 |
| Tracé et impressions associées | 9,92 | 5,10 | 2,20 |
| Dégâts et fin de tour, y compris présentation papier | 5,53 | 0,96 | 1,01 |
| Total | **49,54** | **11,27** | **5,39** |

Le premier tour demande **2,09 fois moins d’étapes que la 0.2**, le second **2,26 fois moins**. Pour le premier tir, six tuiles sont imprimées au lieu de douze ; le second utilise toujours 21 tuiles mais leur calcul est plus rapide. Moins d’encre ne signifie pas automatiquement moins de mouvements. La préparation initiale passe de 6,1 à 6,4 millions d’étapes, notamment pour charger la table trigonométrique : cette version accélère les tours, pas l’impression initiale du terrain. La phase dégâts était déjà peu coûteuse pour le premier tir hors de portée des canons ; le gain est plus marqué au second tir (2,42 → 0,88 millions d’étapes).

Source 0.3 : **2 788 octets tokenisés**, soit **3 163 octets** avant variables et données de travail. Pendant l’essai, la marge programme/variables descend à 2 511 octets, dont le pilote emprunte temporairement jusqu’à 732 octets pour une bande de huit tuiles et sa sauvegarde. La table trigonométrique contient 19 nombres, soit 95 octets de valeurs plus son descripteur. Les rapports `baseline.json`, `optimized.json` et `fast.json` contiennent les mesures ; `fast.bas` est la copie exacte de la source 0.3 testée et `fast.png` son aperçu papier.

### Historique : pistes d’optimisation du moteur graphique en .85

Le moteur de cette version produit des tuiles de **31 colonnes × 16 rangées utiles**, codées sur **64 octets** avec leur colonne de garde. Une bande de huit tuiles prend **512 octets**. Une image maximale de huit bandes prendrait **4 096 octets** sous ce format, ce qui concurrence fortement le programme et ses variables dans les 5 951 octets de RAM BASIC disponibles à vide.

Aligner les cases d’une grille sur ces tuiles rendrait la réutilisation de motifs plus simple, mais **l’alignement ne crée pas de cache** : actuellement, le compositeur appelle les moteurs de formes pour chaque tuile. Une cellule logique proche du carré correspondrait à 31 unités X et 32 unités Y, et non à 31×16 unités BASIC. Adapter les cases de Duel orbital à ces dimensions changerait aussi sa taille et ses placements de sprites.

La première optimisation générale à envisager est d’écarter les formes dont les limites ne croisent pas la tuile. Ensuite viendraient la réutilisation de bandes identiques pour les grilles et un chemin spécialisé pour les traits horizontaux et verticaux. Ces améliorations nécessitent du code firmware et des tests de rendu ; elles ne sont pas implémentées par cette mise à jour du jeu. La réserve ROM de la .85 n’est que de 68 octets explicitement libres, donc une réorganisation peut être nécessaire. Aucun framebuffer permanent n’est réservé par le jeu.

## English

A paper artillery game for Typestar BASIC, with more forgiving hits. One arena is printed at the start; each shot adds its trajectory and impact to that same arena. Terrain and cannons stay fixed: craters are omitted so the current ground cannot be confused with old outlines that paper cannot erase.

### Playing

Open the [French](../games/duel-balistique-fr.bas) or [English program](../games/ballistic-duel-en.bas) in Typestar BASIC Studio, or load it onto the Canon. Firmware used for validation: **0.4.86-dev**. This version requests numeric input again when it is empty or invalid, instead of stopping the program. The ×2 drawing also works with .85, which lacks that INPUT correction.

Enter a seed from 1 to 9999, then **1** to play against the Canon or **2** for two players. P1 is on the left, P2 on the right. Both aim towards their opponent: angle **10 to 80 degrees**, power **20 to 100**. An angle of **0** ends the game. Both players start with 100 health points. The computer chooses shots randomly.

For a reproducible trial, use seed **42**, mode **2**, then angle **45**, power **90** for each player. Both dotted trajectories should overlay the same terrain, without a new scene being printed. A small cross marks each ground impact. The sheet advances after each shot to make the result visible; leave its position under program control. Health remains on the LCD.

Below the terrain, each shot adds a line such as `SHOT 3 P1 ANGLE 45 POWER 90`. Entered angle and power are saved before calculations, including decimals; computer shots are recorded too. Earlier lines remain on paper. Spacing is one and a half lines. The history starts below the highest possible terrain and grows downwards; the sheet advances farther when the latest entry requires it. Allow enough paper for long games: the program provides neither pagination nor automatic sheet changes.

A short rising signal accompanies a shot that damages the opponent. A miss or a shot hurting only its own cannon remains silent. Three notes mark the end when a player's health reaches zero. Voluntarily quitting with angle zero is silent. These sounds use SOUND modulation of the existing buzzer.

Prefer thermal paper. After BREAK, an error or manual paper movement, start again on a fresh area: the game follows commanded movements and has no absolute-position sensor. Overlay accuracy still depends on the paper mechanism; experimental Y calibration is a separate subject.

### Speed improvements

- **One terrain per game.** The initial scene has 16 ground segments and four shapes for the cannons. Terrain then stays unchanged.
- **Dotted trajectories.** Nine filled 4×4-logical-unit squares replace the ten segments: they occupy **4 columns × 2 native rows**, versus 2×1 in .4, doubling width and height. They use BOX rather than POINT to clip cleanly across composition boundaries; no fragment is dropped at a join. Two short LINE commands form the impact cross, replacing the circle. The cannon marks the start and is not reprinted to close the dotted path. Points are calculated once, then stored in two arrays for distribution among printable regions.
- **Skip empty bands above the drawing.** The game moves paper directly to the first useful band, then subtracts that offset from its coordinates. The offset is a multiple of 32 BASIC Y units, or 16 native rows, preserving the pixel grid between passes. The initial scene is cropped in the same way.
- **Small trigonometric table.** Nineteen sine values in thousandths, at 5° intervals, replace SIN/COS calls. Interpolation preserves intermediate angles, including decimals. Cosine reads the same table backwards.
- **Advance by addition.** At equal time intervals, X increases by a constant; the increment of Y also increases by a constant. The game uses this property to traverse terrain and place points, instead of repeating divisions and products at every step.
- **No square root.** Five subdivisions of the interval locate the impact on the struck segment. Damage also uses the approximate distance described below.

Remaining calculations still run through the interpreter and the ROM's decimal routines: integer constants do not turn BASIC into a fast integer interpreter. Rasterising shapes and moving motors also take time. Emulator measurements are comparative, not promised hardware timings.

### Geometry and physics

The simulation retains X=0..240 and Y=0..220. **Rendering doubles both axes**: terrain, cannons, trajectories and impact crosses occupy twice their previous width and height. The title retains its normal size. Positions and damage are calculated in the old coordinates, so enlargement changes neither rules nor range.

Each firmware composition is limited to X=0..247 and Y=0..255. The game therefore divides the drawing into two horizontal regions of 248 units and, when necessary, two vertical regions. The horizontal join corresponds to eight tiles and a HEAD movement of 128 motor units. Vertical regions start on a band boundary; an empty region is cancelled without printing. Ground and impact lines crossing a boundary are clipped. Neither terrain erasure nor trajectory recalculation is needed.

The driver converts Y to `INT(Y/2)`. Logical units have approximately equal physical lengths; native dots are about twice as tall as wide. This enlarges geometric coordinates rather than duplicating individual pixels; very thin lines remain subject to quantisation. The 17 terrain vertices, spaced 15 simulation units apart, have heights from 120 to 180. Two platforms carry cannons at X=30 and X=210.

The trajectory retains the form `X=B(S)+U*T`, `Y=Z-V*T+T*T`, with initial speed close to `P/5` and gravity 2. U and V now use the interpolated table: range on level ground remains near 200 units at power 100 and angle 45°, but results are no longer identical to the firmware's SIN/COS. The nine points fall at 10%, 20%, …, 90% of flight time; a side exit gets a final point and a ground impact gets a cross.

On each ground segment, the difference between projectile height and ground height is a convex quadratic function. While that difference is negative at both ends of the traversed interval, no collision occurs between them. At the first vertex reached below ground, five subdivisions keep the intersection bracketed. The final midpoint gives a theoretical maximum horizontal error of `15/64 = 0.234375` unit for **this same approximate parabola**, excluding BASIC rounding. This bound excludes differences from the old trigonometry. Impact height is interpolated on the terrain to place the cross on its outline. The reasoning assumes a start above ground, monotonic horizontal movement and terrain without caves.

A ground impact within six horizontal units and eight vertical units of a cannon's base causes **100 damage**: one direct hit now defeats an undamaged cannon. These tolerances use simulation coordinates, before ×2 rendering. They provide a margin around the cannon rather than requiring a single-pixel hit. Outside this area, damage is `INT(100-3*distance)`, bounded below by zero, with `distance=max(dx,dy)+3*min(dx,dy)/8`. A player can hurt themselves under the same rules. Leaving the terrain without an impact causes no damage. There is no wind or player movement.

The previous version capped damage at 60: even a centred shot could not destroy a fresh cannon. ROM tests in `tools/validate_ballistic_damage.py` cover the centre, inclusive boundaries, nearby damage, a distant impact and absence of impact.

Studio 0.2.33 accelerates two rasterisation routines recognised byte for byte in the BASIC ROM. A small drawing combining rectangles and a diagonal falls from 3.97 to 3.42 seconds on the test PC (about 16% faster), with identical paper events and CPU/RAM state. The gain depends on the drawing; this figure predicts neither a complete game's duration nor real-hardware timing.

Paper tracking uses `B` for current vertical position and `G` for its target, in motor units; `L` and `H` similarly track the head. Arrays `B()`, `H()` and `L()` are distinct from these scalars. A band advances by 56 motor units; presentation to the player targets at least position 1680 and returns the head to zero. History starts at Y=840, then advances 84 per shot. After LPRINT, position is updated by 56 units; presentation then ensures 280 extra units below this position. `ORIGIN` declares position before each bounded movement and does not itself move paper. Movements happen before DRAW DEFERRED, never while a composition is pending.

### Version 0.5 validation

The program uses **3,898 tokenized bytes**, leaving **2,053 bytes** before variables and buffers. No new firmware is required: keep .86 and reload the program. The last shot's two parameters are saved in X(10) and X(11), separately from the ten plotted positions.

The targeted ROM test checks parameters preserved along human (47.5/88.25) and automatic (46/75 in this test) paths. It then checks victory and the five expected sounds (two for the successful shot, three at the end), and prints shot 12 with angle 47.5 and power 88.25. The preview shows those values; paper returns to the calculated presentation position, `[0,4200]` phases. Four point fragments straddling boundaries are also checked in the shapes actually built by the firmware. Tool: `tools/validate_ballistic_history.py`; report and preview in `build/ballistic-duel/history-checks.json` and `history-late-victory.png`. These tests do not replace mechanical and sound checks on the Canon.

The integrated check uses seed 42, mode 2, a 45°/90 shot and then voluntary exit. It passes, explicitly checking parameters saved after the ballistic calculation and the return to presentation position after history printing. The preview was inspected: `TIR 1 J1 ANGLE 45 PUISSANCE 90` appears below the terrain in the French test. Minimum program/variable headroom is 1,267 bytes before temporarily borrowing the paper buffer. Reports and preview: `build/ballistic-duel/history.json` and `history.png`. Larger dots and added text increase printing work; ballistic calculations are retained.

### History: version 0.4 ×2 validation

Execution of ROM .86: seed 42, two-player mode, 45°/90 shots in both directions, return to menu and exit with angle zero. Both trajectories and impacts overlay the same terrain. Simulated position returns to `[0,3360]` motor phases at each presentation, or 1680 Y units. The test covers commanded movements, not real mechanical drift. Report and preview: `build/ballistic-duel/zoom.json` and `zoom.png`.

Three targeted ROM trials add an impact at a band boundary, a left-side exit and a cross centred at the join of four regions. There is no composition overflow or paper-tracking error; previews were inspected. Report: `build/ballistic-duel/zoom-edges.json`. The last trial uses a synthetic trajectory to isolate clipping, not to validate physics.

Source: **3,517 tokenized bytes**, leaving **2,434 bytes** before variables. Program/variable headroom falls to **1,658 bytes** during this trial, before temporarily borrowing the paper buffer (up to 732 bytes). The game therefore fits RAM without NEW or removing existing features.

Trajectory calculation retains exactly the same step count as .3 for these shots. Larger printing costs more: the first turn goes from 5.39 to 9.62 million core steps, the second from 6.18 to 10.95 million; terrain preparation rises from 6.40 to 14.32 million. These counts are not hardware timings. The first shot prints 24 tiles, the second 55. Dots, fixed terrain and fast calculations remain active. Enlargement still needed checking on real paper at this validation stage.

### History: version 0.3 acceleration

`tools/validate_ballistic_duel.py` retains the .2 exact-collision comparison over 8,000 cases. It adds **10,000 cases for .3**: 100 terrains, two firing directions, ten angles including two fractional ones, and five powers. Results: 9,744 impacts and 256 exits; maximum horizontal error 0.234357 against exact search using the same tabulated velocities. All points remain within bounds and above ground before impact. Cross bounds are also checked after cropping. These comparisons use PC arithmetic and complement execution of the actual ROM code.

The same tool runs the game in Studio's HD6301 core, producing per-phase measurements and a paper preview in `build/ballistic-duel/`. It needs ROMs configured locally for Studio tests. It neither accesses the serial port, prints physically nor writes firmware.

Verified ROM execution: seed 42, two-player mode, 45°/90 shots in both directions, return to menu and exit with angle 0. The preview confirms overlay on one arena; simulated position returns to `[0,2240]` motor phases at each presentation. Two more ROM tests target a cross spanning two bands and a left-side exit. Band counting now excludes the unprinted starting point, avoiding a phantom movement after drawing. Canon-opponent mode and a complete game still needed testing at this stage. This validation does not measure real mechanical drift.

Comparison of the **first turn**, excluding initial preparation and input (millions of emulator-core steps, not millions of hardware cycles):

| Phase | Version 0.1 | Version 0.2 | Version 0.3 |
|---|---:|---:|---:|
| Trajectory and collision calculation | 34.09 | 5.22 | 2.18 |
| Drawing and associated printing | 9.92 | 5.10 | 2.20 |
| Damage and end of turn, including paper presentation | 5.53 | 0.96 | 1.01 |
| Total | **49.54** | **11.27** | **5.39** |

The first turn takes **2.09 times fewer steps than .2**, the second **2.26 times fewer**. The first shot prints six tiles instead of twelve; the second still uses 21 tiles, calculated faster. Less ink does not automatically mean fewer movements. Initial preparation rises from 6.1 to 6.4 million steps, partly to load the trigonometric table: this version speeds up turns, not initial terrain printing. The damage phase was already cheap for the first shot outside cannon range; the gain is greater on the second (2.42 → 0.88 million steps).

Source .3: **2,788 tokenized bytes**, leaving **3,163 bytes** before variables and workspace. During the trial, program/variable headroom falls to 2,511 bytes, from which the driver temporarily borrows up to 732 bytes for an eight-tile band and its saved workspace. The trigonometric table contains 19 numbers: 95 value bytes plus its descriptor. Reports `baseline.json`, `optimized.json` and `fast.json` hold measurements; `fast.bas` is the exact .3 source tested and `fast.png` its paper preview.

### Historical notes: graphics-engine optimisation proposals for .85

The engine described at this stage produces tiles of **31 columns × 16 useful rows**, encoded in **64 bytes** including a guard column. An eight-tile band takes **512 bytes**. A maximum eight-band image would take **4,096 bytes** in this format, competing heavily with the program and variables in the 5,951 BASIC RAM bytes free at startup.

Aligning grid cells to these tiles would simplify motif reuse, but **alignment alone creates no cache**: the compositor described here calls shape routines for every tile. A nearly square logical cell would be 31 X units by 32 Y units, rather than 31×16 BASIC units. Changing Orbital Duel cells to these dimensions would also change board size and sprite positions.

The first general optimisation proposed here was to exclude shapes whose bounds do not intersect a tile. Next would come reuse of identical bands for grids and a specialised path for horizontal and vertical lines. These proposals require firmware code and rendering tests; they were not implemented by this game update. ROM .85 had only 68 explicitly free bytes, so reorganisation could be necessary. The game reserves no permanent framebuffer.
