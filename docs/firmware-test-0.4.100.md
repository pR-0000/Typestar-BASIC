# Typestar BASIC 0.4.100-dev — audit avant publication / pre-publication audit

## Français

- [ROM IC8 32 Ko](../firmware/0.4.100-dev/typestar-basic-32k.bin).
- [Miroir 64 Ko pour W27C512](../firmware/0.4.100-dev/typestar-basic-64k-mirror.bin).
- [Manifeste et rapports](../firmware/0.4.100-dev/validation-summary.json).

### Correctif

Le texte `?FOR/NEXT` partageait sa terminaison avec l'ancien mot-clé `NEXT`. Le rangement des données en ROM avait remplacé cette terminaison par des octets de police. Une erreur de boucle pouvait donc afficher des caractères illisibles. Le message possède désormais son propre stockage ; ses deux références historiques pointent vers le texte complet. Le bandeau de démarrage est également déplacé pour accueillir le numéro de version à trois chiffres.

Les fonctions de la 0.4.99 sont conservées, notamment les rangées GLYPH de 40 motifs et les corrections du sélecteur graphique et du traceur LINE. Les routines moteur et la compensation Y de 1/4 restent identiques.

### Résultats

Les essais exécutent le code HD6301 de l'image finale avec la maskROM NH7-0815. Chaque rapport identifie cette image par SHA-256. La préparation des binaires exige **seize rapports réussis correspondant exactement à ce hash**.

- **ROM :** 10 108 instructions accessibles, 22 742 octets de code et 127 allocations ; contrôle des chevauchements et des sauts directs vers les zones de données ou de réserve répertoriées. Les cibles connues des répartiteurs de commandes et des trois services moteur sont incluses.
- **Données :** 25 messages d'erreur complets, bandeau, anciennes valeurs des patches et couverture exacte des zones réaffectées. Un bloc de 2 560 octets comprenant les services moteur natifs reste identique à la version de référence.
- **BASIC :** 114 cas couvrant les décimaux, priorités, mathématiques, logique, MOD, chaînes, tableaux numériques, DATA/READ, IF/ELSE, appels et huit niveaux de boucles, erreurs et reprise.
- **Mémoire :** 96 insertions/remplacements/suppressions, lignes 1–65535 et CRC vérifié après chaque édition. À mémoire pleine, un échec d'insertion ou d'agrandissement conserve le programme existant.
- **Démarrage :** cinq scénarios avec interruptions mécaniques simulées : programme valide, RAM de travail remplie de FF et série perturbée, mauvais CRC, enregistrement corrompu, signature absente. Le programme valide de 5 949 octets est conservé ; les données invalides sont réinitialisées.
- **Série :** 30 couples vitesse/format, en émission et réception : 1200, 2400, 7812, 15625 et 31250, en 7N1/7N2/7E1/7E2/7O1/7O2. Protocole LOAD/SAVE complet, accents et lignes de 63 octets ; huit scénarios d'erreur ou d'interruption avec fermeture propre.
- **Saisie et affichage :** INPUT numérique redemandé après une réponse vide ou incorrecte, INPUT texte vide et ponctuation, effacement et curseur par défaut après erreur.
- **Papier :** anciens modes GLYPH, rangées mixtes et vides jusqu'à 40 motifs, cache réduit, BREAK, BOX/LINE/CIRCLE après LPRINT et GLYPH, préservation des variables et tableaux. LLIST complet et par plage, avec substitution `?` pour les caractères propres au LCD.
- **Police et clavier :** 95 glyphes papier comparés aux références, 1 760 traductions clavier, 37 tokens et 54 liens de commande.
- **Son :** huit formes de référence v3, compteurs, 969 périodes de bruit, limites de tampon et reprise après BREAK ; 468 appels Piano sur 26 touches, trois registres et six modes dépendant de la touche.
- **Jeux :** Quest FR/EN — choix de carte, carte complète, déplacements, magasins, progression, défaite et cinq gardiens ; Duel Orbital FR/EN — deux grilles complètes, bordure droite comprise, jusqu'au placement.

### Ressources

| Ressource | Valeur |
|---|---|
| ROM IC8 | 32 768 octets |
| ROM hors réserve explicite | 32 710 octets |
| Réserve ROM explicite | 58 octets fragmentés |
| RAM BASIC libre à vide | 5 951 octets |
| Tokens / commandes | 37 / 54 |
| Tampon temporaire du bruit | 672 octets |

### Reproduction et contrôle matériel

Depuis la racine du dépôt, avec l'environnement Python de Studio et les dépendances de diagnostic :

```powershell
studio/.venv/Scripts/python.exe tools/firmware/build_release_candidate.py
studio/.venv/Scripts/python.exe tools/diagnostics/run_release_audit.py
studio/.venv/Scripts/python.exe tools/firmware/prepare_release_candidate.py
```

Les rapports complets sont produits dans `build/release-candidate/` et `build/release-audit-0.4.100/`. La construction incrémentale exige encore l'assembleur A09, les ROM Canon et les étapes antérieures disponibles dans l'environnement de développement. Une seconde construction a produit le même hash CPU : `e864a52bec0d7caab2db0e9c87d6aa0afeee6e5d74ca0424e7c25589a84336ec`.

Le parcours statique porte sur IC8 et les zones décrites par le manifeste ; les calculs et démarrages exécutent les services de la maskROM lors des essais. Le démarrage utilise un modèle mécanique fonctionnel. Les tests de pixels emploient aussi les accélérations papier de Studio, avec comparaison des parcours natifs représentatifs ; les essais sonores contrôlent séparément les noyaux aux cycles comptés. La précision physique du papier, les niveaux sonores, les tensions du câble et les conditions réelles de mise sous tension se vérifient sur machine. Cette couverture de régression s'enrichira avec les futurs programmes et essais matériels.

Avant diffusion, le contrôle matériel conseillé est court : conserver puis redémarrer un gros programme, faire un LOAD/SAVE dans Studio, lancer une impression de Quest ou Duel Orbital, jouer quelques sons du Piano, puis vérifier une erreur `NEXT` dans un petit programme séparé. Les jeux et programmes habituels pourront ensuite servir à l'essai prolongé.

## English

- [32 KiB IC8 ROM](../firmware/0.4.100-dev/typestar-basic-32k.bin).
- [64 KiB W27C512 mirror](../firmware/0.4.100-dev/typestar-basic-64k-mirror.bin).
- [Manifest and reports](../firmware/0.4.100-dev/validation-summary.json).

### Fix

The `?FOR/NEXT` message shared its ending with the old `NEXT` keyword. Repacking ROM data replaced that ending with font bytes, so a loop error could display unreadable characters. The message now has independent storage, and both historical references point to the complete text. The startup banner also moves to accommodate the three-digit version number.

The 0.4.99 features are retained, including 40-tile GLYPH rows and the graphics-selector and LINE-rasterizer fixes. Motor routines and the 1/4 Y compensation remain identical.

### Results

Checks execute the final image's HD6301 code with the NH7-0815 maskROM. Each report identifies the image by SHA-256. Packaging requires **sixteen passing reports matching that exact hash**.

- **ROM:** 10,108 reachable instructions, 22,742 code bytes and 127 allocations; checks for overlapping instructions and direct jumps into listed data/free regions. Known command-dispatch targets and all three indirect motor-service targets are included.
- **Data:** 25 complete error messages, startup banner, original patch bytes and exact coverage of reclaimed regions. A 2,560-byte block containing native motor services remains identical to the reference version.
- **BASIC:** 114 cases covering decimals, precedence, mathematics, logic, MOD, strings, numeric arrays, DATA/READ, IF/ELSE, calls and eight loop levels, errors and recovery.
- **Memory:** 96 insert/replace/delete operations, line numbers 1–65535 and CRC checked after every edit. Failed insertion or growth at capacity preserves the existing program.
- **Startup:** five scenarios with simulated mechanical interrupts: valid program, FF-filled work RAM with disturbed serial state, bad CRC, malformed record, missing signature. The valid 5,949-byte program is retained; invalid data is reset.
- **Serial:** 30 baud/format combinations, with transmit/receive: 1200, 2400, 7812, 15625 and 31250 at 7N1/7N2/7E1/7E2/7O1/7O2. Complete LOAD/SAVE protocol, accents and 63-byte lines; eight failure/interruption scenarios with proper closure.
- **Input and display:** numeric INPUT retries empty/invalid answers, empty and punctuated string INPUT, clear screen and default cursor after errors.
- **Paper:** earlier GLYPH modes, mixed/blank rows through 40 tiles, reduced cache, BREAK, BOX/LINE/CIRCLE after LPRINT and GLYPH, preserved variables/arrays. Full/ranged LLIST and `?` substitution for LCD-only characters.
- **Font and keyboard:** 95 paper glyphs compared with references, 1,760 keyboard translations, 37 tokens and 54 command links.
- **Sound:** eight v3 reference waveforms, counters, 969 noise periods, buffer bounds and deferred BREAK; 468 Piano calls over 26 keys, three registers and six key-dependent modes.
- **Games:** Quest FR/EN — map choice, complete map, movement, shops, progression, defeat and five guardians; Orbital Duel FR/EN — both complete grids, including the right border, through to placement.

### Resources

| Resource | Value |
|---|---|
| IC8 ROM | 32,768 bytes |
| ROM outside explicit reserve | 32,710 bytes |
| Explicit ROM reserve | 58 fragmented bytes |
| Empty BASIC free RAM | 5,951 bytes |
| Tokens / commands | 37 / 54 |
| Temporary noise buffer | 672 bytes |

### Reproduction and hardware check

From the repository root, using Studio's Python environment and the diagnostic dependencies:

```powershell
studio/.venv/Scripts/python.exe tools/firmware/build_release_candidate.py
studio/.venv/Scripts/python.exe tools/diagnostics/run_release_audit.py
studio/.venv/Scripts/python.exe tools/firmware/prepare_release_candidate.py
```

Full reports are generated in `build/release-candidate/` and `build/release-audit-0.4.100/`. The incremental build still requires A09, the Canon ROMs and earlier stages from the development environment. A second build produced the same CPU hash: `e864a52bec0d7caab2db0e9c87d6aa0afeee6e5d74ca0424e7c25589a84336ec`.

Static traversal covers IC8 and manifest-listed regions; calculation and startup tests execute maskROM services at runtime. Startup uses a functional mechanical model. Pixel tests also use Studio's paper acceleration, with representative native-path comparisons; sound tests separately check cycle-counted kernels. Physical paper registration, acoustic levels, cable voltages and real power-on conditions require hardware checks. Future programs and hardware trials will extend this regression coverage.

A short hardware check before distribution is recommended: retain and restart a large program, perform LOAD/SAVE with Studio, print a Quest or Orbital Duel map, play a few Piano sounds, and trigger a NEXT error in a separate small program. Normal programs and games can then provide a longer trial.
