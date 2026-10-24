# Typestar BASIC - manuel de l'utilisateur

Pierre Raimbault & Chat GPT - rédaction française du 24 octobre 2026.

Référence du langage : **Typestar BASIC 0.4.100-dev**, sur Canon S-70 / Typestar 7. Ce manuel accompagne vos premières instructions, puis vos programmes utilisant le clavier, le LCD, l'imprimante, le buzzer et la liaison série. Aucune connaissance de l'assembleur ni de l'électronique n'est nécessaire pour suivre les ateliers.

Chaque leçon propose une idée simple, quelques lignes à essayer, une explication du résultat et une modification personnelle. Sauvegardez votre programme avant de saisir un nouvel exercice. L’[édition anglaise](en/README.md) reprend les chapitres, les exemples et les illustrations localisées.

## Lire les chapitres

L’installation suit immédiatement la présentation des capacités. Le chapitre Studio accompagne ensuite l’édition, les essais et les transferts de programmes ; les chapitres historiques peuvent se lire à votre rythme.

1. [Typestar BASIC en un coup d’œil](00-fiche-machine.md) : capacités, matériel et comparaison de machines à LCD.
2. [Installation - Passer au BASIC](02-installation-firmware.md) : préparer la ROM, ouvrir le boîtier, remplacer IC8 et faire le premier essai.
3. [Typestar BASIC Studio - votre atelier sur ordinateur](02-studio.md) : éditeur, émulateur, glyphes, transferts, papier et débogueur illustrés.
4. [Bienvenue avec Printy](00-pourquoi-programmer.md) : une introduction courte à la programmation.
5. [Une histoire des Canon Typestar](01-histoire-typestar.md)
6. [Le HD6301, un petit ordinateur sous le clavier](02-hd6301.md)
7. [Typestar BASIC sous le capot](02-presentation-firmware.md) : création, carte mémoire, tokens, calculs Canon, compression et voie IC7 / INT-EXT.
8. [À vous de donner les instructions](03-premiers-pas.md) : console, touches, RUN, LIST, NEW, mémoire et sauvegarde.
9. [Des nombres, des mots et des petites boîtes](04-nombres-variables.md) : affectation, décimaux, calculs, chaînes, binaire et tableaux.
10. [Choisir, recommencer et retrouver son chemin](05-decisions-boucles.md) : INPUT, IF/THEN/ELSE, boucles, sous-programmes, DATA et opérateurs logiques.
11. [Une boîte à outils pour les calculs et le texte](06-fonctions-nombres-chaines.md) : hasard, PI, mathématiques et manipulation des chaînes.
12. [Composer un écran et écouter le clavier](07-ecran-clavier.md) : PRINT, LOCATE, curseur, caractères personnels, triangles, lignes et indicateurs.
13. [Votre programme laisse une trace sur le papier](08-papier-dessins.md) : LPRINT, interligne, LLOCATE, géométrie, moteurs et glyphes.
14. [Atelier : une carte faite de petits dessins](08-atelier-tilemap.md) : un programme court et commenté pour découvrir les palettes et les rangées GLYPH.
15. [Faire du bruit et échanger des informations](09-sons-serie-memoire.md) : BEEP, SOUND, LOAD/SAVE, sessions série, PEEK et POKE.
16. [Trouver une erreur et améliorer son programme](10-erreurs-et-limites.md) : messages, limites et méthode de vérification.
17. [Programmes complets](11-programmes-complets.md) : Piano, Pocket Duel, Duel Orbital, Duel Balistique, les Ruines de Typestar et Canon S-70 Quest, avec leurs six listings et leurs commandes.
18. [Choisir ses caractères](12-table-caracteres.md) : palette LCD de Studio et police papier LPRINT.
19. [Annexe : schéma de la carte CPU](13-annexe-schema.md) : vue nettoyée et agrandissements fidèles au scan.
20. [Référence rapide du langage](98-reference-rapide.md)
21. [Lexique](99-lexique.md)
22. [Index alphabétique des commandes et fonctions](index-commandes.md)

La [table de caractères LPRINT](caracteres-lprint.md) fournit une référence supplémentaire de la police papier.

Le projet est indépendant de Canon et s'inspire de Microsoft BASIC sans en promettre une compatibilité totale. Le fonctionnement du câble avec le firmware Canon sur S-90 ne vaut pas validation de ce firmware BASIC sur cette machine. La S-70 reste la machine de référence ; le guide d’installation détaille la révision S-60 validée et le câblage de son extension série.

## Version paginée

Le **Markdown UTF-8 reste le source de référence**, avec un fichier par chapitre et une seule ligne par paragraphe. Les fichiers ne contiennent pas de retours forcés au milieu des phrases pour adapter le texte à une largeur particulière. Photos, schémas et légendes restent dans le dossier `images`.

Le [PDF français](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.100-dev/typestar-basic-manuel-fr.pdf) réunit les chapitres historiques et pratiques. Il possède des pages numérotées, un sommaire cliquable, des signets, les renvois de page du lexique et un index alphabétique des 86 mots-clés, fonctions et constante recensés. Sa pagination est recalculée après chaque modification ; aucune page n'est écrite à la main dans le Markdown. Cette édition accompagne la version publiée **0.4.100-dev** ; les deux PDF sont joints à la release GitHub. Les reconstructions locales sont produites dans `output/pdf/`.

## Utiliser Studio

Pour découvrir les outils, suivez le [chapitre illustré de Studio](02-studio.md). Pour charger et sauvegarder les programmes, ouvrez **Typestar BASIC Studio.pyw** et suivez le [chapitre sur la liaison série](09-sons-serie-memoire.md#save). Les boutons **Envoyer → LOAD** et **Recevoir ← SAVE** indiquent les deux directions ; aucun autre utilitaire de transfert n’est nécessaire.

Le [guide de construction](BUILDING.md) explique comment régénérer les éditions PDF.

Le [guide de conversion série de la S-60](../hardware/typestar-6-serial-upgrade.md) précise la révision testée, les références de prise et le câblage de RA1. L’édition actuelle décrit les rangées GLYPH de 1 à 40 motifs, les neuf modes du Piano, Duel Orbital 2.0, les Ruines de Typestar 0.6 et Canon S-70 Quest 0.9. Dans Quest, **RET passer / BS skip** passe l’impression ; le bassin de l’Oasis est en **26,6** et cinq slimes suffisent pour le niveau 2.
