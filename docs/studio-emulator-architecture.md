# Architecture de l'émulateur / Emulator architecture

Studio utilise un cœur d'instructions **HD6301** partagé par deux modes : la machine Canon générique et l'adaptateur de facilités BASIC. Le mode générique exécute les ROM choisies par l'utilisateur sans connaître les adresses de l'interpréteur BASIC.

## Modules

| Module dans `studio/internal/` | Responsabilité |
|---|---|
| `hd6301.py` | Instructions CPU, ALU, registres et flags |
| `hd6301_dispatch.py` | Table des instructions préparée au lancement, partagée par les modes BASIC et générique |
| `machine.py` | Bus, carte mémoire, RESET, clavier, LCD et cartouches |
| `machine_devices.py` | Timers, interruptions, moteurs, tête thermique et buzzer |
| `rom_images.py` | Chargement des images, ordre des moitiés IC8 et profils facultatifs |
| `emulator_cpu.py`, `basic_adapter.py` | Facilités BASIC : injection de programme, clavier, son et papier |
| `paper_instant.py` | Accélération facultative des routines papier BASIC reconnues, avec vérification des octets du code |
| `emulator_worker.py` | Processus d'émulation et protocole de communication avec l'interface |
| `emulator.py` | Commandes ON/OFF, exécution, touches et réglages |
| `debugger.py` | Registres, mémoire et désassemblage |
| `lcd_glass.py`, `paper.py` | Rendu du LCD et de la feuille |

Les ressources et profils sont inclus dans `assets/` et `profiles/`. Les ROM sont fournies explicitement par l'utilisateur. Le fonctionnement de Studio repose sur ces modules et sur les codecs de `tools/` ; les archives de recherche et diagnostics restent facultatifs.

## Deux modes

En mode BASIC, F5 prépare le programme de l'éditeur puis lance son exécution. Les adresses propres au firmware restent dans l'adaptateur et les profils. En mode générique, F5 démarre ou reprend simplement la machine : le texte de l'éditeur est indépendant de sa RAM.

ON démarre depuis le vecteur RESET de la maskROM sélectionnée. Le clavier générique agit sur la matrice matérielle ; les conversions de caractères dépendent du firmware. Le LCD suit les écritures du contrôleur. Le papier et le son dérivent des commandes thermiques et du buzzer.

## Modèle fonctionnel

Le cœur CPU prépare une table de traitement des opcodes à partir de modèles Python fixes. Chaque étape exécute une instruction HD6301 et utilise les méthodes de lecture et d'écriture de la machine ; le code en RAM reste modifiable et les périphériques restent actifs. Le décodage de référence est conservé dans `HD6301CPU.step_reference()` pour les comparaisons. L'adaptateur BASIC réserve ses vérifications aux points d'interaction, tout en continuant à compter chaque instruction pour le clavier. Les tests différentiels comparent registres, flags, mémoire et ordre des accès au bus.

Les moteurs, capteurs, interruptions et délais sont modélisés pour exécuter les pilotes Canon. Les frottements, l'inertie, le jeu mécanique et la dérive de la feuille restent hors du modèle. Les temps CPU et audio sont approximatifs. Les résultats sur machine réelle complètent les essais dans Studio.

## Impression instantanée

Dans le sous-onglet Papier, une case active des opérations hôtes équivalentes à certaines routines natives : décodage des glyphes et de la police compressée, phases moteur, transferts vers la tête et attente des périphériques. Chaque raccourci vérifie les octets de sa routine ; un code différent poursuit son exécution avec l'interpréteur CPU. Les données graphiques restent celles de la RAM et de la ROM choisies. Les colonnes thermiques suivent le même rendu et les mêmes coordonnées, y compris les compensations du firmware.

L'option concerne l'adaptateur BASIC. Les calculs du programme, BREAK, les sons et les attentes de saisie restent exécutés. L'état de la case est conservé dans `studio.ini`, transmis au processus d'émulation et réappliqué après RESET. Décocher la case rétablit les routines CPU habituelles, y compris pendant une impression. Pour suivre leurs instructions dans le débogueur, utilisez ce mode habituel.

## English overview

`hd6301.py` implements the shared instruction interpreter. `machine.py` and `machine_devices.py` model the Canon bus and devices. BASIC-specific addresses and conveniences remain in the adapter and profiles. The worker runs separately from the interface, keeping menus responsive during program execution. Generic mode runs user-selected ROMs without BASIC source injection. The LCD, paper and sound are functional approximations of the hardware, rather than electrical or mechanical validation.

`hd6301_dispatch.py` prepares the opcode table from fixed internal Python templates. Each step still executes one HD6301 instruction through the machine's read/write methods, retaining mutable RAM code and peripheral effects. `HD6301CPU.step_reference()` retains the reference decoder for differential tests of registers, flags, memory and bus access order. The BASIC adapter checks desktop interactions at their boundaries while counting every instruction for keyboard scheduling.

**Instant printing** is an optional BASIC adapter feature implemented in `paper_instant.py`. Equivalent host operations accelerate known glyph/font decoding, motor scheduling and peripheral transfers. Exact instruction-byte guards leave other code running in the CPU interpreter. Graphic data still comes from the selected program and ROM; thermal columns retain their coordinates and firmware compensation. BASIC calculations, BREAK, sound and input waits continue to execute. The checkbox is saved in `studio.ini`, sent to the worker and restored after RESET. Switching it off during printing resumes normal instruction execution; use that mode when tracing printer routines in the debugger.
