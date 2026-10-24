# Typestar BASIC 0.4.96-dev — Piano et Quest / Piano and Quest

## Français

Cette version conserve la synthèse sonore et les extensions graphiques des candidats .94/.95. Le pilote sonore compte désormais les millisecondes avec moins de travail entre les groupes de périodes. Le banc d'instructions mesure des interruptions maximales plus courtes : environ **223 µs contre 551 µs**, autour de 2–8 kHz, avec une temporisation fonctionnelle hors des boucles critiques. L'écoute sur la Canon reste la référence pour le timbre.

`SOUND cadence,duree[,rapport[,texture]]` accepte maintenant **50 à 31250 Hz**, ou zéro pour une pause. Les autres paramètres restent : 0–2000 ms, rapport 1–99 %, texture 0 (carré) ou 1 (motif périodique de 31 bits, cadence ≥1000, 512 octets temporairement libres). Le signal utilise toujours le bit 6 de `$0034`, en préservant les autres bits de `$1801`. La maskROM, la configuration du timer, les moteurs et la liaison série conservent leur code.

### Essayer Piano

Chargez le nouveau [Piano](../examples/piano-fr.bas), puis essayez **MIX −, MIX +, PULSE, SWEEP, FADE, NOISE et CUT**. Les cadences transposées sont arrondies en entiers : le registre bas des anciennes versions produisait des demi-valeurs rejetées par SOUND. Les divisions lentes des expressions courantes ont été remplacées par des multiplications ; les cadences NOISE sont précalculées dans un tableau. Les impulsions/coupures à 50 Hz, le balayage 5000–8000 Hz et les plateaux d'enveloppe retrouvent les réglages du diagnostic v3. En NOISE, **A/M/Y**, facteur 1, donnent environ **2000/8000/31250 bits/s**. Voir la [notice bilingue](../examples/guides/piano.md).

Les fréquences électriques produisent des battements et des mélanges avec le buzzer : elles offrent des hauteurs perçues variées, dont l'accordage musical dépend du matériel. Studio reconnaît la nouvelle image et conserve son aperçu sonore approximatif.

### Essayer Quest

Le [prototype 0.2](../examples/guides/canon-s70-quest.md) corrige les numéros de lignes : `LPRINT ...;` laisse le papier à la même hauteur, et le suivi de position le prend désormais en compte. Les deux en-têtes sont espacés et les seize numéros de lignes alternent entre deux colonnes pour conserver la taille Courier sans chevauchement. Les cases claires/sable reçoivent des guides pointillés. Deux motifs sont assemblés dans une bande ; les couples identiques suivants sont imprimés à la suite en réutilisant le tampon. Le cache des quinze motifs est décodé avant l'impression, puis libéré avant le jeu. La carte passe de 250 à **184 groupes de motifs**, soit **26,4 % de groupes en moins** ; le temps total inclut aussi les calculs BASIC et les moteurs.

Les combats utilisent **ATK/DEF/OBJ/FUIR**, avec statistiques et inventaire sur trois écrans, repos/potions/épée/armure +1/+2, niveaux requis 2/4/6/8/10 et croix sur les cases des gardiens vaincus. Deux victoires initiales donnent le niveau 2. Les magasins, les actions de combat, les gains et les cinq gardiens sont vérifiés dans l'émulateur ; les fixtures de campagne raccourcissent les déplacements et fixent le niveau de départ de chaque région.

### Mémoire et validation

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32768 octets |
| ROM hors réserve explicite | 32701 octets |
| Réserve ROM explicite | 67 octets fragmentés |
| RAM BASIC libre à vide | 5951 octets |
| Tokens / commandes | 37 / 54 |

Les vérifications couvrent les 95 glyphes Courier 10, 1760 traductions clavier, 17 cas de formes d'onde/durée, le timer, les erreurs d'arguments, la mémoire et BREAK ; les neuf modes de Piano dans les deux langues, ses 26 notes dans trois registres, et les régressions graphiques sont également testés.

Construction : `build_glyph_pair.py`, `build_sound_synth.py`, puis `build_sound_steady.py`, dans `tools/firmware/`. Rapports dans `build/sound-steady/`. `prepare_sound_steady.py` contrôle les rapports avant de produire les images IC8 32 Ko et miroir 64 Ko dans `release/`.

## English

This version retains .94/.95 sound synthesis and graphics. The sound scheduler accounts for elapsed milliseconds with less work between waveform batches. The instruction harness measures shorter maximum gaps: roughly **223 µs instead of 551 µs** around 2–8 kHz, using functional timing outside critical loops. Listening on the Canon remains the reference for timbre.

`SOUND rate,duration[,duty[,texture]]` now accepts **50–31250 Hz**, or zero for silence. Other parameters remain 0–2000 ms, 1–99% duty and texture 0 (square) or 1 (periodic 31-bit pattern, rate ≥1000, 512 temporarily free bytes). Only `$0034` bit 6 is driven, preserving the other `$1801` shadow bits. MaskROM, timer configuration, motors and serial code are unchanged.

### Trying Piano

Load the new [Piano](../examples/piano-en.bas) and try **MIX −, MIX +, PULSE, SWEEP, FADE, NOISE and CUT**. Transposed rates are rounded to integers: the old low register could produce half-integers rejected by SOUND. Slow divisions in common expressions are replaced by multiplications; NOISE rates are precomputed in an array. The 50 Hz pulses/cuts, 5000–8000 Hz sweep and envelope plateaus restore v3 diagnostic settings. In NOISE, **A/M/Y** at multiplier 1 produce about **2000/8000/31250 bits/s**. See the [bilingual guide](../examples/guides/piano.md).

Electrical rates produce beats and mixing with the buzzer, offering varied perceived pitches whose musical tuning depends on the hardware. Studio recognizes the new image and retains its approximate audio preview.

### Trying Quest

[Prototype 0.2](../examples/guides/canon-s70-quest.md#english) fixes row labels: `LPRINT ...;` keeps the paper at the same height, and position tracking now accounts for this. The two headers are spaced apart, and all sixteen row labels alternate between two columns to retain legible Courier digits without overlap. Clear/sand tiles gain dotted guides. Two tiles form one strip; matching subsequent pairs print consecutively using the same buffer. All fifteen tiles are decoded and cached before printing, then released before play. The map drops from 250 to **184 tile groups**, **26.4% fewer groups**; total elapsed time also includes BASIC preparation and motors.

Combat uses **ATK/DEF/ITM/FLEE**, with three status/inventory pages, rest/potions/sword/armor +1/+2, required levels 2/4/6/8/10 and crosses on defeated guardian tiles. Two initial victories reach level 2. Shops, combat actions, rewards and all five guardians are checked in the emulator; campaign fixtures shorten travel and set each region's initial level.

### Memory and validation

IC8 remains **32768 bytes**, with **32701 bytes outside the explicit reserve**, **67 fragmented reserve bytes**, **5951 free BASIC RAM bytes**, **37 token entries and 54 commands**.

Checks cover all 95 Courier 10 glyphs, 1760 keyboard translations, 17 waveform/duration cases, timer wrap, invalid arguments, memory guards and BREAK. Both Piano languages exercise nine modes; 26 notes in three registers and prior graphics regressions are also tested.

Build `build_glyph_pair.py`, `build_sound_synth.py`, then `build_sound_steady.py` in `tools/firmware/`. Reports live in `build/sound-steady/`. `prepare_sound_steady.py` verifies reports before producing 32 KiB IC8 and mirrored 64 KiB images in `release/`.
