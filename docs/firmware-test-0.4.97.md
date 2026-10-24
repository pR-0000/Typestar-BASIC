# Typestar BASIC 0.4.97-dev — rangées continues / continuous rows

## Français

### Binaire et programmes à tester

- ROM IC8 32 Ko : `../release/s70-basic-0.4.97-dev-canon-start-nh7.bin`.
- Image miroir 64 Ko : `../release/s70-basic-0.4.97-dev-canon-start-nh7-64k-mirror.bin`.
- [Canon S-70 Quest 0.3](../examples/games/canon-s70-quest-fr.bas), [notice](../examples/guides/canon-s70-quest.md).
- [Piano](../examples/piano-fr.bas), [notice](../examples/guides/piano.md).

**Quest :** utilisez ce nouveau listing avec ce firmware. Les 30 cases d'une rangée sont confiées à un seul appel natif. Les dessins restent aussi grands qu'en mode 4. La tête conserve le mode de continuation entre les motifs, y compris les cases entièrement vides ; un seul retour termine la rangée. La préparation BASIC se fait entre les rangées. Titres et coordonnées inclus, la carte emploie 35 transactions papier au lieu de 203. Le relevé complet passe d'environ 212 à 45 millions d'instructions dans l'émulateur ; le temps réel dépend aussi des moteurs.

**Piano :** les sons au clavier durent 75–90 ms, et les cadences des trois registres sont précalculées. Le registre initial commence à 523 Hz avant mélange. **Espace** joue la gamme MIX MINUS du diagnostic v3 vers **1 min 38** : huit sons de 320 ms, rapport 50 %, cadences 5365, 5301, 5229, 5190, 5105, 5009, 4901 et 4842. Les sons courts facilitent le jeu ; cette démonstration longue permet la comparaison acoustique. SOUND reste bloquant, et BREAK permet d'interrompre.

### Extension GLYPH


`GLYPH P(0),colonnes,8,5` imprime 1–32 motifs de 8×8 en grands pixels carrés. Les 64 premiers éléments du tableau contiennent une palette de 16 motifs : quatre mots de 16 bits par motif, chaque mot décrivant deux lignes de huit pixels. Les éléments suivants donnent les numéros 0–15 des motifs à imprimer. Cette forme utilise le cache et la continuation de LPRINT ; son avance suit LSPACING. Quest choisit `LSPACING 1`, soit 56 unités par rangée.

Le cache s'adapte à la mémoire disponible, jusqu'à un seul emplacement avec 316 octets libres. La source entière est vérifiée avant le premier mouvement. La commande conserve le tableau et les limites du tas BASIC ; la mémoire empruntée est libérée à la fin. Les modes 1–4 et leurs répétitions restent disponibles.

### Organisation et mémoire

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32768 octets |
| ROM hors réserve explicite | 32666 octets |
| Réserve ROM explicite | 102 octets fragmentés |
| RAM BASIC libre à vide | 5951 octets |
| Tokens / commandes | 37 / 54 |
| Quest FR / EN tokenisé | 4523 / 4515 octets |
| Minimum libre observé au démarrage de Quest | 730 octets |
| Piano FR / EN tokenisé | 2361 / 2360 octets |

Le catalogue de commandes partage sa terminaison avec l'adresse balisée du gestionnaire. Les lecteurs de mots acceptent cette représentation interne ; les 37 identifiants de tokens et le format des programmes conservés restent identiques. ORIGIN, CLEAR, KEYS et la préparation des glyphes sont regroupés après comparaison de leurs anciens octets avec les sources. Le décodeur Courier écrit directement dans l'ordre natif du cache. Les 95 dessins papier et les 1760 traductions clavier sont conservés. Les routines Canon de démarrage, calcul et moteurs ainsi que la maskROM gardent leurs emplacements et leurs octets.

### Vérification

Les rapports dans `build/tile-stream/` couvrent les rangées de 32 motifs, les cases vides, le remplacement d'un cache réduit à un motif, les limites des tableaux, BREAK physique, les pixels des anciens modes et le mode instantané de Studio. Ils vérifient aussi les 95 glyphes, le clavier, les 37 tokens, les 54 commandes, les formes d'onde, les durées, les neuf modes de Piano et ses 26 touches dans trois registres. Le démarrage complet de Quest et ses règles sont exercés par l'interpréteur.

Les essais sur la Canon restent nécessaires pour apprécier le mouvement continu de la tête et comparer le son au diagnostic v3. Construction : `tools/firmware/build_tile_stream.py`. Assemblage des images IC8 après contrôle des rapports : `tools/firmware/prepare_tile_stream.py`. Studio 0.2.38 reconnaît la nouvelle ROM et adapte ses accélérations graphiques aux octets du pilote.

### Retour sonore du 22 octobre 2026

L'analyse de `piano_espace.wav` compare les huit sons à la section 502 de v3. Les boucles réellement générées par .97 ont exactement les mêmes périodes élémentaires : 186, 189, 191, 193, 196, 200, 204 et 207 cycles. Deux notes ont une impulsion active plus courte d'un cycle, à cause d'un arrondi inférieur au lieu de l'arrondi au plus proche utilisé par le diagnostic. Le pilote SOUND rend la main au contrôle de durée et à la lecture physique de BREAK après 38–42 périodes, soit environ 8 ms. La commande reste alors à l'état bas. Cette pause est interne au pilote assembleur ; l'évaluation BASIC reprend entre les commandes SOUND.

L'enregistrement présente des composantes supplémentaires espacées de 123–126 Hz, en accord avec cette périodicité de service. Sur le premier son, la composante inférieure est à environ −13 dB de la composante principale. Les pics principaux associés à la modulation sont de 8–21 Hz plus hauts que ceux de v3, tandis que la composante propre au buzzer reste vers 5889 Hz. Cela explique une différence de timbre malgré les mêmes cadences demandées. Les intervalles acoustiques entre notes sont d'environ 35–60 ms, contre un enchaînement presque continu dans v3 ; ils comprennent la préparation des commandes et la réponse acoustique du buzzer. Ces observations désignent la continuité du pilote comme le prochain point à améliorer. Elles établissent une modulation audible, avec mélange et battements ; l'accordage musical sur plusieurs octaves reste à caractériser.

Analyse reproductible : `tools/diagnostics/analyze_piano_space.py`, avec les deux WAV en arguments. Rapport : `build/tile-stream/piano-space-audio-analysis.json`. Les périodes du code généré sont vérifiées au cycle près ; les spectres et enveloppes décrivent l'enregistrement. L'image du firmware et les statistiques mémoire restent celles de .97.

## English

### Firmware and programs to try

- 32 KiB IC8 ROM : `../release/s70-basic-0.4.97-dev-canon-start-nh7.bin`.
- 64 KiB mirrored image : `../release/s70-basic-0.4.97-dev-canon-start-nh7-64k-mirror.bin`.
- [Canon S-70 Quest 0.3](../examples/games/canon-s70-quest-en.bas), [guide](../examples/guides/canon-s70-quest.md#english).
- [Piano](../examples/piano-en.bas), [guide](../examples/guides/piano.md#english).

**Quest:** use this updated listing with the new firmware. A single native call handles all 30 tiles in a row, retaining mode 4's large artwork. The head remains in continuation mode between tiles, including fully blank tiles; one carriage return ends the row. BASIC preparation takes place between rows. Including titles and coordinates, the map uses 35 paper transactions instead of 203. The complete measurement drops from about 212 to 45 million emulator instructions; real elapsed time also depends on the motors.

**Piano:** keyboard sounds last 75–90 ms, and all three registers use precomputed rates. The initial register starts at 523 Hz before mixing. **Space** plays the MIX MINUS scale heard around **1:38** in the v3 diagnostic: eight 320 ms sounds at 50% duty, with rates 5365, 5301, 5229, 5190, 5105, 5009, 4901 and 4842. Short sounds make keyboard play more responsive; the long demonstration supports acoustic comparison. SOUND remains blocking, and BREAK interrupts it.

### GLYPH extension

`GLYPH P(0),columns,8,5` prints 1–32 tiles of 8×8 pixels using large square pixels. The first 64 array elements hold a palette of 16 tiles: four 16-bit words per tile, each word describing two eight-pixel rows. Following elements select tile numbers 0–15. This form uses LPRINT's cache and continuation path; paper advance follows LSPACING. Quest selects `LSPACING 1`, or 56 units per row.

The cache adapts to available memory, down to one slot with 316 free bytes. The complete source is checked before the first movement. The command preserves its array and BASIC heap boundaries, releasing borrowed memory afterwards. Modes 1–4 and their repetitions remain available.

### Layout and memory

| Resource | Value |
|---|---|
| IC8 ROM | 32768 bytes |
| ROM outside explicit reserve | 32666 bytes |
| Explicit ROM reserve | 102 fragmented bytes |
| Empty BASIC RAM | 5951 bytes |
| Token entries / commands | 37 / 54 |
| Tokenized Quest FR / EN | 4523 / 4515 bytes |
| Minimum free RAM during Quest startup | 730 bytes |
| Tokenized Piano FR / EN | 2361 / 2360 bytes |

The command catalogue shares its terminator with a tagged handler address. Keyword readers accept this internal representation; all 37 token identifiers and the stored program format remain identical. ORIGIN, CLEAR, KEYS and glyph preparation are regrouped after checking their old bytes against the sources. The Courier decoder writes directly in native cache order. All 95 paper glyphs and 1760 keyboard translations are retained. Canon startup, calculation and motor routines, and the maskROM, retain their locations and bytes.

### Verification

Reports in `build/tile-stream/` cover 32-tile rows, blanks, one-slot cache replacement, array bounds, physical BREAK, prior graphics pixels and Studio's instant mode. They also check all 95 glyphs, keyboard mappings, 37 tokens, 54 commands, waveforms, durations, all nine Piano modes and 26 keys in three registers. Quest's complete startup and rules run through the interpreter.

Canon hardware tests remain necessary to assess continuous head movement and compare the sound with v3. Build with `tools/firmware/build_tile_stream.py`; `tools/firmware/prepare_tile_stream.py` verifies reports before packaging IC8 images. Studio 0.2.38 recognizes the new ROM and matches graphics shortcuts to the driver's exact bytes.

### Sound feedback, 22 October 2026

Analysis of `piano_espace.wav` compares its eight sounds with v3 section 502. The kernels actually generated by .97 have exactly the same elementary periods: 186, 189, 191, 193, 196, 200, 204 and 207 cycles. Two notes have a one-cycle shorter active pulse because of rounding down, whereas the diagnostic rounds to nearest. SOUND returns to its duration check and physical BREAK scan after 38–42 periods, about every 8 ms. The gate remains low during that service pause. This occurs inside the assembly driver; BASIC expression evaluation resumes between SOUND commands.

The recording shows additional components spaced by 123–126 Hz, consistent with that service rate. On the first sound, the lower sideband is about −13 dB relative to the main component. The dominant modulation-related peaks are 8–21 Hz higher than v3's, while the buzzer's own component remains near 5889 Hz. This accounts for a timbre difference despite identical requested rates. Acoustic gaps between notes are about 35–60 ms, compared with nearly continuous transitions in v3; these include command preparation and the buzzer's acoustic response. These observations identify driver continuity as the next improvement. They establish audible modulation, mixing and beats; musical tuning across several octaves still requires characterization.

Reproduce with `tools/diagnostics/analyze_piano_space.py`, supplying both WAV files. Report: `build/tile-stream/piano-space-audio-analysis.json`. Generated-code periods are checked cycle exactly; spectra and envelopes describe the recording. The firmware image and memory statistics remain those of .97.
