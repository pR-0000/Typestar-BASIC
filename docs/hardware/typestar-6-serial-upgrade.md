# Typestar 6 / S-60 : BASIC et port série / BASIC and serial upgrade

[Français](#français) · [English](#english)

## Français

Le firmware **Typestar BASIC 0.4.93-dev** fonctionne sur la **Canon S-60 / Typestar 6** testée. L'ajout de l'interface série permet les transferts de programmes avec **Typestar BASIC Studio jusqu'à 31250 bauds, 7E1**, avec le même câble USB-TTL que la S-70. Le remplacement de la ROM IC8 se fait sur support ; l'ajout du circuit série demande des soudures.

### Reconnaître la carte validée

- PCB **NG3-0672 / NH1-0159-065**, daté **« 86;06,12. »**.
- Petite trappe prévue pour le port série, **collée en usine** sur cet exemplaire.
- Molette de contraste d'impression placée à l'avant, comme sur la S-70.
- Microcontrôleur d'origine **HD6301Y0P**, marqué **NH7-0815**, conservé en IC9 ; **IC8 reçoit directement le firmware BASIC**.

Des S-60 avec une coque sans trappe et une molette sur la tranche droite ont également été observées. La validation concerne la carte ci-dessus ; les autres révisions et la S-61 restent à caractériser.

### Composants

| Emplacement | Montage validé |
|---|---|
| CN7 | **DE-9 mâle coudée pour PCB**. Référence de la prise S-70 : **AMP 8609 747109-1** ; référence mécanique à comparer : **TE Connectivity / AMP 5745001-3**. Un équivalent de stock ancien a servi à l'essai. Vérifier les perçages et fixations avec le [plan constructeur](https://www.te.com/en/product-5745001-3.html). |
| IC4 | **Texas Instruments CD4050BE**, DIP-16, testé à la place du **Fujitsu MB84050B**. Alimentation : **broche 1 au +5 V**, **broche 8 à la masse**. |
| R77, R78, R79 | **4,7 kΩ** chacune, en série respectivement avec **CN7.4, CN7.2, CN7.7**. |
| RA1 | Réseau mixte reconstruit avec **trois résistances de 4,7 kΩ et trois de 22 kΩ**, suivant le tableau ci-dessous. |

### Les six résistances de RA1

**La broche 7 est la pastille identifiée sur le PCB par un petit carré : elle est reliée au +5 V.** Depuis cette extrémité, compter 7, 6, 5, 4, 3, 2, 1. La gauche et la droite dépendent du côté depuis lequel la carte est regardée.

| Pastille RA1 | Connexion relevée |
|---|---|
| 1 | CN7.5, IF_ENABLE# |
| 2 | IC4.3 |
| 3 | CN7.3, RXD depuis le PC |
| 4 | IC4.7 |
| 5 | CN7.6, IF_PRESENT# |
| 6 | IC4.9 |
| 7, carré | +5 V |

| Résistance entre pastilles | Valeur | Fonction |
|---|---|---|
| **1–2** | **4,7 kΩ** | Série IF_ENABLE# |
| **3–4** | **4,7 kΩ** | Série RXD |
| **5–6** | **4,7 kΩ** | Série IF_PRESENT# |
| **1–7** | **22 kΩ** | Rappel IF_ENABLE# au +5 V |
| **3–7** | **22 kΩ** | Rappel RXD au +5 V |
| **5–7** | **22 kΩ** | Rappel IF_PRESENT# au +5 V, état défini câble débranché |

RA1 assure **à la fois des liaisons série et des rappels**. Un réseau de six résistances en étoile autour d'un point commun fournit seulement les rappels : il manque les trois paires série 1–2, 3–4 et 5–6. Le montage ci-dessus est une reconstruction fonctionnelle validée sur cette carte, plutôt qu'une identification du réseau Canon marqué « 7071 63 ».

Effectuer le montage hors tension, secteur, piles et câble USB retirés. Isoler les connexions puis vérifier les liaisons, l'orientation d'IC4 et les résistances avant remise sous tension. Le port et le câble travaillent en **TTL 5 V**. Le [chapitre d'installation illustré](../user-manual/02-installation-firmware.md#s60-serial) complète ce relevé ; le [câblage du câble USB](../user-manual/02-presentation-firmware.md#serial-cable) précise les contacts Canon et les deux résistances de détection dans le câble.

## English

**Typestar BASIC 0.4.93-dev** runs on the tested **Canon S-60 / Typestar 6**. Adding the serial interface enables program transfers with **Typestar BASIC Studio at up to 31250 baud, 7E1**, using the same USB-TTL cable as the S-70. IC8 ROM replacement is socketed; adding the serial components requires soldering.

### Identifying the tested board

- PCB **NG3-0672 / NH1-0159-065**, dated **"86;06,12."**.
- A small factory-provided serial-port hatch, **glued shut** on this machine.
- Print-contrast control at the front, as on the S-70.
- Original **HD6301Y0P** MCU marked **NH7-0815** retained at IC9; **IC8 receives the BASIC firmware directly**.

S-60 machines with no hatch and a contrast control on the right-hand side have also been observed. Validation applies to the board above; other revisions and the S-61 remain to be characterized.

### Components

| Position | Tested arrangement |
|---|---|
| CN7 | **Right-angle male DE-9 PCB connector**. S-70 connector marking: **AMP 8609 747109-1**; mechanical reference for comparison: **TE Connectivity / AMP 5745001-3**. A new-old-stock equivalent was used in the test. Compare the mounting holes and fixings with the [manufacturer drawing](https://www.te.com/en/product-5745001-3.html). |
| IC4 | **Texas Instruments CD4050BE**, DIP-16, tested in place of the **Fujitsu MB84050B**. Supply: **pin 1 to +5 V**, **pin 8 to ground**. |
| R77, R78, R79 | **4.7 kΩ** each, in series with **CN7.4, CN7.2, CN7.7**, respectively. |
| RA1 | Mixed network rebuilt with **three 4.7 kΩ and three 22 kΩ resistors**, wired as shown below. |

### RA1's six resistors

**Pin 7 is the pad identified by a small square on the PCB: it connects to +5 V.** Count 7, 6, 5, 4, 3, 2, 1 from that end. Left/right orientation depends on which side of the board is viewed.

| RA1 pad | Measured connection |
|---|---|
| 1 | CN7.5, IF_ENABLE# |
| 2 | IC4.3 |
| 3 | CN7.3, RXD from the PC |
| 4 | IC4.7 |
| 5 | CN7.6, IF_PRESENT# |
| 6 | IC4.9 |
| 7, square | +5 V |

| Resistor between pads | Value | Function |
|---|---|---|
| **1–2** | **4.7 kΩ** | IF_ENABLE# series resistor |
| **3–4** | **4.7 kΩ** | RXD series resistor |
| **5–6** | **4.7 kΩ** | IF_PRESENT# series resistor |
| **1–7** | **22 kΩ** | IF_ENABLE# pull-up to +5 V |
| **3–7** | **22 kΩ** | RXD pull-up to +5 V |
| **5–7** | **22 kΩ** | IF_PRESENT# pull-up to +5 V, defining the unplugged state |

RA1 provides **both series connections and pull-ups**. A six-resistor star network around one common pin supplies only pull-ups: it omits the three series pairs 1–2, 3–4 and 5–6. This is a functional reconstruction validated on the tested board, rather than an identification of the Canon network marked "7071 63".

Fit components with mains, batteries and USB disconnected. Insulate connections and check continuity, IC4 orientation and resistor values before applying power. The port and cable use **5 V TTL** levels. The [illustrated installation chapter](../user-manual/en/02-installation-firmware.md#s60-serial) supplements these measurements; the [USB cable wiring](../user-manual/en/02-presentation-firmware.md#serial-cable) identifies the Canon contacts and the two detection resistors inside the cable.
