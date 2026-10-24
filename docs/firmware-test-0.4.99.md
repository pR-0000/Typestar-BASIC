# Typestar BASIC 0.4.99-dev — tracés papier et jeux / paper graphics and games

## Français

- ROM IC8 32 Ko : `../release/s70-basic-0.4.99-dev-canon-start-nh7.bin`.
- Miroir 64 Ko pour W27C512 : `../release/s70-basic-0.4.99-dev-canon-start-nh7-64k-mirror.bin`.
- [S-70 Quest 0.4](../examples/guides/canon-s70-quest.md), [Duel Orbital 2.0](../examples/guides/duel-orbital.md), [sprites LCD 5 × 7](../examples/graphics/s70-quest-sprites.png).

Le sélecteur papier distingue explicitement la composition géométrique, un glyphe et une rangée de motifs. Une composition revenait auparavant dans le sélecteur LPRINT, puis dans ce même sélecteur, ce qui bloquait notamment la bordure droite de Duel Orbital. BOX, LINE et CIRCLE retrouvent leur parcours de dessin.

L'entrée historique de LINE avait aussi perdu une partie de son contrôle de coordonnées lors du rangement du clavier en 0.4.95. Les enregistrements graphiques passent déjà ce contrôle avant la soumission. Le compositeur appelle désormais directement `PLVALID`, dont le corps est vérifié octet par octet contre la version 0.4.94. Les limites publiques de coordonnées et d'épaisseur restent vérifiées avant l'impression.

**GLYPH mode 5 accepte 1 à 40 motifs**, toujours avec une palette de seize dessins 8 × 8. Le tampon de rangée utilise au plus 40 des 64 octets disponibles. Les modes 1 à 4 gardent leurs dimensions précédentes. Les deux grilles de Duel Orbital utilisent 37 motifs par bande, bordure droite comprise, en seize passages continus. Le tableau Q occupe 514 octets ; le cache de cette grille utilise jusqu'à 508 octets temporaires.

Quest propose **Entrée : imprimer / BACKSPACE : garder la carte**. Trois premières victoires donnent le niveau 2 ; le coût en expérience augmente ensuite et les adversaires se renforcent après les gardiens. Une potion prend un tour. Les huit silhouettes LCD sont distinctes, les PV laissent une case vide devant les sprites, et les pertes du tour apparaissent au centre sans effacer les personnages. Les versions FR/EN et leurs notices sont mises à jour. Les Ruines affiche **CHARGEMENT** au démarrage.

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32 768 octets |
| ROM hors réserve explicite | 32 709 octets |
| Réserve ROM explicite | 59 octets fragmentés |
| RAM BASIC libre à vide | 5 951 octets |
| Tokens / commandes | 37 / 54 |
| Rangée GLYPH 5 | 1–40 motifs, palette de 16 |
| Quest FR / EN | 4 865 / 4 851 octets tokenisés |
| Duel Orbital FR / EN | 3 850 / 3 839 octets tokenisés |

Construction : `tools/firmware/build_paper_grid.py`. Préparation des images : `tools/firmware/prepare_paper_grid.py`. Les rapports de `build/paper-grid/` couvrent le mélange des producteurs graphiques, les rangées de 37 et 40 motifs, le cache réduit, BREAK, les modes de glyphes précédents, les 95 caractères papier, les 1 760 traductions clavier, les tokens et commandes, et les sons continus. Les essais des jeux exécutent le BASIC tokenisé avec les ROM réelles : choix de carte, impression de Quest, progression et cinq gardiens, grille complète de Duel Orbital jusqu'au placement. Le temps mécanique, l'alignement sur papier et l'équilibrage ressenti restent à confirmer sur machine.

## English

- 32 KiB IC8 ROM : `../release/s70-basic-0.4.99-dev-canon-start-nh7.bin`.
- 64 KiB W27C512 mirror : `../release/s70-basic-0.4.99-dev-canon-start-nh7-64k-mirror.bin`.
- [S-70 Quest 0.4](../examples/guides/canon-s70-quest.md#english), [Orbital Duel 2.0](../examples/guides/duel-orbital.md#english), [5 × 7 LCD sprites](../examples/graphics/s70-quest-sprites.png).

The paper selector explicitly distinguishes a geometric composition, a single glyph and a tile row. A composition previously returned through the LPRINT selector into the same selector, blocking Orbital Duel's right border in particular. BOX, LINE and CIRCLE follow their drawing paths again.

Part of LINE's historical coordinate validator was also lost when keyboard data was repacked in 0.4.95. Graphics records already pass these checks before submission. The compositor now enters `PLVALID` directly; its body is checked byte for byte against 0.4.94. Public coordinate and stroke limits remain checked before printing.

**GLYPH mode 5 accepts 1–40 tiles**, retaining the sixteen-picture 8 × 8 palette. Row staging uses at most 40 of the available 64 bytes. Modes 1–4 retain their previous dimensions. Orbital Duel's two grids use 37 tiles per band, including the right edge, in sixteen continuous sweeps. Array Q takes 514 bytes; this grid's cache takes up to 508 temporary bytes.

Quest offers **Enter: print / Backspace: keep the map**. Three initial victories reach level 2; experience costs then increase and enemies grow stronger after guardians. A potion takes a turn. All eight LCD silhouettes are distinct, HP leaves a blank cell beside the sprites, and turn damage appears in the centre while characters stay visible. French/English versions and guides are updated. Ruins displays **LOADING** at startup.

| Resource | Value |
|---|---|
| IC8 ROM | 32,768 bytes |
| ROM outside explicit reserve | 32,709 bytes |
| Explicit ROM reserve | 59 fragmented bytes |
| Empty BASIC free RAM | 5,951 bytes |
| Tokens / commands | 37 / 54 |
| GLYPH 5 row | 1–40 tiles, 16-picture palette |
| Quest FR / EN | 4,865 / 4,851 tokenized bytes |
| Orbital Duel FR / EN | 3,850 / 3,839 tokenized bytes |

Build with `tools/firmware/build_paper_grid.py`; package using `tools/firmware/prepare_paper_grid.py`. Reports in `build/paper-grid/` cover mixed graphics producers, 37/40-tile rows, reduced cache, BREAK, previous glyph modes, all 95 paper characters, 1,760 keyboard translations, tokens and commands, and continuous sound. Game checks execute tokenized BASIC with the actual ROMs: map selection, Quest printing, progression and five guardians, and Orbital Duel's complete grid through to placement. Mechanical timing, paper alignment and perceived game balance still need confirmation on hardware.
