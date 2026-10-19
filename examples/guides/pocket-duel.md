# Pocket Duel 1.1 — Typestar BASIC

## Français

Un duel pour le LCD et le buzzer.

Ouvrez la [version française](../games/pocket-duel-fr.bas) dans Studio, puis lancez F5, ou envoyez-la à la Canon et tapez RUN. Une touche passe le dernier écran de présentation. L'arène de 32 cases relie son bord gauche à son bord droit. **Les flèches déplacent votre personnage, Entrée attaque un adversaire adjacent et Espace téléporte.** La lettre A reste sans action. BREAK interrompt la partie.

Vous commencez avec cinq points de vie et deux points de charge. Chaque déplacement ajoute un point de charge, jusqu'à cinq. Une attaque ou une téléportation demande les cinq points et vide cette réserve. Un double bip indique une action indisponible : rechargez en marchant ou rapprochez-vous pour attaquer. Relâchez la touche après votre choix. L'adversaire agit après votre action. Les cases 1 et 32 sont voisines, y compris pour les attaques.

Les triangles représentent les points de vie ; la ligne inférieure indique la charge. Les mines infligent des dégâts et les grilles bloquent les déplacements ordinaires. Ces obstacles peuvent apparaître, disparaître et, pour les grilles, se déplacer. Une attaque repousse aussi sa cible.

Ce jeu montre deux personnages LCD personnalisés, un effet temporaire, LCDTRI, LCDLINE, les sons et les caractères natifs : **172 pour la grille**, **192 pour la mine**, y compris dans la légende de départ. « Flèches » utilise directement è dans le source UTF-8 ; le caractère occupe un seul octet en RAM.

Retirez les cinq points de vie de l'adversaire pour gagner. Une victoire ou une défaite termine la manche ; RUN en commence une autre. Les touches directionnelles utilisent les valeurs INKEY traduites 18/19 ; Entrée vaut 13. La commande MEM permet de consulter la mémoire libre sur la machine.

## English

A duel for the LCD and buzzer.

Open the [English version](../games/pocket-duel-en.bas) in Studio and press F5, or send it to the Canon and type RUN. A key passes the last introduction screen. The 32-cell arena connects its left and right ends. **Arrows move your character, Enter attacks an adjacent enemy and Space teleports.** A has no action. BREAK interrupts the game.

You start with five health points and two charge points. Each move adds one charge point, up to five. Attacking or teleporting needs all five and empties the reserve. A double beep means the action is unavailable: recharge by moving or get closer before attacking. Release the key after choosing an action. The enemy acts after you. Cells 1 and 32 are adjacent, including for attacks.

Triangles show health; the lower row shows charge. Mines cause damage and fences block ordinary movement. These obstacles can appear, disappear and, in the case of fences, move. An attack also knocks its target back.

This game demonstrates two custom LCD characters, a temporary effect, LCDTRI, LCDLINE, sound and native characters: **172 for fences**, **192 for mines**, including in the opening legend. The French UTF-8 source writes “Flèches” with a literal è; that character occupies one byte in RAM.

Remove all five enemy health points to win. Victory or defeat ends the round; RUN starts another. Arrow keys use translated INKEY values 18/19; Enter is 13. MEM reports free memory on the machine.
