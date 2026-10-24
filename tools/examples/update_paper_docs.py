"""Refresh bilingual paper-game notes after the row-renderer update."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    p=ROOT/'examples/guides/ruines-typestar.md'
    text=p.read_text(encoding='utf-8').replace('— 0.4','— 0.6').replace('0.4.93-dev','0.4.98-dev')
    replacements={
        'Les dix dessins fournis': 'Les dix dessins fournis conservent exactement leurs **16 × 16 pixels**, leur taille et leurs asymétries. Chacun est partagé en quatre motifs de 8 × 8 pour le **mode 5 de GLYPH**, qui enchaîne des dessins différents, cases blanches comprises.',
        'Le jeu charge un motif': 'Le jeu imprime les parties hautes de toute une rangée, puis les parties basses. **Dix grands murs demandent toujours deux passes horizontales** ; les objets différents peuvent maintenant partager ces mêmes passes. Le mur et le sol gardent des emplacements fixes dans la palette ; cinq autres types peuvent être préparés par bande. Une rangée très variée est fractionnée quand cette palette est pleine. L’écran affiche **IMPRESSION CARTE 1/8** à **8/8**, pour les huit rangées du plan.',
        'Cet aperçu montre': 'Cet aperçu conserve la disposition prévue et la police papier du firmware. Les règles et les grands dessins restent ceux du jeu validé ; le regroupement en rangées est vérifié dans l’émulateur. La durée réelle dépend de la carte et des mouvements nécessaires.',
        'Le programme occupe': 'Le programme occupe **4 322 octets tokenisés** en français et **4 280** en anglais. Les tableaux utilisent **1 016 octets**, en-têtes compris : `M(79)` pour la carte, `G(83)` pour la palette et la rangée, `S(20)` pour les adresses des dessins, et `D(10)` pour leurs emplacements dans la palette. Les images restent stockées dans les DATA du programme ; une lecture PEEK parcourt les enregistrements documentés à partir de &H20C0 et retrouve les chaînes des lignes 2000 à 2009. Les adresses sont recalculées au lancement. Les règles conservent la difficulté de la version 0.4 : trois reliques gardées et 48 déplacements.',
        'Le rendu emploie': 'Le rendu de la carte appelle `GLYPH G(0),2*Q,8,5`, où Q est le nombre de grandes cases de la bande. Chaque case fournit deux petits motifs côte à côte. Le pas reste de **32 unités HEAD** et **112 unités FEED**. Les images compactes utilisent un octet d’échappement pour les valeurs réservées ; le décodage reconstruit les bitmaps d’origine. Le pilote adapte son cache à la mémoire disponible, avec au minimum 316 octets temporaires. Les pastilles et les croix gardent leur impression isolée en mode 4. B/C suivent les coordonnées et la routine moteur conserve ses mouvements découpés.',
        'The ten supplied drawings': 'The ten supplied drawings retain their exact **16 × 16 pixels**, size and asymmetries. Each is split into four 8 × 8 tiles for **GLYPH mode 5**, which streams different pictures, including blank cells.',
        'The game loads one motif': 'The game prints the upper parts across a complete row, then the lower parts. **Ten large walls still need two horizontal sweeps**; different objects can now share those same sweeps. Wall and floor have fixed palette slots; five other types can be prepared per band. A particularly varied row is split when that palette fills. The LCD shows **PRINTING MAP 1/8** through **8/8**, counting the eight map rows.',
        'This preview uses nominal': 'This preview retains the intended layout and firmware paper font. Rules and large artwork remain those of the validated game; row batching is checked in the emulator. Actual duration depends on the map and required movements.',
        'The French program uses': 'The French program uses **4,322 tokenized bytes**, the English program **4,280**. Arrays use **1,016 bytes**, including headers: `M(79)` for the map, `G(83)` for the palette and row, `S(20)` for artwork addresses, and `D(10)` for palette slots. Artwork remains in the program DATA; PEEK scans documented records from &H20C0 to locate strings on lines 2000 through 2009. Addresses are recalculated at startup. Rules retain version 0.4’s difficulty: three guarded relics and 48 moves.',
        'Printing uses `GLYPH': 'Map rendering calls `GLYPH G(0),2*Q,8,5`, where Q counts large cells in the band. Each cell supplies two small tiles side by side. Pitches remain **32 HEAD units** and **112 FEED units**. Compact artwork uses an escape byte for reserved values; decoding reconstructs the original bitmaps. The driver adapts its cache to available memory, requiring at least 316 temporary bytes. Dots and crosses retain their isolated mode 4 printing. B/C track coordinates and the motor routine retains its segmented movements.',
    }
    parts=text.split('\n\n')
    for i,part in enumerate(parts):
        for prefix,replacement in replacements.items():
            if part.startswith(prefix):parts[i]=replacement;break
    p.write_text('\n\n'.join(parts),encoding='utf-8')

    p=ROOT/'examples/guides/duel-orbital.md'
    text=p.read_text(encoding='utf-8').replace('Orbital Duel 1.8','Orbital Duel 1.9').replace('0.4.93-dev','0.4.98-dev')
    text=text.replace('avec le mode `GLYPH 4`','avec les grands pixels carrés de GLYPH')
    text=text.replace('using `GLYPH 4`','using GLYPH’s large square pixels')
    text=text.replace('Le programme français occupe **3 828 octets tokenisés**, l\'anglais **3 817**. Les tableaux de jeu B, C, H et Z utilisent **856 octets**', 'Le programme français occupe **3 827 octets tokenisés**, l\'anglais **3 816**. Les tableaux de jeu B, C, H et Z utilisent **981 octets**')
    text=text.replace('The French program uses **3,828 tokenized bytes**, the English **3,817**. Game arrays B, C, H and Z use **856 bytes**', 'The French program uses **3,827 tokenized bytes**, the English **3,816**. Game arrays B, C, H and Z use **981 bytes**')
    text=text.replace('### Impression continue et mémoire', 'Les satellites et les impacts utilisent désormais une palette de petits motifs en **GLYPH mode 5**. Une formation horizontale complète est imprimée en **deux passes**, avec les espaces entre ses cases conservés. Les formations verticales et les tirs isolés conservent leurs coordonnées ; chaque dessin garde exactement les pixels du modèle 16 × 16.\n\n### Impression continue et mémoire',1)
    text=text.replace('### Continuous printing and memory', 'Satellites and impacts now use a small-tile palette in **GLYPH mode 5**. A complete horizontal formation prints in **two passes**, preserving gaps between its cells. Vertical formations and individual shots retain their coordinates; each picture keeps the original 16 × 16 artwork exactly.\n\n### Continuous printing and memory',1)
    text=text.replace('Z les trois bitmaps.', 'Z la palette des trois dessins et la rangée à imprimer.')
    text=text.replace('Z the three bitmaps.', 'Z the three-picture palette and the row to print.')
    text=text.replace('Le dessin et le jeu ont été validés sur machine.', 'La grille conserve son tracé validé sur machine ; les nouvelles rangées de satellites sont contrôlées dans l’émulateur.')
    text=text.replace('Drawing and gameplay have been validated on hardware.', 'The grid retains its hardware-validated renderer; new satellite rows are checked in the emulator.')
    p.write_text(text,encoding='utf-8')


if __name__=='__main__':main()
