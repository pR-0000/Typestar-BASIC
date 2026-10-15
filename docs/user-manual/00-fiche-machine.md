# Typestar BASIC en un coup d'œil

**Un ordinateur 8 bits à clavier, LCD et imprimante A4**, construit autour du Hitachi **HD6301Y0P** de la Canon Typestar 7 / S-70. Le processeur d'origine exécute réellement vos programmes : le remplacement de la ROM IC8 lui donne un BASIC, tout en conservant les services de la ROM interne Canon.

> **32 caractères à l'écran - 5 951 octets libres - une imprimante intégrée.** Calculez, composez un jeu, créez vos personnages, puis donnez-leur une place sur le papier !

| Ressource | Typestar BASIC 0.4.88-dev sur S-70 |
|---|---|
| **Processeur** | HD6301Y0P, 8 bits ; horloge système d'environ **1 MHz**, à partir d'un quartz de 4 MHz. |
| **Mémoires** | **8 Ko de RAM externe** ; **5 951 octets libres à vide**, partagés entre programme tokenisé et données. ROM BASIC de **32 Ko**, ROM Canon interne de 16 Ko conservée. |
| **Programme et données** | Un programme ; lignes 1 à 65535, 63 caractères natifs par ligne, plusieurs instructions avec `:`. Variables numériques et texte ; tableaux numériques à une ou deux dimensions. |
| **Calculs** | Décimaux à **huit chiffres significatifs** ; hasard, PI, racine, trigonométrie, logarithme, exponentielle et opérateurs logiques. |
| **Écran et clavier** | **32 caractères de 5 × 7 pixels**, huit motifs personnels, triangles, lignes inférieures et indicateurs. Clavier multilingue de **44 touches**, selon la fiche Canon ; lecture des touches par INKEY. |
| **Texte imprimé** | **Courier 10 Canon**, 72 colonnes et 95 caractères ASCII ; LLIST, interligne réglable et positionnement par LLOCATE. Impression sur papier ordinaire avec ruban, ou directement sur papier thermique. |
| **Dessins imprimés** | Points, lignes, rectangles, cercles, contours et formes pleines. Glyphes personnels, agrandissement, déplacements de la tête et du papier. |
| **Sons** | BEEP et SOUND : pauses, bips et bruitages par modulation d'amplitude du buzzer ; modulation de 60 à 750 Hz, durée jusqu'à 2000 ms. |
| **Échanges avec un PC** | Câble USB adapté au port TTL 5 V ; LOAD/SAVE, émission et réception. Jusqu'à **31 250 bauds** ; réglage par défaut **31250 / 7E1**. |
| **Typestar BASIC Studio** | Éditeur, transfert, création de glyphes, émulation du LCD, du papier et du son ; impression d'images monochromes par CODE+P. |

## Le matériel que vous retrouvez sous le BASIC

Voici les principales caractéristiques de la Typestar 7 avec son logiciel Canon. Les vitesses de calcul et de dessin du BASIC dépendent du programme exécuté et des déplacements mécaniques. [C1]

| Caractéristique | Spécification Canon |
|---|---|
| Impression | Tête thermique de **32 × 26 points** ; 18 caractères par seconde annoncés avec le logiciel d'origine. |
| Papier | Largeur maximale **241 mm** ; largeur imprimable maximale **203 mm**. Une feuille A4 mesure 210 × 297 mm. |
| Clavier | 44 touches, multilingue ; pas de 19,05 mm, course de 4 mm. Le tampon de 80 caractères est celui du firmware Canon. |
| Alimentation | Quatre piles **R20 / D**, 6 V ; adaptateur Canon AD-6 ou bloc rechargeable en option. |
| Format et poids | **315 × 277 × 55,5 mm** ; environ **2,7 kg**, piles et cassette de ruban comprises. |

La tête physique, les glyphes exploités par le BASIC et les cellules du LCD sont trois choses distinctes.

La machine accepte le BASIC avec une ROM programmée dans IC8. Le câble et Studio facilitent les échanges avec un ordinateur. Le démarrage sur S-60 / Typestar 6 a également été essayé ; l’ajout d’un port série sur ce modèle est à l’étude. La S-90 / Typestar 7-II demande un portage adapté à ses ROM.

## Un processeur peu courant dans les ordinateurs personnels

La plupart des micro-ordinateurs familiers utilisent un Z80, un 6502 ou une autre famille bien connue. **Typestar BASIC permet de programmer un véritable HD6301**, plus souvent rencontré dans l'électronique embarquée. Il rejoint ainsi un petit groupe de machines personnelles utilisant cette famille Hitachi.

L’**Epson HX-20** utilise deux processeurs CMOS 6301. [E1] Le **Psion Organiser I** emploie un HD6301X à 0,9216 MHz. [I1] L’**Organiser II** utilise un **HD6303XFP** : ce cousin du HD6301 lit son programme dans une ROM extérieure, tandis que le HD6301 de la Typestar possède une ROM interne. Les deux familles partagent le jeu d’instructions de base ; leurs variantes se distinguent surtout par la mémoire et les périphériques intégrés. [I2] Des ordinateurs d’échecs emploient aussi des variantes HD6301, dont la V1.

## Quelques voisins à écran LCD

Ces appareils montrent ce que l’on pouvait faire avec une seule ligne d’affichage et peu de mémoire. **Le tableau compare leurs ressources et leurs usages.** La colonne mémoire précise, pour chaque appareil, la capacité totale ou la zone de programme annoncée.

| Machine | Processeur | LCD | Mémoire indiquée | Impression et programmation |
|---|---|---|---|---|
| **Typestar BASIC / S-70** | Hitachi HD6301Y0P | 1 × 32 | 8 Ko externes ; **5 951 octets libres** à vide | BASIC ; imprimante intégrée, texte et dessins sur A4. |
| **Sharp PC-1251** | Sharp SC61860 | 1 × 24 | 4 Ko de RAM ; **3 486 octets** dans la zone programme/données [S1] | BASIC ; imprimante et microcassette CE-125 en option. |
| **Psion Organiser I** | Hitachi HD6301X | 1 × 16 | 2 Ko de RAM ; 4 Ko de ROM et Datapak EPROM [I1] | Données et calculs ; programmation avec modules adaptés. |
| **VTech Laser 50** | Z80A [V3] | 1 × 16 | 2 192 octets de RAM annoncés ; extension de 16 Ko [V1] | BASIC, dix programmes P0 à P9 ; cassette et imprimante en option. |

Le PC-1251 réserve aussi de la RAM aux variables fixes et à une petite zone distincte. Pour le Laser 50, le tableau reprend la capacité annoncée dans la brochure. Son processeur appartient à la famille Z80 ; les composants Toshiba T7812/T7813 sont visibles sur les photographies de son circuit. [V2] [V3]

## Bien lire les chiffres du BASIC

Un Ko vaut ici **1 024 octets**. Les 5 951 octets libres sont partagés entre le programme et ses données. La tokenisation raccourcit les mots-clés : **MEM** mesure directement l’occupation en RAM, tandis que le fichier `.bas` conserve le texte lisible sur le PC.

Les dessins utilisent une fenêtre logique de **248 × 256 coordonnées**, avec un axe vertical quantifié. Les glyphes personnels et les moteurs permettent d'étendre les compositions sur la feuille ; le chapitre papier explique leurs unités.

SOUND module un buzzer à fréquence propre fixe. Les débits série décrivent les échanges avec le PC ; les calculs et les moteurs ont leur propre rythme. Le support des cartouches RAM est envisagé pour une version ultérieure.

[C1]: https://site.xavier.edu/polt/typewriters/CanonTypestar7.pdf

[E1]: https://electrickery.hosting.philpem.me.uk/comp/hx20/doc/om7-11ABC.pdf

[I1]: https://www.jaapsch.net/psion/p1manorg.htm

[I2]: https://www.jaapsch.net/psion/tech02.htm

[S1]: https://lastin.dti.supsi.ch/VET/sys/SHARP/PC-1251/PC-1250-PC-1251-Service_Manual.pdf

[V1]: references.md

[V2]: https://oldvcr.blogspot.com/2021/03/those-mysterious-toshiba-t-chips-plus.html

[V3]: https://sites.google.com/site/jamesskingdom/Home/computers-exposed/vtech-computers
