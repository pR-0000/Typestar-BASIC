# Clavier distant / Remote keyboard

[BASIC français](remote-keyboard-fr.bas) · [English BASIC](remote-keyboard-en.bas)

## Français

Utilisez la Canon comme **clavier de texte pour votre ordinateur**. Le programme BASIC lit `INKEY(0)` et transmet le code de chaque frappe ; le script Python le convertit en texte ou en touche de navigation. Choisissez **`--type` pour écrire dans Studio, le Bloc-notes ou une autre application**. Le **mode moniteur**, choisi par défaut, sert à voir les codes dans la console.

### Premier essai : voir les codes

Depuis le dossier principal du projet, installez les dépendances :

```text
python -m pip install -r examples/remote-keyboard/requirements.txt
```

1. Ouvrez **remote-keyboard-fr.bas** dans **Typestar BASIC Studio**, puis **Envoyer → LOAD**, aux réglages habituels **31250/7E1**. Attendez la fin du transfert.
2. Lancez le script ci-dessous, en remplaçant COM28 par le port indiqué dans Studio.
3. Sur la Canon, tapez **RUN**. Le LCD indique d'abord l'attente du PC, puis **CLAVIER ACTIF**.
4. Tapez quelques lettres et utilisez les flèches. Le moniteur affiche chaque code, sans écrire dans une autre application.
5. **Ctrl+C dans la console Python** ferme proprement la session et termine le programme Canon.

```text
python examples/remote-keyboard/keyboard_pc_fr.py COM28 --monitor
```

Exemples de résultats :

```text
 97 / 0x61 : 'a'
225 / 0xE1 : 'é'
 18 / 0x12 : Gauche
```

Studio sert au chargement ; l'essai de liaison série se fait avec la **machine réelle et son câble USB**. Le moniteur demande seulement pySerial ; pynput sert à écrire dans les autres applications. Sous Linux/macOS, utilisez au besoin `python3` et un port tel que `/dev/ttyUSB0` ou `/dev/cu.usbserial-...`.

### Écrire dans une application

Relancez le script avec **`--type`**, puis tapez de nouveau **RUN** sur la Canon :

```text
python examples/remote-keyboard/keyboard_pc_fr.py COM28 --type
```

Après la connexion, vous disposez de **cinq secondes** pour cliquer dans la zone de texte voulue, par exemple l'éditeur de **Typestar BASIC Studio** ou un document vide du Bloc-notes. Le script active ensuite les frappes dans cette fenêtre. `--start-delay 10` donne dix secondes pour choisir la fenêtre. Les frappes commencent après ce délai ; le programme écarte la touche déjà en attente au démarrage. Pour l'essai dans Studio, gardez le curseur dans l'éditeur de texte ; l'écran de l'émulateur reçoit les touches comme une Canon émulée.

Chaque événement clavier est une action complète ; deux frappes consécutives de la même lettre sont transmises séparément. Majuscules, ponctuation et accents suivent les caractères que renvoie le BASIC, selon le clavier et son mode I/II. Le script réutilise la table de caractères native du projet : gardez le dossier `tools/` à sa place.

Le programme rapide **KB2** transmet deux octets par touche, sans conversion hexadécimale ni confirmation à attendre entre les frappes. Rechargez les nouveaux fichiers BASIC avec Studio pour profiter de cette accélération. Le script accepte aussi l'ancien programme KB1 et indique quand celui-ci est utilisé. La vitesse reste celle d'un programme BASIC interprété : le firmware conserve un seul événement en attente, et une frappe très rapide peut encore dépasser sa capacité de lecture.

| Code INKEY | Action sur le PC |
|---:|---|
| 8 | Retour arrière |
| 9 | Tabulation, si ce code est fourni |
| 13 | Entrée |
| 18 / 19 | Gauche / droite |
| 20 / 21 | Haut / bas, avec LEFT MARGIN / RIGHT MARGIN |
| 32–126 | Texte ASCII, espace compris |
| Accents natifs reconnus | Caractère Unicode correspondant |
| 127 | Supprimer, si ce code est fourni |

Les autres codes sont visibles comme **ignorés** dans le moniteur. Ce sont les codes **traduits par INKEY**, différents des positions physiques affichées par KEYS. Les touches Shift et CODE participent au choix du caractère ; elles ne deviennent pas des touches Ctrl/Alt du PC. Les jeux demandant plusieurs touches maintenues nécessiteraient un autre protocole.

Sur **macOS**, autorisez le Terminal ou Python dans les réglages **Accessibilité** pour l'envoi de frappes. Sous **Linux**, pynput utilise notamment X11 ; la session graphique et ses autorisations conditionnent l'injection, avec des restrictions sous Wayland. Le moniteur fonctionne sans cette injection. Voir les [limitations de pynput](https://pynput.readthedocs.io/en/latest/limitations.html).

### Arrêt et réglages

Pour fermer la session, revenez à la console Python et faites **Ctrl+C**. Le LCD indique **CLAVIER FERME** ; la Canon retrouve **31250/7E1**. **MARGIN RELEASE / BREAK** interrompt aussi le BASIC. Après une interruption matérielle ou un câble débranché, arrêtez le script puis tapez `BAUD 31250` avant un transfert Studio.

Le débit est **31250 bauds, 7E1** par défaut. Pour essayer 1200 bauds, remplacez `B=31250` par `B=1200` à la ligne 20, rechargez le programme, puis ajoutez **`--baud 1200`** au script. Les choix sont 1200, 2400, 7812, 15625 et 31250. Le format reste 7E1.

### Comment cela fonctionne

La Canon annonce `KB2` suivi de CR ; le PC répond ACK (6) lorsqu'il est prêt. Une frappe occupe **deux octets** : 64 pour un code inférieur à 128, ou 65 pour un code de 128 à 255 ; puis les sept bits restants. Ainsi, `40 61` représente **a** et `41 61` représente le code natif **E1**, soit **é** (valeurs hexadécimales). Chaque octet tient sur sept bits. Le PC vérifie la paire avant d'agir ; la Canon poursuit aussitôt sa lecture du clavier. **EOT (4)** ferme la session, avec un dernier ACK. Seules l'ouverture et la fermeture demandent une réponse du PC.

L'ancien dialogue KB1 utilise quatre octets (STX, deux chiffres hexadécimaux, ETX) et une confirmation après chaque touche. Le script choisit automatiquement le bon dialogue à partir du message d'ouverture ; les scripts PC anciens demandent le programme BASIC ancien.

Le programme montre `INKEY`, `SERCFG`, `SEROPEN`, `SERIN`, `SEROUT` et `SERCLOSE`. Le firmware reste inchangé. Les essais automatisés vérifient le protocole et les sorties dans un clavier simulé ; la frappe réelle dans vos applications reste à essayer sur la machine.

## English

Use the Canon as a **text keyboard for your computer**. BASIC reads `INKEY(0)` and sends each keystroke's code; Python converts it to text or a navigation key. Choose **`--type` to write in Studio, Notepad or another application**. **Monitor mode**, the default, displays codes in the console.

### First trial: see the codes

From the project's main directory, install dependencies:

```text
python -m pip install -r examples/remote-keyboard/requirements.txt
```

1. Open **remote-keyboard-en.bas** in **Typestar BASIC Studio**, then choose **Send → LOAD**, at the usual **31250/7E1** settings. Wait for the transfer to finish.
2. Start the script below, replacing COM28 with the port shown in Studio.
3. Type **RUN** on the Canon. The LCD first shows that it is waiting for the PC, then **KEYBOARD ACTIVE**.
4. Type letters and try the arrows. The monitor displays each code without typing in another application.
5. **Ctrl+C in the Python console** cleanly closes the session and ends the Canon program.

```text
python examples/remote-keyboard/keyboard_pc_en.py COM28 --monitor
```

Example output:

```text
 97 / 0x61 : 'a'
225 / 0xE1 : 'é'
 18 / 0x12 : Left
```

Studio loads the program; the serial trial uses the **real machine and USB cable**. Monitoring needs only pySerial; pynput is used to type in other applications. On Linux/macOS, use `python3` if appropriate and a port such as `/dev/ttyUSB0` or `/dev/cu.usbserial-...`.

### Typing in an application

Restart the script with **`--type`**, then type **RUN** again on the Canon:

```text
python examples/remote-keyboard/keyboard_pc_en.py COM28 --type
```

After connecting, you have **five seconds** to click the desired text area, such as the **Typestar BASIC Studio** editor or an empty Notepad document. The script then enables keystrokes in that window. `--start-delay 10` gives ten seconds to select a window. Typing starts after this delay; the program discards a key already pending at startup. In Studio, keep the cursor in the text editor; the emulator's display handles input as an emulated Canon.

Each keyboard event is a complete action; consecutive presses of the same letter are transmitted separately. Uppercase, punctuation and accents follow the characters BASIC supplies, according to the keyboard and I/II mode. The script reuses the project's native character table: keep `tools/` in place.

The faster **KB2** program sends two bytes per key, without hexadecimal conversion or waiting for an acknowledgement between keystrokes. Reload the new BASIC files with Studio to benefit from this speedup. The script also accepts the older KB1 program and identifies it when used. This is still an interpreted BASIC program: the firmware retains one pending event, so very fast typing can still exceed its reading capacity.

| INKEY code | PC action |
|---:|---|
| 8 | Backspace |
| 9 | Tab, if this code is supplied |
| 13 | Enter |
| 18 / 19 | Left / right |
| 20 / 21 | Up / down, using LEFT MARGIN / RIGHT MARGIN |
| 32–126 | ASCII text, including space |
| Recognised native accents | Corresponding Unicode character |
| 127 | Delete, if this code is supplied |

Other codes appear as **ignored** in the monitor. These are **translated INKEY codes**, distinct from the physical positions displayed by KEYS. Shift and CODE help select characters; they do not become PC Ctrl/Alt keys. Games requiring several held keys would need another protocol.

On **macOS**, allow Terminal or Python in **Accessibility** settings to send keystrokes. On **Linux**, pynput uses backends including X11; the graphical session and its permissions determine injection support, with restrictions under Wayland. The monitor works without injection. See [pynput's limitations](https://pynput.readthedocs.io/en/latest/limitations.html).

### Stopping and settings

Return to the Python console and press **Ctrl+C** to close the session. The LCD shows **KEYBOARD CLOSED**; the Canon returns to **31250/7E1**. **MARGIN RELEASE / BREAK** also interrupts BASIC. After a hardware interruption or unplugged cable, stop the script and type `BAUD 31250` before a Studio transfer.

The default is **31250 baud, 7E1**. To try 1200 baud, change `B=31250` to `B=1200` at line 20, reload the program, then add **`--baud 1200`** to the script. Choices are 1200, 2400, 7812, 15625 and 31250. The format remains 7E1.

### How it works

The Canon announces `KB2` followed by CR; the PC replies ACK (6) when ready. A keystroke occupies **two bytes**: 64 for a code below 128, or 65 for a code from 128 to 255; then the remaining seven bits. Thus, `40 61` represents **a** and `41 61` represents native code **E1**, or **é** (hexadecimal values). Every byte fits seven bits. The PC checks the pair before acting; the Canon immediately resumes reading its keyboard. **EOT (4)** closes the session, with one final ACK. Only opening and closing require a reply from the PC.

The older KB1 dialogue uses four bytes (STX, two hexadecimal digits, ETX) and an acknowledgement after every key. The script automatically selects the appropriate dialogue from the opening message; older PC scripts require the older BASIC program.

The program demonstrates `INKEY`, `SERCFG`, `SEROPEN`, `SERIN`, `SEROUT` and `SERCLOSE`. The firmware is unchanged. Automated trials check the protocol and output through a simulated keyboard; typing in real applications remains to be tried on your machine.
