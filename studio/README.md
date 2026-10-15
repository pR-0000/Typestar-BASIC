# Typestar BASIC Studio 0.2.33

[Français](#français) · [English](#english)

## Français

Studio réunit l'éditeur BASIC, les transferts série, l'éditeur de glyphes, l'impression graphique, un émulateur HD6301, le papier virtuel et le débogueur. Firmware de référence : **Typestar BASIC 0.4.88-dev**.

### Lancer Studio

Installez Python **3.12 ou plus récent**, puis double-cliquez sur **Typestar BASIC Studio.pyw** sous Windows. Sous Linux/macOS, depuis la racine du projet :

```text
python3 "studio/Typestar BASIC Studio.pyw"
```

Le lanceur crée son environnement `studio/.venv`, vérifie silencieusement les dépendances et installe les paquets manquants avec pip. La première installation demande Internet et peut prendre quelques instants. Python et venv/pip doivent être disponibles. Un message apparaît seulement en cas d'erreur ; le détail se trouve dans `studio/studio-install.log`.

Gardez `studio/` à côté de `tools/`, `src/`, `docs/` et `examples/`. Les modules partagés de `tools/` sont nécessaires au fonctionnement. Les tests et fichiers de recherche sont facultatifs.

### Utilisation

- **Fichier → Ouvrir** : choisissez un programme. Les exemples portent les suffixes `-fr.bas` et `-en.bas`.
- **Exécuter (F5)** : charge et lance le programme de l'éditeur dans l'émulateur BASIC. Le démarrage automatique passe les messages d'accueil.
- **Envoyer → LOAD / Recevoir ← SAVE** : échanges avec la Canon. Les réglages par défaut sont **31250 bauds, 7E1** ; sélectionnez les mêmes valeurs aux deux extrémités.
- **Émulation → Choisir les ROM…** : indiquez la maskROM et la ROM externe. Studio conserve leurs chemins dans ses réglages ; aucun fichier ROM caché n'est substitué.
- **ON/OFF** : alimentation virtuelle. **Arrêter** fige l'émulation ; **Réinitialiser** recommence le démarrage.
- **Affichage** : langue française ou anglaise, thème système, clair ou sombre. Les choix sont enregistrés dans le fichier INI de Studio.

Cliquez sur le LCD pour utiliser le clavier. F7 ou Ctrl correspond à **CODE**, F8 à **MODE** et F9 à **KB - I/II**. Les boutons sous l'écran donnent accès aux autres touches spéciales. Les outils de glyphes acceptent les motifs LCD et papier ; la table des caractères permet d'insérer un caractère dans le programme.

Le mode **ROM générique** utilise le cœur de la machine sans injection de programme BASIC. Dans ce mode, F5 démarre ou reprend simplement le firmware sélectionné. La précision des moteurs, du son et des délais reste une simulation fonctionnelle ; la validation sur machine complète les essais dans Studio.

### Sources

```text
studio/
  Typestar BASIC Studio.pyw    Fichier à lancer
  internal/                   Application, traductions et ressources
    hd6301.py                 Instructions du processeur
    machine.py                Bus et périphériques Canon
    machine_devices.py        Timers, moteurs, tête thermique et buzzer
    basic_adapter.py          Facilités du firmware BASIC
    assets/                   Police LCD et ressources
    profiles/                 Symboles des firmwares reconnus
    requirements.txt          Dépendances Python
```

Voir le [chapitre Studio en français](../docs/user-manual/02-studio.md), son [équivalent anglais](../docs/user-manual/en/02-studio.md) et l'[architecture de l'émulateur](../docs/studio-emulator-architecture.md).

Copyright © 2026 Pierre Raimbault. Les images ROM Canon sont fournies séparément par l'utilisateur.

---

## English

Studio combines the BASIC editor, serial transfers, glyph editor, graphical printing, an HD6301 emulator, virtual paper and debugger. Reference firmware: **Typestar BASIC 0.4.88-dev**.

### Launching Studio

Install Python **3.12 or later**, then double-click **Typestar BASIC Studio.pyw** on Windows. On Linux/macOS, run this command from the project root:

```text
python3 "studio/Typestar BASIC Studio.pyw"
```

The launcher creates its environment in `studio/.venv`, silently checks dependencies and installs missing packages with pip. The first installation requires Internet access and may take a little while. Python and venv/pip must be available. A message appears only if an error occurs; details are recorded in `studio/studio-install.log`.

Keep `studio/` alongside `tools/`, `src/`, `docs/` and `examples/`. Shared modules in `tools/` are required for the application to work. Tests and research files are optional.

### Using Studio

- **File → Open**: choose a program. Example filenames use the suffixes `-fr.bas` and `-en.bas`.
- **Run (F5)**: loads and runs the editor's program in the BASIC emulator. Automatic startup skips the welcome messages.
- **Send → LOAD / Receive ← SAVE**: exchange programs with the Canon. Defaults are **31250 baud, 7E1**; select matching settings at both ends.
- **Emulation → Choose ROMs…**: select the maskROM and external ROM. Studio saves their paths in its settings; no hidden ROM file is substituted.
- **ON/OFF**: virtual power switch. **Stop** freezes emulation; **Reset** starts the boot sequence again.
- **View**: choose French or English and the system, light or dark theme. Your choices are saved in Studio's INI settings file.

Click the LCD to use the keyboard. F7 or Ctrl corresponds to **CODE**, F8 to **MODE**, and F9 to **KB - I/II**. Buttons below the display provide the other special keys. Glyph tools accept LCD and paper patterns; the character table lets you insert a character into your program.

**Generic ROM** mode uses the machine core without injecting a BASIC program. In this mode, F5 simply starts or resumes the selected firmware. Motor, sound and timing accuracy remains a functional simulation; testing on real hardware complements the trials in Studio.

### Source layout

```text
studio/
  Typestar BASIC Studio.pyw    File to launch
  internal/                   Application, translations and resources
    hd6301.py                 Processor instructions
    machine.py                Canon bus and peripherals
    machine_devices.py        Timers, motors, thermal head and buzzer
    basic_adapter.py          BASIC firmware conveniences
    assets/                   LCD font and resources
    profiles/                 Symbols for recognized firmware
    requirements.txt          Python dependencies
```

See the [Studio chapter in French](../docs/user-manual/02-studio.md), its [English counterpart](../docs/user-manual/en/02-studio.md) and the [emulator architecture](../docs/studio-emulator-architecture.md).

Copyright © 2026 Pierre Raimbault. Canon ROM images are supplied separately by the user.
