# Pocket Duel 1.0 — Typestar BASIC

Validé sur machine par Pierre le 27 septembre 2026.

## Français

Programme finalisé : [version française](../pocket-duel-fr.bas). Une arène de 32 cases relie son bord gauche à son bord droit. Déplacez-vous avec les flèches ; A attaque un adversaire adjacent, Espace téléporte, Return termine la partie. Les actions d’attaque et de téléportation demandent une charge pleine. Les déplacements rechargent votre personnage ; l’adversaire agit après votre action.

Les triangles représentent les points de vie ; la ligne inférieure indique la charge. Les mines infligent des dégâts et les grilles bloquent les déplacements ordinaires. Ces obstacles peuvent apparaître, disparaître et, pour les grilles, se déplacer. Une attaque repousse aussi sa cible.

Ce jeu montre deux personnages LCD personnalisés, un effet temporaire, LCDTRI, LCDLINE, les sons et les caractères natifs : **172 pour la grille**, **192 pour la mine**, y compris dans la légende de départ. « Flèches » utilise directement è dans le source UTF-8. Utiliser Studio 0.2.19 ou transfer_native_basic.py avec le firmware 0.4.83-dev ; le caractère occupe un seul octet en RAM.

Taille tokenisée française : **4 750 octets**, laissant **1 201 octets** avant allocation des variables et buffers. Les touches directionnelles utilisent les valeurs INKEY traduites 18/19, et non les codes bruts KEYS $31/$32. Pour l’attaque, saisir a (sans majuscule). BREAK reste disponible pour interrompre le programme.

## English

Finished program: [English version](../pocket-duel-en.bas). Fight in a 32-cell arena whose left and right ends connect. Use the arrow keys to move, A (lowercase a) to attack an adjacent enemy, Space to teleport, and Return to quit. Attacks and teleportation require a full charge. Movement restores charge; the enemy takes its turn after your action.

The triangles show health; the lower row shows charge. Mines cause damage and fences block ordinary movement. Obstacles appear and expire; fences may also move. Attacks knock the target back.

The game demonstrates custom LCD characters, an effect glyph, LCDTRI, LCDLINE, sound and native characters: **CHR$(172) for fences** and **CHR$(192) for mines**. The English program uses **4,738 tokenized bytes**, leaving **1,213 bytes** before variables and buffers. Load it using Studio or the program transfer tool. F5 runs it directly in Studio; on the Canon, use LOAD then RUN. BREAK interrupts execution.

The French version uses a literal è in its UTF-8 source and requires firmware 0.4.83-dev with Studio 0.2.19 or transfer_native_basic.py. Each supported accented character occupies one byte in BASIC RAM. The English source remains ASCII. Native LCD codes are distinct from Unicode and paper-font codes.
