# Architecture de l'émulateur / Emulator architecture

Studio utilise un cœur d'instructions **HD6301** partagé par deux modes : la machine Canon générique et l'adaptateur de facilités BASIC. Le mode générique exécute les ROM choisies par l'utilisateur sans connaître les adresses de l'interpréteur BASIC.

## Modules

| Module dans `studio/internal/` | Responsabilité |
|---|---|
| `hd6301.py` | Instructions CPU, ALU, registres et flags |
| `machine.py` | Bus, carte mémoire, RESET, clavier, LCD et cartouches |
| `machine_devices.py` | Timers, interruptions, moteurs, tête thermique et buzzer |
| `rom_images.py` | Chargement des images, ordre des moitiés IC8 et profils facultatifs |
| `emulator_cpu.py`, `basic_adapter.py` | Facilités BASIC : injection de programme, clavier, son et papier |
| `emulator_worker.py` | Processus d'émulation et protocole de communication avec l'interface |
| `emulator.py` | Commandes ON/OFF, exécution, touches et réglages |
| `debugger.py` | Registres, mémoire et désassemblage |
| `lcd_glass.py`, `paper.py` | Rendu du LCD et de la feuille |

Les ressources et profils sont inclus dans `assets/` et `profiles/`. Les ROM sont fournies explicitement par l'utilisateur. Le fonctionnement de Studio repose sur ces modules et sur les codecs de `tools/` ; les archives de recherche et diagnostics restent facultatifs.

## Deux modes

En mode BASIC, F5 prépare le programme de l'éditeur puis lance son exécution. Les adresses propres au firmware restent dans l'adaptateur et les profils. En mode générique, F5 démarre ou reprend simplement la machine : le texte de l'éditeur est indépendant de sa RAM.

ON démarre depuis le vecteur RESET de la maskROM sélectionnée. Le clavier générique agit sur la matrice matérielle ; les conversions de caractères dépendent du firmware. Le LCD suit les écritures du contrôleur. Le papier et le son dérivent des commandes thermiques et du buzzer.

## Modèle fonctionnel

Les moteurs, capteurs, interruptions et délais sont modélisés pour exécuter les pilotes Canon. Les frottements, l'inertie, le jeu mécanique et la dérive de la feuille restent hors du modèle. Les temps CPU et audio sont approximatifs. Les résultats sur machine réelle complètent les essais dans Studio.

## English overview

`hd6301.py` implements the shared instruction interpreter. `machine.py` and `machine_devices.py` model the Canon bus and devices. BASIC-specific addresses and conveniences remain in the adapter and profiles. The worker runs separately from the interface, keeping menus responsive during program execution. Generic mode runs user-selected ROMs without BASIC source injection. The LCD, paper and sound are functional approximations of the hardware, rather than electrical or mechanical validation.
