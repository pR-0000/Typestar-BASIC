# Typestar BASIC 0.4.98-dev — son continu / continuous sound

## Français

- ROM IC8 32 Ko : `../release/s70-basic-0.4.98-dev-canon-start-nh7.bin`.
- Image miroir 64 Ko : `../release/s70-basic-0.4.98-dev-canon-start-nh7-64k-mirror.bin`.
- [Piano français](../examples/piano-fr.bas), [notice](../examples/guides/piano.md).

**SOUND produit désormais chaque son d'une seule traite.** Une boucle assembleur compte les périodes complètes, avec des temporisations intégrées au signal. Le contrôle périodique du temps et la lecture de BREAK sont remplacés par un calcul du nombre de périodes avant la lecture. Cela retire les pauses qui ajoutaient des composantes espacées d'environ 125 Hz dans l'enregistrement de .97.

La limite reste **2000 ms par commande** pour BEEP, SOUND et les pauses silencieuses. Le clavier est lu à nouveau après le son : maintenez **BREAK** jusqu'à sa fin pour interrompre le programme sur la Canon. Studio 0.2.39 applique aussi cette attente avec le nouveau profil.

Les impulsions sont arrondies au plus proche, avec les égalités arrondies à l'entier pair, comme dans le diagnostic v3. Les huit sons de la démonstration **Espace** de Piano ont exactement les mêmes plateaux actifs/inactifs que la section 502 de v3. Le programme Piano existant convient ; la préparation BASIC entre les commandes reste présente. L'enregistrement sur la Canon permettra d'apprécier le timbre obtenu.

La durée suit un nombre entier de cycles, arrondi vers le bas, avec au minimum un cycle pour une demande positive. Un cycle vaut une période en mode carré, ou un motif de 31 bits en mode bruit : résolution jusqu'à 20 ms pour les cadences lentes et 31 ms pour le bruit. Une durée zéro termine immédiatement la commande. Le motif de bruit emprunte temporairement **672 octets libres**, pour un noyau généré de 651 octets au maximum ; les sons carrés utilisent toujours le tampon de 64 octets.

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32768 octets |
| ROM hors réserve explicite | 32684 octets |
| Réserve ROM explicite | 84 octets fragmentés |
| RAM BASIC libre à vide | 5951 octets |
| Tokens / commandes | 37 / 54 |
| Durée demandée maximale | 2000 ms |
| Tampon temporaire carré / bruit | 64 / 672 octets |

Le compilateur de temporisations conserve X comme compteur de périodes et emploie D pour les délais. Un court appel indirect par la pile lance le code RAM, puis passe par la routine normale d'extinction du buzzer. Les registres de configuration des timers et de l'ASIC conservent leur fonctionnement ; seule la commande connue du buzzer est utilisée. Les blocs privés BASIC et leurs données sont replacés dans les plages ROM déjà auditées. Les routines Canon de démarrage, calcul et moteurs gardent leurs emplacements et leurs octets.

### Vérifications

Les rapports de `build/sound-continuous/` vérifient les huit références v3 sur 100 périodes consécutives chacune, les calculs de durée avec retenues et valeurs limites, le signal complet pendant deux secondes à 50 et 31250 Hz, l'absence de lecture clavier/timer durant le son, la remise au silence et la conservation de la pile et de la mémoire. Les 969 périodes possibles du bruit sont contrôlées pour la taille du noyau généré, avec exécution des cas les plus grands. Les essais couvrent aussi les 468 combinaisons du Piano, ses neuf modes en français/anglais, les glyphes papier, le clavier, les tokens, les rangées GLYPH et Quest.

Construction : `tools/firmware/build_sound_continuous.py`. Vérification et préparation des images : `tools/firmware/prepare_sound_continuous.py`. Le profil Studio est lié au hash exact du binaire testé. Les enregistrements confirment la continuité et les fréquences ; l'écart de timbre avec v3 reste étudié ci-dessous.

### Deuxième enregistrement Piano : fréquences et dynamique

Le fichier `panio_espace_2.wav` confirme la disparition des composantes parasites liées aux pauses de .97. Les huit pics associés à la modulation correspondent à la section **502, de 1:38 à 1:41**, du diagnostic v3 : environ 5403, 5317, 5262, 5207, 5127, 5025, 4926 et 4855 Hz. Ces fréquences acoustiques décrivent les composantes du signal enregistré ; les valeurs SOUND restent les cadences de commande de la porte du buzzer.

La dynamique demeure différente. Sur les fenêtres de comparaison de 200 ms, l'écart de niveau RMS entre les sons extrêmes est d'environ **15,7 dB dans v3 et 5,6 dB dans Piano**. Sur le dernier son, la composante vers 5889 Hz dépasse celle vers 4855 Hz d'environ 4,9 dB dans v3 ; elle se trouve environ 13,6 dB en dessous dans Piano. Cette redistribution d'énergie change le timbre et peut modifier la hauteur perçue. La cause acoustique ou matérielle reste à établir ; les enregistrements séparés incluent la réponse du microphone, la géométrie acoustique et un éventuel traitement automatique. Le correctif de continuité est confirmé, l'équivalence du rendu complet reste à vérifier.

Analyse reproductible : `tools/diagnostics/analyze_piano_space.py`, option `--build sound-continuous`. Rapport : `build/sound-continuous/piano-space-audio-analysis.json`.

### Diagnostic comparatif AB4b

Image temporaire IC8 32 Ko : `../release/s70-buzzer-ab-v4b-canon-start-nh7.bin` · Miroir 64 Ko : `../release/s70-buzzer-ab-v4b-canon-start-nh7-64k-mirror.bin`

Cette ROM de diagnostic remplace temporairement le BASIC. Après démarrage, appuyer sur **I/II** lance cinq passages, environ quinze secondes au total. Garder le microphone et la machine immobiles, avec un niveau d'enregistrement fixe si l'application le permet. L'écran indique :

| Passage | Boucle sonore | Enchaînement des huit sons |
|---|---|---|
| A1 V3 JOINED | Instructions originales de v3 | Continu |
| A2 V3 GAPS 50MS | Instructions originales de v3 | Pause de 50 ms entre sons |
| B1 SOUND JOINED | Noyaux RAM générés par .98 | Continu |
| B2 SOUND GAPS 50MS | Noyaux RAM générés par .98 | Pause de 50 ms entre sons |
| A1 V3 JOINED AGAIN | Répétition de la première référence | Continu |

Les touches **1 à 5** jouent un passage isolé. I/II relance l'ensemble ; réinstaller ensuite le firmware BASIC habituel. Les quatre variantes partagent le même démarrage Canon, les mêmes états de commande, les mêmes impulsions et les mêmes nombres de périodes. Le BASIC n'est pas exécuté pendant cette comparaison. Les pauses imposées représentent les intervalles entre commandes ; leur effet peut ainsi être distingué de celui des instructions utilisées pour produire le son. La répétition finale de A1 aide à repérer une évolution pendant l'enregistrement.

L'image reste de 32768 octets et contient **2175 octets de diagnostic** en remplacement du début de la ROM externe Canon. Les huit noyaux RAM occupent **384 octets empruntés puis restaurés**, de `$20C0` à `$223F`, ainsi que les dix octets de travail déjà employés par v3. Chaque octet copié et chaque valeur de commande modifiée sont relus avant exécution. Un échec affiche **RAM CHECK FAILED**, restaure les données empruntées et revient au clavier Canon. Les tests vérifient les huit paires de formes d'onde au cycle près, l'ordre des cinq passages, les pauses, la conservation des autres bits de commande, la restauration de la RAM, la pile et le retour clavier Canon. Ils exécutent aussi la troisième gamme complète sans raccourci de lecture et simulent trois échecs de copie. Le test isole les boucles et les pauses dans un même contexte Canon ; un éventuel effet propre à l'initialisation BASIC reste distinct de cet essai.

Construction et validation : `tools/diagnostics/build_buzzer_ab_v4.py` et `tools/diagnostics/validate_buzzer_ab_v4.py`. Les binaires sont produits après réussite des contrôles logiciels.

### Retour matériel AB4 : deux passages enregistrés

Le fichier `buzzer_survey_v4.wav`, de **6,269 secondes**, contient A1 puis A2. L'utilisateur a lancé I/II et observé un retour de la tête à gauche après ces deux gammes. Les passages B1, B2 et la répétition finale de A1 restent donc à mesurer. L'ancien AB4 plaçait ses noyaux à `$1000`, une zone de travail acceptée par le banc logiciel mais sans validation matérielle. L'arrêt coïncide avec la première exécution dans cette zone. **AB4b emploie désormais l'arène RAM documentée du BASIC et vérifie les écritures avant exécution.** Ce défaut concerne le diagnostic AB4 ; les sons du BASIC .98 utilisent leur propre allocation.

Les huit composantes de commande correspondent encore à v3. Sur les fenêtres centrales de 200 ms, les niveaux A2 diffèrent de A1 de **−0,41 à +0,87 dB** selon le son. Les pauses de 50 ms modifient donc peu l'enveloppe mesurée dans cet essai. La répartition des niveaux entre sons diffère de l'ancien enregistrement v3, même avec les boucles originales exécutées depuis la ROM et sans interpréteur BASIC. Le septième son est particulièrement atténué dans ce nouvel enregistrement. L'étendue totale des niveaux est proche de **15,0 dB pour A1, 15,3 dB pour A2 et 15,7 dB dans v3** ; ces étendues voisines masquent une distribution différente entre les huit sons. Le traitement d'enregistrement, la géométrie acoustique, la machine utilisée et son état préalable restent des variables à distinguer. Ce fichier établit une différence de rendu ; il permet seulement la comparaison A1/A2, pas encore ROM/RAM.

Analyse reproductible : `tools/diagnostics/analyze_buzzer_ab_v4.py enregistrement.wav v3.wav`. Rapport conservé dans `build/buzzer-ab-v4/audio-analysis.json`, avec les hashes des deux fichiers et le statut explicite **full_suite_recorded: false**. Le prochain essai utilise **AB4b**, avec I/II ; l'écran doit parcourir les cinq passages et terminer par **END AB4b - I/II REPLAY** après environ quinze secondes.

### Retour matériel AB4b : comparaison complète

Le fichier `buzzer_survey_v4b.wav`, de **15,197 secondes**, contient les cinq passages attendus, soit quarante sons. Les départs acoustiques sont situés vers **0,130 s, 3,028 s, 6,276 s, 9,174 s et 12,422 s**. Les huit composantes associées à la commande correspondent entre les noyaux ROM et RAM : environ **5403, 5317, 5262, 5207, 5128, 5025, 4926 et 4855 Hz**. Les écarts des pics ajustés restent dans un pas de la grille FFT suréchantillonnée ; la fenêtre de 200 ms limite la résolution spectrale réelle. Les niveaux sont mesurés sur ces mêmes fenêtres centrales.

| Comparaison dans ce fichier | Observation |
|---|---|
| Boucles ROM puis RAM, sans pauses | Écarts RMS par son de −0,48 à +3,28 dB ; fréquences correspondantes. |
| Boucles ROM puis RAM, avec pauses | Écarts RMS par son de −0,68 à +2,68 dB ; fréquences correspondantes. |
| ROM, ajout des pauses de 50 ms | Écarts RMS de −0,18 à +1,11 dB. |
| RAM, ajout des pauses de 50 ms | Écarts RMS de −1,02 à +0,52 dB. |
| Première et dernière lecture de la même gamme ROM | Le premier son gagne **4,16 dB** ; le rapport entre la composante à 5889 Hz et celle à 5403 Hz diminue de **9,31 dB**. |

Le témoin répété établit que le rendu évolue pendant l'enregistrement à instructions identiques. Pour le premier son, cet écart dépasse celui entre la première lecture ROM et la lecture RAM. Une comparaison A/B directe confond donc le changement de noyau et cette évolution dans le temps. Les boucles SOUND reproduisent les fréquences des références, et les pauses seules ont un effet modeste dans ce fichier. **L'équivalence complète du timbre et du volume reste distincte de cette validation des fréquences.** L'essai utilise le démarrage Canon pour les cinq passages ; il caractérise les noyaux générés par .98, plutôt que tout le contexte d'exécution du BASIC.

La composante fixe vers 5889 Hz s'atténue progressivement alors que plusieurs composantes de commande conservent leur niveau ou augmentent. Un traitement adaptatif du microphone, notamment une réduction du bruit, pourrait contribuer à ce phénomène ; le déplacement du microphone et une évolution de l'état matériel restent également possibles. La cause reste ouverte. Le prochain contrôle utile consiste à reprendre ce même diagnostic en gardant la géométrie fixe et en désactivant les traitements du microphone, plutôt qu'à modifier à nouveau les temporisations sur cette seule base. Le fichier 8 bits présente un échantillon à une valeur extrême par canal, soit environ **0,00015 %** : un écrêtage fréquent n'explique pas ces observations.

Analyse : `tools/diagnostics/analyze_buzzer_ab_v4.py enregistrement.wav v3.wav --build buzzer-ab-v4b --full-suite`. Le rapport `build/buzzer-ab-v4b/audio-analysis.json` conserve les hashes, les quarante mesures, les cinq comparaisons et **full_suite_recorded: true**. Le découpage des fenêtres centrales en deux moitiés de 100 ms conserve le constat sur le premier son : environ **+4,2 puis +4,1 dB** entre les lectures ROM initiale et finale. Le défaut d'arrêt observé avec AB4 ne se reproduit pas dans cet enregistrement.

### Jeux papier, atelier et Studio 0.2.40

Les capacités sonores de cette version sont retenues après les essais. La ROM reste identique. Les programmes des **Ruines 0.5** et de **Duel Orbital 1.9** utilisent maintenant le mode 5, en français et en anglais. Quest utilisait déjà les rangées ; les autres jeux dessinent avec le LCD ou les commandes géométriques adaptées à leur contenu.

Les Ruines conservent leurs bitmaps 16 × 16, en préparant leurs quatre petits motifs dans une palette par bande. Le mur et le sol ont des emplacements permanents ; cinq autres types tiennent dans la même bande. Une rangée plus variée est fractionnée. Les images compactes restent dans les DATA ; S mémorise leurs adresses trouvées en parcourant les enregistrements à partir de &H20C0. Le programme utilise **4323 / 4282 octets tokenisés FR/EN**, et ses quatre tableaux **1016 octets**. Une exécution complète d'une carte de contrôle termine l'impression, avec 38 transactions papier et 51 retours de tête, contre 45 et 127 pour l'ancien rendu sur cette carte. La préparation BASIC ajoute du calcul ; ces nombres décrivent les mouvements, pas le temps gagné sur la Canon.

Duel Orbital conserve la grille répétée, déjà imprimée ensemble sur toute sa largeur. Les satellites et les deux impacts utilisent une palette de douze petits motifs. Une formation horizontale complète est imprimée en deux passes. Les programmes utilisent **3827 / 3816 octets FR/EN**, et les tableaux **981 octets**. Une comparaison des trois dessins répétés trois fois donne 7 retours de tête au lieu de 27, déplacements de positionnement compris.

Les tests `tools/examples/validate_paper_games.py --focused` et `validate_orbital_rows.py` exécutent le BASIC et les pilotes de la ROM .98. Ils comparent toutes les marques des dix dessins des Ruines et des trois dessins d'Orbital aux références, avec leurs coordonnées. L'oracle retire uniquement les pas supplémentaires de compensation Y de son repère idéal : les moteurs virtuels idéaux n'ont pas le jeu mécanique compensé par ces pas. La ROM et son exécution gardent la compensation réelle ; les événements bruts et les corrections sont conservés dans les rapports. Les tests couvrent les sources françaises et anglaises, le remplacement d'une palette pleine et la mémoire disponible. Après la carte, le programme recharge les données de la croix et de la pastille.

L'[atelier tilemap](user-manual/08-atelier-tilemap.md) fournit deux sources commentées, la palette, le plan et une illustration issue du pilote émulé : **24 motifs, quatre passes** dans les deux langues. Les deux manuels PDF sont reconstruits, avec 89 blocs BASIC contrôlés par édition. Studio fournit une petite police pour les octets U+E080–U+E0FF : les glyphes affichent leur code hexadécimal. Les tests vérifient les 128 glyphes, les thèmes clair/sombre et la conservation exacte des sources, sélections et octets tokenisés de Quest et des Ruines. Les PDF emploient aussi cette police pour ces octets dans les listings.

## English

- 32 KiB IC8 ROM : `../release/s70-basic-0.4.98-dev-canon-start-nh7.bin`.
- 64 KiB mirrored image : `../release/s70-basic-0.4.98-dev-canon-start-nh7-64k-mirror.bin`.
- [English Piano](../examples/piano-en.bas), [guide](../examples/guides/piano.md#english).

**SOUND now plays each sound continuously.** An assembly loop counts complete cycles, with delays integrated into the signal. Periodic time checks and BREAK scans are replaced by a cycle-count calculation before playback. This removes the pauses that added components spaced by about 125 Hz in the .97 recording.

The limit remains **2000 ms per command** for BEEP, SOUND and silent pauses. Keyboard scanning resumes after the sound: hold **BREAK** until it ends to interrupt the program on the Canon. Studio 0.2.39 follows this behavior with the new profile.

Pulse widths round to nearest, with ties to even, matching diagnostic v3. All eight sounds in Piano's **Space** demonstration use exactly the same on/off plateaus as v3 section 502. The existing Piano program works; BASIC preparation between commands remains. A Canon recording will establish the resulting timbre.

Duration follows a whole number of cycles, rounded down, with at least one cycle for a positive request. A cycle is one period for square gating or a 31-bit pattern for noise: resolution reaches 20 ms at slow rates and 31 ms for noise. Zero duration returns immediately. Noise temporarily borrows **672 free bytes**, for a generated kernel of at most 651 bytes; square sounds still use the 64-byte buffer.

| Resource | Value |
|---|---|
| IC8 ROM | 32768 bytes |
| ROM outside explicit reserve | 32684 bytes |
| Explicit ROM reserve | 84 fragmented bytes |
| Empty BASIC RAM | 5951 bytes |
| Token entries / commands | 37 / 54 |
| Maximum requested duration | 2000 ms |
| Temporary square / noise buffer | 64 / 672 bytes |

The delay compiler keeps X as its cycle counter and uses D for delays. A short stack-based indirect call launches the RAM code, then passes through normal buzzer cleanup. Timer and ASIC configuration retain their operation; only the known buzzer gate is used. Private BASIC blocks and data are repacked within previously audited ROM regions. Canon startup, calculation and motor routines retain their locations and bytes.

### Verification

Reports in `build/sound-continuous/` check all eight v3 references over 100 consecutive periods each, duration arithmetic with carries and boundary values, complete two-second waveforms at 50 and 31250 Hz, absence of keyboard/timer reads during sound, gate cleanup and stack/memory preservation. All 969 possible noise periods are checked for generated kernel size, with execution of the largest cases. Checks also cover Piano's 468 combinations, all nine modes in French/English, paper glyphs, keyboard mappings, tokens, GLYPH rows and Quest.

Build with `tools/firmware/build_sound_continuous.py`; verify and package with `tools/firmware/prepare_sound_continuous.py`. The Studio profile is linked to the tested binary's exact hash. Recordings confirm continuity and frequencies; the timbre difference from v3 remains under investigation below.

### Second Piano recording: frequencies and dynamics

The file `panio_espace_2.wav` confirms removal of the spurious components associated with .97's service pauses. All eight modulation-related peaks match diagnostic v3 **section 502, from 1:38 to 1:41**: approximately 5403, 5317, 5262, 5207, 5127, 5025, 4926 and 4855 Hz. These acoustic frequencies describe recorded signal components; SOUND parameters still specify buzzer gate command rates.

Dynamics remain different. Across the 200 ms comparison windows, the RMS level range is about **15.7 dB in v3 and 5.6 dB in Piano**. On the last sound, the component near 5889 Hz exceeds the 4855 Hz component by about 4.9 dB in v3; it is about 13.6 dB below it in Piano. This energy redistribution changes timbre and may alter perceived pitch. Its acoustic or hardware cause remains unresolved; separate recordings include microphone response, acoustic geometry and possible automatic processing. Continuity is confirmed; equivalence of the complete acoustic result still needs investigation.

Reproduce with `tools/diagnostics/analyze_piano_space.py --build sound-continuous`. Report: `build/sound-continuous/piano-space-audio-analysis.json`.

### AB4b comparison diagnostic

Temporary 32 KiB IC8 image : `../release/s70-buzzer-ab-v4b-canon-start-nh7.bin` · 64 KiB mirror : `../release/s70-buzzer-ab-v4b-canon-start-nh7-64k-mirror.bin`

This diagnostic ROM temporarily replaces BASIC. After startup, press **I/II** to play five sections, about fifteen seconds in total. Keep the microphone and machine stationary, using fixed recording gain if available. The LCD shows:

| Section | Sound loop | Eight-sound transitions |
|---|---|---|
| A1 V3 JOINED | Original v3 instructions | Continuous |
| A2 V3 GAPS 50MS | Original v3 instructions | 50 ms pause between sounds |
| B1 SOUND JOINED | RAM kernels generated by .98 | Continuous |
| B2 SOUND GAPS 50MS | RAM kernels generated by .98 | 50 ms pause between sounds |
| A1 V3 JOINED AGAIN | Repeat of the first reference | Continuous |

Keys **1–5** play individual sections. I/II repeats the complete sequence; reinstall the usual BASIC firmware afterwards. All four variants share Canon startup, command states, pulse widths and period counts. BASIC does not execute during this comparison. Imposed pauses represent inter-command intervals, separating their effect from that of the instructions producing the sound. The final A1 repeat helps detect changes during recording.

The image remains 32768 bytes, with **2175 diagnostic bytes** replacing the beginning of Canon's external ROM. Its eight RAM kernels use **384 borrowed bytes, restored afterwards**, from `$20C0` through `$223F`, plus the ten work bytes already used by v3. Every copied byte and patched command value is read back before execution. Failure displays **RAM CHECK FAILED**, restores borrowed data and returns to Canon's keyboard. Checks verify all eight waveform pairs cycle exactly, sequence order, pauses, unrelated control-bit preservation, RAM/stack restoration and the Canon keyboard return ABI. They also execute the entire third scale without skipping playback and inject three copy failures. This test isolates loops and pauses in a common Canon context; a possible BASIC initialization effect remains a separate question.

Build and validate with `tools/diagnostics/build_buzzer_ab_v4.py` and `tools/diagnostics/validate_buzzer_ab_v4.py`. Binaries are packaged after software checks pass.

### AB4 hardware result: two recorded sections

The **6.269-second** file `buzzer_survey_v4.wav` contains A1 followed by A2. The user pressed I/II and observed the carriage returning left after those two scales. B1, B2 and the final A1 repeat therefore still need measurement. The old AB4 placed kernels at `$1000`, a scratch region accepted by the software harness but without hardware validation. The interruption coincides with the first execution in that region. **AB4b now uses BASIC's documented RAM arena and checks writes before execution.** This defect concerns the AB4 diagnostic; BASIC .98 sounds use their own allocation.

All eight gate-related components still match v3. Across central 200 ms windows, A2 levels differ from A1 by **−0.41 to +0.87 dB** depending on the sound. Thus 50 ms pauses have little effect on the measured envelope in this trial. Relative levels between sounds differ from the earlier v3 recording even with original ROM loops and no BASIC interpreter running. The seventh sound is particularly attenuated in this recording. The overall level ranges are about **15.0 dB for A1, 15.3 dB for A2 and 15.7 dB in v3**; these similar ranges conceal different distributions across the eight sounds. Recording processing, acoustic geometry, machine identity and prior hardware state remain variables to separate. This file establishes an acoustic difference and supports an A1/A2 comparison, but does not yet compare ROM with RAM.

Reproduce with `tools/diagnostics/analyze_buzzer_ab_v4.py recording.wav v3.wav`. The report in `build/buzzer-ab-v4/audio-analysis.json` retains both file hashes and explicitly records **full_suite_recorded: false**. Use **AB4b** for the next trial and press I/II: the LCD should show all five sections, ending with **END AB4b - I/II REPLAY** after about fifteen seconds.

### AB4b hardware result: complete comparison

The **15.197-second** file `buzzer_survey_v4b.wav` contains all five expected sections, or forty sounds. Acoustic starts occur around **0.130 s, 3.028 s, 6.276 s, 9.174 s and 12.422 s**. The eight gate-related components match between ROM and RAM kernels: approximately **5403, 5317, 5262, 5207, 5128, 5025, 4926 and 4855 Hz**. Fitted peak differences remain within one bin of the zero-padded FFT grid; the 200 ms window limits actual spectral resolution. Levels use the same central windows.

| Comparison within this recording | Observation |
|---|---|
| ROM then RAM loops, joined | Per-sound RMS differences from −0.48 to +3.28 dB; matching frequencies. |
| ROM then RAM loops, paused | Per-sound RMS differences from −0.68 to +2.68 dB; matching frequencies. |
| ROM, adding 50 ms pauses | RMS differences from −0.18 to +1.11 dB. |
| RAM, adding 50 ms pauses | RMS differences from −1.02 to +0.52 dB. |
| First and last playback of the same ROM scale | The first sound gains **4.16 dB**; its 5889 Hz to 5403 Hz component ratio decreases by **9.31 dB**. |

The repeated control establishes a change during recording with identical instructions. For the first sound, this difference exceeds that between initial ROM playback and RAM playback. A direct A/B comparison therefore conflates kernel changes with this time-dependent variation. SOUND kernels reproduce reference frequencies, and pauses alone have a modest effect in this file. **Complete timbre and volume equivalence remains separate from this frequency validation.** All five sections share Canon startup; this trial characterizes .98-generated kernels rather than the entire BASIC execution context.

The fixed component near 5889 Hz progressively weakens while several gate-related components retain or increase their level. Adaptive microphone processing, particularly noise suppression, could contribute; microphone movement and a changing hardware state are also possible. The cause remains open. The next useful control is to repeat this same diagnostic with fixed acoustic geometry and microphone processing disabled, rather than adjust timing again on this evidence alone. The 8-bit file has one extreme-valued sample per channel, about **0.00015%**: frequent clipping does not explain these observations.

Analyze with `tools/diagnostics/analyze_buzzer_ab_v4.py recording.wav v3.wav --build buzzer-ab-v4b --full-suite`. The report in `build/buzzer-ab-v4b/audio-analysis.json` retains file hashes, forty measurements, five comparisons and **full_suite_recorded: true**. Splitting central windows into two 100 ms halves preserves the first-sound observation: about **+4.2 then +4.1 dB** between initial and final ROM playback. The interruption observed with AB4 does not recur in this recording.

### Paper games, workshop and Studio 0.2.40

Current sound capabilities are retained following the trials. The ROM is unchanged. **Ruins 0.5** and **Orbital Duel 1.9** now use mode 5 in French and English. Quest already used streaming rows; other games use their LCD or suitable geometric commands.

Ruins retains its 16 × 16 artwork, preparing four small tiles per picture in a per-band palette. Wall and floor have permanent slots; five other types fit in the same band. More varied rows are split. Compact artwork stays in DATA; S records its addresses by scanning program records from &H20C0. Programs use **4323 / 4282 tokenized bytes FR/EN**, and their four arrays **1016 bytes**. A complete control-map run finishes printing with 38 paper transactions and 51 carriage returns, compared with 45 and 127 for the old renderer on that map. BASIC preparation adds computation; these counts describe movement, not elapsed time saved on the Canon.

Orbital Duel retains its repeated grid, already printed together across the full width. Satellites and both impact pictures use a twelve-tile palette. A complete horizontal formation prints in two passes. Programs use **3827 / 3816 bytes FR/EN**, and arrays **981 bytes**. Comparing all three pictures repeated three times gives 7 carriage returns instead of 27, including positioning movements.

Tests `tools/examples/validate_paper_games.py --focused` and `validate_orbital_rows.py` execute BASIC and the .98 ROM drivers. They compare every mark and coordinate of Ruins' ten pictures and Orbital's three pictures against the references. The comparison oracle excludes only additional Y-compensation steps from its ideal coordinate frame: ideal virtual rollers lack the mechanical play those steps compensate. The ROM and its execution retain actual compensation; reports retain raw events and corrections. Checks cover French/English sources, replacement of a full palette and available memory. After map printing, the program reloads the dot and cross data.

The [tilemap workshop](user-manual/en/08-atelier-tilemap.md) provides two commented sources, palette, plan and an illustration from the emulated driver: **24 tiles, four passes** in both languages. Both manual PDFs are rebuilt, with 89 BASIC blocks checked per edition. Studio bundles a small font for U+E080–U+E0FF bytes, displaying their hexadecimal codes. Checks cover all 128 glyphs, light/dark themes and exact preservation of Quest/Ruins sources, selections and tokenized bytes. PDF listings use this font for those bytes too.
