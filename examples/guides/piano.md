# Piano

[Programme français / French program](../piano-fr.bas) · [English program](../piano-en.bas)

## Français

Avec le firmware **0.4.98-dev**, les lettres **A à Z** jouent des sons courts. Majuscules et minuscules conviennent ; **Entrée** termine le programme. Lancez Piano avec F5 dans Studio ou `RUN` sur la Canon.

**Gauche/droite** choisissent neuf modes : CLASSIC, MIX −, MIX +, PULSE, SWEEP, FADE, NOISE, CUT et HOLD. Les touches **1, 2, 3** choisissent les registres 0,5 / 1 / 2 ; **4, 5, 6** règlent le rapport cyclique à 10 / 50 / 90 %. PULSE/CUT utilisent leurs propres rapports, FADE les fait varier et NOISE/HOLD les ignorent.

**Espace** joue les huit sons longs de la gamme **MIX MINUS**, avec les cadences et les durées du passage vers **1 min 38 du diagnostic v3**. Chaque son dure 320 ms, avec un rapport de 50 %. Ce raccourci facilite la comparaison avec l'enregistrement. Le registre initial des lettres commence à 523 Hz avant mélange ; en MIX −, essayez **A, C, E, F, H, J, L, M**.

Les sons au clavier durent **75 à 90 ms**, contre 320 ms ou davantage auparavant. Les trois registres et les cadences de mélange/bruit sont **précalculés dans les DATA** ; les lectures de touches demandent moins de calculs. Maintenir une lettre la répète. SOUND attend la fin du son avant de lire la touche suivante ; **BREAK** est lu entre les sons. Maintenez-le jusqu'à la fin du son pour interrompre le programme sur la Canon. Chaque commande accepte au maximum deux secondes. Le programme occupe **2361 octets tokenisés** avant ses tableaux et ses variables.

Les cadences électriques produisent des battements et des mélanges avec le buzzer de la machine. L'écoute sur la Canon reste la référence pour le timbre et l'accordage ; Studio en donne un aperçu approximatif. Dans Studio, activez le son et choisissez votre sortie audio. En NOISE, **A/M/Y**, registre 1, donnent environ **2000/8000/31250 bits/s**.

Le pilote **.98** produit chaque son d'une seule traite. Les huit notes de la démonstration Espace utilisent les périodes et les impulsions exactes du diagnostic v3 ; les pauses périodiques de .97 sont retirées. La préparation BASIC reste présente entre les notes. La durée est quantifiée par périodes entières : jusqu'à 20 ms pour les cadences lentes et 31 ms pour le bruit. Le mode NOISE emprunte temporairement **672 octets libres**. Voir les [notes de test .98](../../docs/firmware-test-0.4.98.md).

## English

With firmware **0.4.98-dev**, letters **A to Z** play short sounds. Uppercase and lowercase both work; **Enter** exits. Run Piano with F5 in Studio or `RUN` on the Canon.

**Left/right** select nine modes: CLASSIC, MIX −, MIX +, PULSE, SWEEP, FADE, NOISE, CUT and HOLD. Keys **1, 2, 3** select registers 0.5 / 1 / 2; **4, 5, 6** set duty to 10 / 50 / 90%. PULSE/CUT use their own duty ratios, FADE varies them, and NOISE/HOLD ignore them.

**Space** plays the eight long sounds of the **MIX MINUS** scale, using the rates and durations of the passage around **1:38 in the v3 diagnostic**. Each sound lasts 320 ms at 50% duty. This shortcut makes comparison with the recording easier. The initial letter register starts at 523 Hz before mixing; in MIX −, try **A, C, E, F, H, J, L, M**.

Keyboard sounds last **75–90 ms**, previously 320 ms or longer. All three registers and mixed/noise rates are **precomputed in DATA**, reducing work between key reads. Holding a letter repeats it. SOUND waits for the sound to finish before reading the next key; **BREAK** is sampled between sounds. Hold it until the sound ends to interrupt the program on the Canon. Each command accepts a maximum of two seconds. The program occupies **2360 tokenized bytes** before its arrays and variables.

Electrical rates produce beats and mixing with the machine's buzzer. Listening on the Canon remains the reference for timbre and tuning; Studio gives an approximate preview. Enable sound and select your audio output in Studio. In NOISE, **A/M/Y** at register 1 give about **2000/8000/31250 bits/s**.

The **.98** driver plays each sound continuously. All eight notes in the Space demonstration use v3's exact periods and pulse widths; .97's periodic service pauses are removed. BASIC preparation still occurs between notes. Duration is quantized to whole cycles: up to 20 ms at slow rates and 31 ms for noise. NOISE temporarily borrows **672 free bytes**. See the [.98 test notes](../../docs/firmware-test-0.4.98.md#english).
