# Tilemap papier / Paper tilemap

## Français

Ouvrez [tilemap-fr.bas](tilemap-fr.bas) dans **Typestar BASIC Studio**. Ce programme commenté dessine une pièce et un coffre en **quatre passes horizontales**, avec le mode rapide **GLYPH 5**.

Le tableau **G** contient deux zones : **G(0) à G(63)** pour les pixels de la palette, **G(64) à G(69)** pour les six numéros de motifs de la rangée à imprimer. C'est le format attendu par GLYPH 5. La palette reste prête pendant que la rangée est remplacée à chaque passe.

**READ** parcourt les valeurs DATA dans l'ordre des lignes BASIC, de gauche à droite. Les premiers READ prennent les 16 rangées de pixels des dessins ; `G(I)=256*A+B` assemble les rangées deux par deux. Les READ suivants continuent avec les numéros des cases du plan. **GLYPH lit le tableau préparé**, et les numéros de ligne servent à ordonner le programme et les DATA. Le [chapitre du manuel](../../docs/user-manual/08-atelier-tilemap.md) détaille ce parcours avec des tableaux pas à pas.

Les dessins gardent **une ligne DATA par rangée de 8 pixels**. Les DATA des lignes **450 à 480** décrivent le plan : **0** est le sol, **1** le mur et **2** le coffre. Modifiez ces valeurs pour déplacer le coffre ou ouvrir une porte.

Le [catalogue LCD de S-70 Quest](s70-quest-sprites-fr.bas) propose aussi huit dessins **5 × 7**, avec une ligne DATA par rangée de pixels. [Planche des sprites](s70-quest-sprites.png) · [Pixels en JSON](s70-quest-sprites.json).

## English

Open [tilemap-en.bas](tilemap-en.bas) in **Typestar BASIC Studio**. This commented program draws a room and a chest in **four horizontal passes**, using fast **GLYPH mode 5**.

Array **G** has two sections: **G(0) through G(63)** for palette pixels, **G(64) through G(69)** for the six picture numbers in the map row to print. This is the format GLYPH 5 expects. The palette stays ready while the map row is replaced on each pass.

**READ** follows DATA values in BASIC line order, from left to right. The first READ statements take the pictures' 16 pixel rows; `G(I)=256*A+B` combines rows in pairs. Subsequent READ statements continue with the plan's cell numbers. **GLYPH reads the prepared array**, and line numbers determine the order of the program and its DATA. The [manual chapter](../../docs/user-manual/en/08-atelier-tilemap.md) walks through this process in tables.

Pictures retain **one DATA line per row of 8 pixels**. DATA on lines **450 through 480** describes the plan: **0** is floor, **1** wall and **2** chest. Change these values to move the chest or open a doorway.

The [S-70 Quest LCD catalogue](s70-quest-sprites-en.bas) also provides eight **5 × 7** pictures, with one DATA line per pixel row. [Sprite sheet](s70-quest-sprites.png) · [JSON pixels](s70-quest-sprites.json).
