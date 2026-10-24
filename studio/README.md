# Typestar BASIC Studio 0.2.40

[Français](#français) · [English](#english)

## Français

Studio réunit l'éditeur BASIC, les transferts série, l'éditeur de glyphes, l'impression graphique, un émulateur HD6301, le papier virtuel et le débogueur. Firmware de référence : **Typestar BASIC 0.4.100-dev**.

### Lancer Studio

Installez Python **3.12 ou plus récent**, puis double-cliquez sur **Typestar BASIC Studio.pyw** sous Windows. Sous Linux/macOS, depuis la racine du projet :

```text
python3 "studio/Typestar BASIC Studio.pyw"
```

Le lanceur crée son environnement `studio/.venv`, vérifie silencieusement les dépendances et installe les paquets manquants avec pip. La première installation demande Internet et peut prendre quelques instants. Python et venv/pip doivent être disponibles. Un message apparaît seulement en cas d'erreur ; le détail se trouve dans `studio/studio-install.log`.

Gardez `studio/` à côté de `tools/`, `src/`, `docs/` et `examples/`. Les modules partagés de `tools/` sont nécessaires au fonctionnement. Les tests et fichiers de recherche sont facultatifs.

Les octets sans caractère Unicode habituel dans les DATA apparaissent comme de petits repères hexadécimaux **[B3]**. Ils restent chacun un octet à la sauvegarde et au transfert ; la police de repérage est fournie avec Studio.

### Utilisation

- **Fichier → Ouvrir** : choisissez un programme. Les exemples portent les suffixes `-fr.bas` et `-en.bas`.
- **Exécuter (F5)** : charge et lance le programme de l'éditeur dans l'émulateur BASIC. Le démarrage automatique passe les messages d'accueil.
- **Envoyer → LOAD / Recevoir ← SAVE** : échanges avec la Canon. Les réglages par défaut sont **31250 bauds, 7E1** ; sélectionnez les mêmes valeurs aux deux extrémités.
- **Émulation → Choisir les ROM…** : indiquez la maskROM et la ROM externe. Studio conserve leurs chemins dans ses réglages ; aucun fichier ROM caché n'est substitué.
- **ON/OFF** : alimentation virtuelle. **Arrêter** fige l'émulation ; **Réinitialiser** recommence le démarrage.
- **Émulateur → Papier → Impression instantanée** : accélère le dessin pour les essais BASIC. La case agit pendant l'exécution et son état est mémorisé.
- **Affichage** : langue française ou anglaise, thème système, clair ou sombre. Les choix sont enregistrés dans le fichier INI de Studio.

Cliquez sur le LCD pour utiliser le clavier. F7 ou Ctrl correspond à **CODE**, F8 à **MODE** et F9 à **KB - I/II**. Les boutons sous l'écran donnent accès aux autres touches spéciales. Les outils de glyphes acceptent les motifs LCD et papier ; la table des caractères permet d'insérer un caractère dans le programme.

Le mode **ROM générique** utilise le cœur de la machine sans injection de programme BASIC. Dans ce mode, F5 démarre ou reprend simplement le firmware sélectionné. La précision des moteurs, du son et des délais reste une simulation fonctionnelle ; la validation sur machine complète les essais dans Studio.

### Nouveautés de Studio 0.2.39

Le profil BASIC 0.4.98 prend en charge le son continu et la lecture de BREAK à la fin du son, comme sur la Canon. Les rangées de glyphes et leur impression instantanée sont conservées.

### Depuis Studio 0.2.38

Le profil BASIC 0.4.97 prend en charge le pilote sonore étendu : rapport cyclique, motif pseudo-aléatoire et neuf modes de Piano. Le mode GLYPH 5 et les rangées continues de Quest sont également exécutés depuis le firmware sélectionné. Le son reste un aperçu approximatif du buzzer réel. Les correspondances du clavier suivent le nouveau format compact des tables ROM. Le cœur HD6301 gère également les instructions ADCA/ADCB utilisées par ces routines.

### Depuis Studio 0.2.36

Le cœur HD6301 utilise une table d'exécution préparée au lancement. Les essais locaux hors impression montrent un gain d'environ **×2 à ×2,7**, selon le programme ; la vitesse dépend aussi de l'ordinateur hôte. Le firmware exécute les mêmes instructions, avec les mêmes registres, flags et accès aux périphériques. L'adaptateur BASIC évite également des vérifications répétées entre les points de lecture du clavier, du LCD et du son. Cette accélération est automatique et conserve les temporisations sonores et les attentes de saisie.

### Depuis Studio 0.2.35

La case **Impression instantanée**, désactivée au départ, accélère les routines de dessin et d'impression du firmware BASIC reconnu. Les motifs, la police et les positions proviennent toujours des ROM et du programme sélectionnés. Les calculs BASIC, les sons et les attentes clavier continuent de s'exécuter : une carte complexe conserve donc un temps de préparation. Décochez la case pour retrouver l'exécution habituelle. Le réglage reste mémorisé après une réinitialisation ou une nouvelle séance. Le mode ROM générique conserve son fonctionnement habituel.

### Depuis Studio 0.2.34

L'éditeur de glyphes importe et exporte le **mode papier 4**, à grands pixels carrés. L'import accepte aussi les blocs GLYPH comportant un paramètre de répétition et retrouve leur motif source. Les images BASIC jusqu'à **0.4.93-dev** disposent de leurs symboles pour le débogueur. BREAK atteint aussi les boucles natives d'impression ; le cœur HD6301 complète sa prise en charge de SBCA/SBCB. Les nouveaux jeux servent d'exemples de grandes cartes et de motifs répétés.

### Sources

```text
studio/
  Typestar BASIC Studio.pyw    Fichier à lancer
  internal/                   Application, traductions et ressources
    hd6301.py                 Instructions du processeur
    hd6301_dispatch.py        Table d'exécution des instructions
    machine.py                Bus et périphériques Canon
    machine_devices.py        Timers, moteurs, tête thermique et buzzer
    basic_adapter.py          Facilités du firmware BASIC
    paper_instant.py          Accélération facultative du papier BASIC
    assets/                   Police LCD et ressources
    profiles/                 Symboles des firmwares reconnus
    requirements.txt          Dépendances Python
```

Voir le [chapitre Studio en français](../docs/user-manual/02-studio.md), son [équivalent anglais](../docs/user-manual/en/02-studio.md) et l'[architecture de l'émulateur](../docs/studio-emulator-architecture.md).

Copyright © 2026 Pierre Raimbault. Les images ROM Canon sont fournies séparément par l'utilisateur.

---

## English

Studio combines the BASIC editor, serial transfers, glyph editor, graphical printing, an HD6301 emulator, virtual paper and debugger. Reference firmware: **Typestar BASIC 0.4.100-dev**.

### Launching Studio

Install Python **3.12 or later**, then double-click **Typestar BASIC Studio.pyw** on Windows. On Linux/macOS, run this command from the project root:

```text
python3 "studio/Typestar BASIC Studio.pyw"
```

The launcher creates its environment in `studio/.venv`, silently checks dependencies and installs missing packages with pip. The first installation requires Internet access and may take a little while. Python and venv/pip must be available. A message appears only if an error occurs; details are recorded in `studio/studio-install.log`.

Keep `studio/` alongside `tools/`, `src/`, `docs/` and `examples/`. Shared modules in `tools/` are required for the application to work. Tests and research files are optional.

DATA bytes without a usual Unicode character appear as small hexadecimal badges **[B3]**. Each remains one byte when saved or transferred; the display font is bundled with Studio.

### Using Studio

- **File → Open**: choose a program. Example filenames use the suffixes `-fr.bas` and `-en.bas`.
- **Run (F5)**: loads and runs the editor's program in the BASIC emulator. Automatic startup skips the welcome messages.
- **Send → LOAD / Receive ← SAVE**: exchange programs with the Canon. Defaults are **31250 baud, 7E1**; select matching settings at both ends.
- **Emulation → Choose ROMs…**: select the maskROM and external ROM. Studio saves their paths in its settings; no hidden ROM file is substituted.
- **ON/OFF**: virtual power switch. **Stop** freezes emulation; **Reset** starts the boot sequence again.
- **Emulator → Paper → Instant printing**: speeds up drawing when testing BASIC programs. The checkbox takes effect during execution and its state is saved.
- **View**: choose French or English and the system, light or dark theme. Your choices are saved in Studio's INI settings file.

Click the LCD to use the keyboard. F7 or Ctrl corresponds to **CODE**, F8 to **MODE**, and F9 to **KB - I/II**. Buttons below the display provide the other special keys. Glyph tools accept LCD and paper patterns; the character table lets you insert a character into your program.

**Generic ROM** mode uses the machine core without injecting a BASIC program. In this mode, F5 simply starts or resumes the selected firmware. Motor, sound and timing accuracy remains a functional simulation; testing on real hardware complements the trials in Studio.

### New in Studio 0.2.39

The BASIC 0.4.98 profile supports continuous sound and defers BREAK until the sound ends, matching the Canon. Glyph rows and instant printing remain available.

### Since Studio 0.2.38

The BASIC 0.4.97 profile supports the extended sound driver: duty ratio, pseudo-random pattern and nine Piano modes. GLYPH mode 5 and Quest’s continuous rows also execute from the selected firmware. Audio remains an approximate preview of the real buzzer. Keyboard mappings follow the new compact ROM table format. The HD6301 core also handles the ADCA/ADCB instructions used by these routines.

### Since Studio 0.2.36

The HD6301 core uses an execution table prepared at startup. Local non-printing tests show a speedup of about **2× to 2.7×**, depending on the program; speed also depends on the host computer. The firmware executes the same instructions, with the same registers, flags and peripheral accesses. The BASIC adapter also avoids repeated checks between keyboard, LCD and sound boundaries. Acceleration is automatic and preserves sound timing and input waits.

### Since Studio 0.2.35

The **Instant printing** checkbox, initially off, speeds up drawing and printing routines in recognized BASIC firmware. Patterns, fonts and positions still come from the selected ROMs and program. BASIC calculations, sounds and keyboard waits continue to run, so complex maps still take time to prepare. Uncheck it to restore normal execution. The setting persists across resets and sessions. Generic ROM mode retains its usual operation.

### Since Studio 0.2.34

The glyph editor imports and exports **paper mode 4**, with large square pixels. Import also accepts GLYPH blocks with a repeat parameter and recovers their source motif. BASIC images up to **0.4.93-dev** have matching debugger symbols. BREAK also reaches native print loops; the HD6301 core adds SBCA/SBCB support. The new games demonstrate large maps and repeated motifs.

### Source layout

```text
studio/
  Typestar BASIC Studio.pyw    File to launch
  internal/                   Application, translations and resources
    hd6301.py                 Processor instructions
    hd6301_dispatch.py        Instruction execution table
    machine.py                Canon bus and peripherals
    machine_devices.py        Timers, motors, thermal head and buzzer
    basic_adapter.py          BASIC firmware conveniences
    paper_instant.py          Optional BASIC paper acceleration
    assets/                   LCD font and resources
    profiles/                 Symbols for recognized firmware
    requirements.txt          Python dependencies
```

See the [Studio chapter in French](../docs/user-manual/02-studio.md), its [English counterpart](../docs/user-manual/en/02-studio.md) and the [emulator architecture](../docs/studio-emulator-architecture.md).

Copyright © 2026 Pierre Raimbault. Canon ROM images are supplied separately by the user.
