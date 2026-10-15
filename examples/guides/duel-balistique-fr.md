# Duel balistique 0.6 — impacts plus tolérants

Jeu d’artillerie sur papier pour Typestar BASIC. Une arène est imprimée au début de la partie ; chaque tir ajoute sa trajectoire et son impact sur cette même arène. Le relief et les canons restent fixes : il n’y a plus de cratères, pour éviter de confondre le sol actuel avec des contours impossibles à effacer. Ce choix a été confirmé par Pierre.

## Jouer

Ouvrir `duel-balistique-fr.bas` dans Typestar BASIC Studio ou le charger sur la Canon. Firmware utilisé pour la vérification : **0.4.86-dev**. Cette version redemande les réponses numériques vides ou invalides au lieu d’arrêter le programme. Le dessin ×2 reste compatible avec la .85, mais elle ne possède pas cette correction d’INPUT.

Entrer une graine de 1 à 9999, puis **1** pour jouer contre la Canon ou **2** pour deux joueurs. J1 est à gauche, J2 à droite. Chacun vise vers son adversaire : angle de **10 à 80 degrés**, puissance de **20 à 100**. Un angle de **0** termine la partie. Les deux joueurs commencent avec 100 points de vie. L’adversaire informatique choisit ses tirs au hasard.

Pour un essai reproductible : graine **42**, mode **2**, puis angle **45**, puissance **90** pour chaque joueur. Les deux trajectoires en pointillés doivent se superposer au même terrain, sans nouvelle vignette. Une petite croix marque chaque impact au sol. La feuille avance après chaque tir pour rendre le résultat visible ; ne pas modifier manuellement sa position pendant la partie. Les vies restent sur le LCD.

Sous le terrain, chaque tir ajoute une ligne telle que `TIR 3 J1 ANGLE 45 PUISSANCE 90`. L’angle et la puissance saisis sont conservés avant les calculs, y compris leurs décimales ; les tirs de l’adversaire informatique sont consignés également. Les anciennes lignes restent sur papier. L’interligne vaut une ligne et demie. L’historique commence sous le relief le plus haut possible et descend progressivement ; la feuille avance davantage lorsque la dernière entrée le nécessite. Prévoir assez de papier pour les longues parties : le jeu n’effectue pas de pagination ni de changement de feuille automatique.

Un bref signal ascendant accompagne un tir qui endommage l’adversaire ; un tir raté ou qui ne blesse que son propre canon reste silencieux. Trois notes marquent la fin de la partie lorsque les vies d’un joueur atteignent zéro. La sortie volontaire avec un angle nul reste silencieuse. Ces sons utilisent la modulation SOUND du buzzer existant.

Préférer du papier thermique. Après BREAK, une erreur ou une manipulation manuelle de la feuille, recommencer sur une zone vierge : le jeu suit les déplacements commandés, il n’a pas de capteur de position absolue. La précision des superpositions dépend toujours du mécanisme papier ; la calibration Y expérimentale reste un sujet séparé.

## Accélérations

- **Un terrain par partie.** La scène initiale contient 16 segments de sol et quatre formes pour les canons. Le terrain reste inchangé ensuite.
- **Trajectoires en pointillés.** Neuf petits carrés pleins de 4×4 unités logiques remplacent les dix segments : ils occupent **4 colonnes ×2 rangées natives**, contre 2×1 dans la .4, soit le double de largeur et de hauteur. Ils utilisent BOX plutôt que POINT pour découper proprement ceux qui traversent une limite de zone ; aucun fragment n’est supprimé au raccord. Deux petits LINE forment la croix d’impact, à la place du cercle. Le canon matérialise le départ ; il n’est pas réimprimé pour fermer les pointillés. Les points sont calculés une seule fois, puis conservés dans deux tableaux pour être répartis entre les zones imprimables.
- **Suppression des bandes vides en tête de dessin.** Le jeu déplace directement la feuille jusqu’à la première bande utile, puis soustrait son décalage aux coordonnées. Ce décalage est un multiple de 32 unités Y BASIC, soit 16 rangées natives, pour conserver la même grille de pixels entre passages. La scène initiale bénéficie aussi de ce recadrage.
- **Petite table trigonométrique.** Dix-neuf valeurs de sinus en millièmes, espacées de 5°, remplacent les appels à SIN/COS. Une interpolation conserve les angles intermédiaires, y compris décimaux. Le cosinus utilise la même table en sens inverse.
- **Progression par additions.** À intervalles de temps égaux, X augmente d’une constante ; l’incrément de Y augmente lui aussi d’une constante. Le jeu utilise cette propriété pour parcourir le relief et placer les points, au lieu de refaire divisions et produits à chaque étape.
- **Aucune racine carrée.** Sur le segment touché, cinq subdivisions de l’intervalle recherchent l’impact. Les dégâts utilisent également une distance approchée, décrite ci-dessous.

Les calculs restants passent toujours par l’interpréteur et les routines décimales de la ROM : écrire des constantes entières ne transforme pas le BASIC en interpréteur entier rapide. La conversion des formes en pixels et les moteurs prennent aussi du temps. Les mesures d’émulation sont comparatives ; ce ne sont pas des durées promises sur machine réelle.

## Géométrie et physique

La simulation conserve X=0..240 et Y=0..220. **Le rendu double les deux axes** : terrain, canons, trajectoires et croix d’impact occupent deux fois la largeur et la hauteur précédentes. Le titre conserve sa taille normale. Les positions et dégâts sont calculés dans les anciennes coordonnées ; l’agrandissement ne change pas les règles ni la portée.

Chaque composition du firmware est limitée à X=0..247 et Y=0..255. Le jeu découpe donc le dessin en deux zones horizontales de 248 unités et, si nécessaire, deux zones verticales. Le raccord horizontal correspond à huit tuiles et à un déplacement HEAD de 128 unités moteur. Les zones verticales commencent sur une frontière de bande ; une zone vide est annulée sans impression. Les traits de sol et d’impact qui traversent une frontière sont découpés. Aucun effacement du terrain ni recalcul de la trajectoire n’est nécessaire.

Le pilote convertit Y en `INT(Y/2)`. Les unités logiques ont des longueurs physiques approximativement égales ; les points natifs sont environ deux fois plus hauts que larges. Il s’agit d’un agrandissement des coordonnées géométriques, pas d’une duplication pixel par pixel ; les traits très fins restent soumis à cette quantification. Les 17 sommets du relief, espacés de 15 unités de simulation, ont des hauteurs entre 120 et 180. Deux plateformes portent les canons aux abscisses 30 et 210.

La trajectoire conserve la forme `X=B(S)+U*T`, `Y=Z-V*T+T*T`, avec une vitesse initiale voisine de `P/5` et une gravité de 2. U et V utilisent maintenant la table interpolée : la portée à hauteur égale reste proche de 200 unités à puissance 100 et angle 45°, mais les résultats ne sont plus strictement identiques à ceux des SIN/COS du firmware. Les neuf points se situent à 10 %, 20 %, …, 90 % du temps de vol ; la sortie latérale reçoit un dernier point, l’impact au sol une croix.

Sur chaque segment de terrain, la différence entre la hauteur du projectile et celle du sol est une fonction quadratique convexe. Tant que cette différence reste négative aux deux extrémités traversées, il n’y a pas de collision entre elles. Au premier sommet atteint sous le sol, cinq subdivisions conservent l’encadrement de l’intersection. Le milieu final donne une erreur horizontale théorique maximale de `15/64 = 0,234375` unité pour **cette même parabole approchée**, hors arrondis BASIC. Cette borne n’inclut pas la différence avec l’ancienne trigonométrie. La hauteur d’impact est interpolée sur le terrain afin de placer la croix sur son contour. Le raisonnement dépend du départ au-dessus du sol, de la progression horizontale monotone et du relief sans cavernes.

Un impact au sol situé à six unités horizontales et huit unités verticales au plus de la base du canon inflige **100 dégâts** : un coup direct suffit désormais à gagner contre un canon intact. Ces tolérances utilisent les coordonnées de simulation, avant le rendu ×2. Elles accordent une marge autour du canon ; il ne faut pas viser un pixel précis. En dehors de cette zone, les dégâts valent `INT(100-3*distance)`, bornés à zéro, avec `distance=max(dx,dy)+3*min(dx,dy)/8`. Un joueur peut se blesser lui-même selon les mêmes règles. Les sorties de terrain sans impact ne causent aucun dégât. Il n’y a pas de vent ni de déplacement des joueurs.

La version précédente plafonnait à 60 dégâts : même un tir centré ne pouvait pas détruire un canon neuf. Les tests ROM de `tools/validate_ballistic_damage.py` contrôlent le centre, les limites incluses, les dégâts proches, un impact éloigné et l’absence d’impact.

Studio 0.2.33 accélère deux routines de rasterisation reconnues octet par octet dans la ROM BASIC. Un petit dessin mêlant rectangles et diagonale passe de 3,97 à 3,42 secondes sur le PC de test (environ 16 % plus rapide), avec des événements papier et un état CPU/RAM identiques. Le gain dépend du dessin ; ce chiffre ne prédit pas la durée d’une partie complète ni celle de la machine réelle.

Le suivi papier utilise `B` pour la position verticale courante et `G` pour la cible, en unités moteur ; `L` et `H` suivent de même la tête. Les tableaux `B()`, `H()` et `L()` sont distincts de ces scalaires. Une bande avance de 56 unités moteur ; la présentation au joueur vise au minimum la position 1680 et ramène la tête à zéro. L’historique commence à Y=840 puis utilise un pas de 84 par tir. Après LPRINT, la position est actualisée de 56 unités ; la présentation garantit ensuite 280 unités supplémentaires sous cette position. `ORIGIN` déclare la position avant chaque mouvement borné et ne déplace pas lui-même la feuille. Les déplacements ont lieu avant DRAW DEFERRED, jamais pendant une composition en attente.

## Validation de la version 0.5

Le programme occupe **3 898 octets tokenisés**, laissant **2 053 octets** avant les variables et les tampons. Aucun nouveau firmware n’est nécessaire : conserver la .86, puis recharger le programme. Les deux valeurs du dernier tir sont gardées dans X(10) et X(11), distinctes des dix positions dessinées.

Le test ROM ciblé vérifie les paramètres conservés par les chemins humain (47.5/88.25) et automatique (46/75 dans cet essai). Il vérifie ensuite une victoire et les cinq sons attendus (deux pour le tir réussi, trois pour la fin), puis imprime le tir 12 avec angle 47.5 et puissance 88.25. L’aperçu restitue ces valeurs ; le papier revient à la position de présentation calculée, `[0,4200]` phases. Quatre fragments de point à cheval sur les frontières sont également vérifiés dans la liste de formes réellement construite par le firmware. Outil : `tools/validate_ballistic_history.py` ; rapport et aperçu dans `build/ballistic-duel/history-checks.json` et `history-late-victory.png`. Ces essais ne remplacent pas la vérification mécanique et sonore sur la Canon.

Le contrôle intégré utilise la graine 42, le mode 2, un tir à 45°/90 puis la sortie volontaire. Il passe, avec vérification explicite des paramètres sauvegardés après le calcul balistique et du retour à la position de présentation après l’impression de l’historique. L’aperçu a été vérifié : `TIR 1 J1 ANGLE 45 PUISSANCE 90` figure sous le terrain. La marge programme/variables minimale est de 1 267 octets avant l’emprunt temporaire du tampon papier. Rapports et aperçu : `build/ballistic-duel/history.json` et `history.png`. Les plus gros points et le texte ajouté augmentent le travail d’impression ; les calculs balistiques sont conservés.

## Historique : validation de la version 0.4 ×2

Exécution de la ROM .86 : graine 42, mode deux joueurs, tirs 45°/90 dans les deux sens, retour au menu et sortie avec angle zéro. Les deux trajectoires et impacts sont superposés au même terrain. La position simulée revient à `[0,3360]` phases moteur à chaque présentation, soit 1680 unités Y. Le test porte sur les déplacements commandés ; il ne mesure pas la dérive mécanique réelle. Rapport et aperçu : `build/ballistic-duel/zoom.json` et `zoom.png`.

Trois essais ROM ciblés complètent cette partie : impact à une frontière de bande, sortie latérale gauche et croix centrée sur le raccord de quatre zones. Aucun dépassement de composition ni erreur de suivi papier ; les aperçus ont été vérifiés. Rapport : `build/ballistic-duel/zoom-edges.json`. Le dernier essai utilise une trajectoire synthétique pour isoler le découpage, pas pour valider la physique.

Source : **3 517 octets tokenisés**, soit **2 434 octets** avant variables. La marge programme/variables descend à **1 658 octets** pendant cet essai, avant l’emprunt temporaire du tampon papier (jusqu’à 732 octets). Le jeu tient donc dans la RAM sans NEW ni suppression des fonctions existantes.

Le calcul de trajectoire conserve exactement le même nombre d’étapes que la .3 pour ces tirs. L’impression agrandie coûte davantage : le premier tour passe de 5,39 à 9,62 millions d’étapes du cœur, le second de 6,18 à 10,95 millions ; la préparation du terrain passe de 6,40 à 14,32 millions. Ces comptes ne sont pas des durées sur machine. Le premier tir imprime 24 tuiles, le second 55. Les pointillés, le relief fixe et le calcul rapide restent actifs. L’agrandissement doit encore être vérifié sur papier réel.

## Historique : accélération de la version 0.3

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

## Optimisations possibles du moteur graphique

Le moteur actuel produit des tuiles de **31 colonnes × 16 rangées utiles**, codées sur **64 octets** avec leur colonne de garde. Une bande de huit tuiles prend **512 octets**. Une image maximale de huit bandes prendrait **4 096 octets** sous ce format, ce qui concurrence fortement le programme et ses variables dans les 5 951 octets de RAM BASIC disponibles à vide.

Aligner les cases d’une grille sur ces tuiles rendrait la réutilisation de motifs plus simple, mais **l’alignement ne crée pas de cache** : actuellement, le compositeur appelle les moteurs de formes pour chaque tuile. Une cellule logique proche du carré correspondrait à 31 unités X et 32 unités Y, et non à 31×16 unités BASIC. Adapter les cases de Duel orbital à ces dimensions changerait aussi sa taille et ses placements de sprites.

La première optimisation générale à envisager est d’écarter les formes dont les limites ne croisent pas la tuile. Ensuite viendraient la réutilisation de bandes identiques pour les grilles et un chemin spécialisé pour les traits horizontaux et verticaux. Ces améliorations nécessitent du code firmware et des tests de rendu ; elles ne sont pas implémentées par cette mise à jour du jeu. La réserve ROM de la .85 n’est que de 68 octets explicitement libres, donc une réorganisation peut être nécessaire. Aucun framebuffer permanent n’est réservé par le jeu.
