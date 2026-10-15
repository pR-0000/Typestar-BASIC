# Bataille navale — première version Typestar BASIC

Une [version duel contre la Canon](duel-orbital.md) permet aussi de placer sa flotte et de jouer à tour de rôle.

Chasse en solitaire contre trois navires placés au hasard : un de trois cases et deux de deux cases. Ils sont horizontaux ou verticaux, ne se chevauchent pas mais peuvent se toucher. Retrouvez les sept cases en 24 tirs.

Ouvrir `bataille-navale-fr.bas` dans Studio, puis F5 pour essayer avec le papier simulé, ou envoyer le programme sur la Canon et taper RUN. Charger du papier thermique avant de commencer. Return lance la partie ; le temps d'attente fournit la graine aléatoire sans demander un nombre au joueur.

Le programme imprime un petit bateau dessiné avec BOX et LINE, les règles et une grille 6 × 6. Saisir une coordonnée comme A1 ou f6, puis Return. Le résultat reste sur le LCD jusqu'à Return : TOUCHE, COULE ou A L'EAU, suivi du nombre de tirs utilisés et du nombre de cases touchées. Une coordonnée invalide ou une case déjà visée ne coûte pas de tir. Q puis Return termine la partie et dévoile les cases restantes.

Les marques sont imprimées dans la grille grâce à LLOCATE : X pour une touche, O pour l'eau, # pour les cases révélées à la fin. Après chaque tir, le papier avance jusqu'à une position de lecture ; il revient ensuite à la case à marquer. Ne pas déplacer le papier manuellement pendant la partie. L'interligne est réglé à 1.5. BREAK interrompt le programme, mais ne termine pas la feuille de résultats.

Cette première version utilise une grille de caractères pour les cases, et les primitives graphiques pour le dessin du bateau. Elle démontre DIM à deux dimensions, RND, INPUT, IF, GOSUB, BOX, LINE, DRAW, LPRINT, LLOCATE, LSPACING et SOUND. Elle tient sur une seule feuille et ne nécessite pas de cartouche RAM. L'alignement et la hauteur de lecture restent à valider sur la machine réelle.

## Vérification de développement

`tools/validate_naval_paper.py` exécute le programme complet avec papier simulé : un tir, le même tir répété, une coordonnée invalide et un abandon. L’aperçu est enregistré dans `build/naval/preview.png`. `tools/validate_naval_logic.py` teste la victoire et la limite de tirs avec une flotte fixe, en retirant les impressions pour accélérer ce contrôle distinct. Les deux outils exécutent le firmware BASIC ; aucun port série physique n’est ouvert.

Validation hors machine réussie : impression et révélation, tirs répétés, entrée invalide, victoire en sept tirs et fin après 24 tirs. Taille du programme : **1 790 octets**, laissant **4 161 octets** avant allocation des variables et buffers. Rapport : `build/naval/validation.json`.
