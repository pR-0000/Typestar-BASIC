# Typestar BASIC 0.4.95-dev — synthèse sonore / sound synthesis

## Français

Cette version intègre les résultats du diagnostic sonore v3, en conservant les extensions graphiques de la 0.4.94. Le seul signal commandé reste **le bit 6 de `$0034`**, avec préservation des autres bits du registre miroir `$1801`. La maskROM Canon, les réglages d'horloge, les moteurs et les pilotes série conservent leur code.

```basic
SOUND cadence,duree[,rapport[,texture]]
```

| Paramètre | Valeurs |
|---|---|
| `cadence` | 60 à 31250 Hz ; 0 pour une pause silencieuse |
| `duree` | 0 à 2000 millisecondes |
| `rapport` | 1 à 99 %, défaut 50 ; proportion de temps où la porte est ouverte |
| `texture` | 0 : onde carrée, défaut ; 1 : motif pseudo-aléatoire périodique de 31 bits |

La texture 1 utilise une cadence de **1000 à 31250 bits/s**. Son motif se répète tous les 31 bits et ignore le rapport cyclique. Elle demande **512 octets temporairement libres** entre les variables et le tas ; les limites d'allocation restent inchangées. L'onde carrée utilise 64 octets de travail déjà réservés. Une durée nulle reste silencieuse. `BEEP [duree]` commande la porte en continu, avec 100 ms par défaut.

```basic
10 SOUND 5500,180,50
20 SOUND 0,100
30 SOUND 8000,250,50,1
40 FOR D=10 TO 90 STEP 10:SOUND 5890,30,D:NEXT D
```

Le rapport règle **le niveau et le timbre**, selon une réponse dépendant de la cadence et de la mécanique du buzzer. Les plateaux sont arrondis à la microseconde, en supposant une horloge interne de 1 MHz. Chaque plateau actif dure au moins 5 cycles ; le dernier plateau inactif réserve au moins 12 cycles. À 31250 Hz, un rapport extrême est donc rapproché du rapport réalisable. La durée est contrôlée par lecture du Timer 1 existant, sans en modifier la configuration ; l'arrêt intervient en fin de groupe de périodes, avec une résolution allant jusqu'à environ 31 ms. BREAK reste interrogé entre ces groupes, sans consommer les autres touches.

**Les cadences sont des commandes électriques, pas des notes garanties.** Le diagnostic enregistré montre une composante fixe proche de 5889 Hz, des composantes dominantes réglables autour de 5–6,4 kHz et de riches produits de mélange. Les graves perçus peuvent venir des battements et des enveloppes. Ces observations permettent un synthétiseur de textures ; l'accordage de toutes les octaves reste à caractériser sur le matériel.

### Piano et Studio

[Piano français](../examples/piano-fr.bas) et [anglais](../examples/piano-en.bas) proposent neuf modes : CLASSIC, MIX −, MIX +, PULSE, SWEEP, FADE, NOISE, CUT, HOLD. **Gauche/droite** changent de mode, **A–Z** jouent, **1/2/3** changent le facteur de cadence, **4/5/6** sélectionnent 10/50/90 %, **Entrée** quitte. Voir la [notice bilingue](../examples/guides/piano.md).

Studio reconnaît cette ROM et conserve les attentes bloquantes. Son aperçu sonore prend en compte le rapport et le motif de bruit ; il représente les textures de manière approximative. La validation acoustique du nouveau pilote et de Piano se fait sur la Canon.

### Mémoire et vérifications

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32768 octets |
| Réserve ROM explicite | 66 octets fragmentés |
| ROM occupée hors réserve explicite | 32702 octets |
| RAM BASIC libre au démarrage | 5951 octets |
| Tokens / commandes | 37 / 54, inchangés |

Le pilote tient en ROM grâce à une compression sans perte des 40 tables clavier et de la police Courier 10 : normalisation des majuscules, parents et positions compacts, trois contextes Huffman, partage exact des glyphes miroirs. Les 1760 correspondances clavier et les 95 glyphes natifs de 93 octets ont été comparés intégralement à leur référence. Les temporaires sonores réutilisent l'espace de travail exclusif des commandes de liste et d'impression ; le programme et ses variables restent conservés.

La validation exécute les vraies instructions du parseur, du compilateur de formes d'onde et des boucles produites en RAM : périodes et rapports, motif v3, division, passage du compteur à zéro, durée, erreurs d'arguments, manque de mémoire et nettoyage sur BREAK. Piano est parcouru dans ses neuf modes en français et en anglais. Les tests graphiques antérieurs sont également rejoués. Les mesures de durée du banc utilisent une temporisation fonctionnelle pour les instructions ordinaires, et les cycles documentés pour les boucles critiques.

Construction : `tools/firmware/build_glyph_pair.py`, puis `tools/firmware/build_sound_synth.py`. Validation : `tools/diagnostics/validate_sound_synth.py`. Les rapports locaux se trouvent dans `build/sound-synth/`. Le conditionnement en image IC8/OneROM est assuré par `tools/firmware/prepare_sound_synth.py` après vérification des rapports.

## English

This version integrates the v3 sound survey while retaining .94 graphics. It drives only **bit 6 of `$0034`**, preserving the other `$1801` shadow bits. Canon maskROM, clock configuration, motors and serial drivers retain their code.

```basic
SOUND rate,duration[,duty[,texture]]
```

| Argument | Values |
|---|---|
| `rate` | 60–31250 Hz; 0 for a silent pause |
| `duration` | 0–2000 milliseconds |
| `duty` | 1–99%, default 50; proportion of time with the gate enabled |
| `texture` | 0: square gate waveform, default; 1: periodic 31-bit pseudo-random pattern |

Texture 1 accepts **1000–31250 bits/s**, repeats every 31 bits and ignores duty. It needs **512 temporarily free bytes** between variables and heap, without changing allocation boundaries. Square waves use an existing 64-byte work buffer. Zero duration stays silent. `BEEP [duration]` holds the gate enabled, defaulting to 100 ms.

Duty controls **level and timbre**, with a response depending on rate and the transducer. Plateaus are rounded to microseconds assuming a 1 MHz internal clock. Active plateaus need at least 5 cycles; the last inactive plateau reserves at least 12 cycles. Extreme duty ratios therefore approach the achievable ratio at 31250 Hz. Duration reads the existing Timer 1 without reconfiguring it. Playback stops at a batch boundary, with resolution up to about 31 ms. BREAK is sampled between batches without consuming other keys.

The four-line example above demonstrates square gating, silence, a noise texture and a duty envelope. **Electrical gate rates are not guaranteed musical notes.** The recording shows a fixed component near 5889 Hz, adjustable dominant components around 5–6.4 kHz and rich mixing products. Perceived low pitches may come from beats and envelopes. This supports texture synthesis; tuning across all octaves still needs hardware characterization.

### Piano and Studio

Both [French](../examples/piano-fr.bas) and [English](../examples/piano-en.bas) Piano provide nine modes: CLASSIC, MIX −, MIX +, PULSE, SWEEP, FADE, NOISE, CUT, HOLD. **Left/right** select modes, **A–Z** play, **1/2/3** change the rate multiplier, **4/5/6** select 10/50/90% duty, and **Enter** exits. See the [bilingual guide](../examples/guides/piano.md).

Studio recognizes the ROM and preserves blocking waits. Its preview includes duty and the noise pattern, as an approximate representation of the textures. Acoustic validation of the new driver and Piano takes place on the Canon.

### Memory and checks

The image remains **32768 bytes**, with **66 explicitly free fragmented bytes** and **32702 bytes outside that reserve**. Empty BASIC RAM remains **5951 bytes**; the **37 token entries and 54 commands** are unchanged. Lossless keyboard/font compression pays for the driver: case normalization, compact parent links and offsets, three Huffman contexts and exact mirrored glyph sharing. All **1760 keyboard mappings and 95 native 93-byte glyphs** match the reference. Sound borrows exclusive listing/printing work memory; programs and variables remain intact.

Regression tests execute real parser, waveform compiler and generated RAM instructions: period/duty timing, the v3 pattern, division, timer wrap, duration, invalid arguments, insufficient memory and BREAK cleanup. Both Piano versions exercise all nine modes. Previous graphics regressions are rerun. The duration harness uses functional timing for ordinary instructions and documented cycle counts for critical loops.

Build `tools/firmware/build_glyph_pair.py`, then `tools/firmware/build_sound_synth.py`; validate with `tools/diagnostics/validate_sound_synth.py`. Local reports live in `build/sound-synth/`. `tools/firmware/prepare_sound_synth.py` packages the IC8/OneROM image after checking the reports.
