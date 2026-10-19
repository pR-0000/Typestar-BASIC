# Un terminal papier en BASIC / A BASIC paper terminal

## Français

`terminal-fr.bas` reçoit le texte PC sur l'imprimante et prépare les réponses clavier sur le LCD, avant leur envoi par Return. `terminal_pc_fr.py` est son correspondant PC. Les deux utilisent **1200 bauds, 7E1** et **un acquittement ACK par octet PC**. Il s'agit d'un exemple de terminal en mode ligne avec son protocole ; un flux tty continu demande une réception tamponnée dans le firmware.

1. Charger `terminal-fr.bas` avec **Typestar BASIC Studio > Envoyer → LOAD**, aux réglages habituels **31250/7E1**.
2. Préparer une feuille thermique. Dans un terminal PC ouvert au dossier du projet, lancer `python examples/terminal/terminal_pc_fr.py COM28`, avec le port indiqué dans Studio.
3. Sur la Canon, taper **RUN**. Le script doit être lancé avant RUN pour recevoir le premier ACK.
4. PC : taper une phrase puis Entrée pour l'imprimer. Canon : taper une réponse, corriger avec Backspace, puis envoyer avec Return.
5. PC : `/quit` puis Entrée ferme la session et restaure **31250/7E1** sur la Canon. Après un arrêt par **MARGIN RELEASE / BREAK**, taper `BAUD 31250` avant de transférer avec Studio.

Python utilise **pySerial** : au besoin `python -m pip install pyserial`. Sous Linux/macOS, utiliser au besoin `python3` et un port tel que `/dev/ttyUSB0` ou `/dev/cu.usbserial-...`.

Le préfixe LCD `> ` laisse **30 caractères** pour la réponse. Les caractères sont ASCII. Les accents des phrases PC sont simplifiés (`café` → `cafe`), les autres signes deviennent `?`. La réponse Canon utilise CRLF. CR, LF ou CRLF reçus donnent une fin de ligne papier ; CRLF est compté une fois. Les tabulations avancent au prochain taquet de huit colonnes. Le texte continue après 72 colonnes.

La réception occupe au plus une place à la fois : le PC attend ACK après chaque octet, y compris pendant l'impression. Le BASIC prépare des groupes de 36 caractères, ferme la session pour imprimer, la rouvre, puis confirme. Le clavier est relevé entre les impressions ; saisir lorsque la tête est à l'arrêt évite de perdre les frappes survenues pendant un lot.

Pour un autre débit, modifier `B=1200` à la ligne 20 et utiliser la même valeur avec `--baud`, par exemple `--baud 2400`. Les autres choix sont 7812, 15625 et 31250 ; le format reste 7E1.

Le [chapitre du manuel](../../docs/user-manual/09-terminal-papier.md) contient les explications et les deux listings complets. La validation électrique et mécanique sur machine reste à effectuer.

## English

`terminal-en.bas` prints text received from the PC and prepares keyboard replies on the LCD before sending them with Return. `terminal_pc_en.py` is its PC peer. Both use **1200 baud, 7E1** and **one ACK per PC byte**. This is a line-oriented terminal example with its own protocol; a continuous tty stream requires buffered reception in the firmware.

1. Load `terminal-en.bas` using **Typestar BASIC Studio > Send → LOAD**, at the usual **31250/7E1** settings.
2. Prepare thermal paper. In a PC terminal opened in the project folder, run `python examples/terminal/terminal_pc_en.py COM28`, replacing the port with the one shown in Studio.
3. Type **RUN** on the Canon. Start the PC script before RUN so it receives the first ACK.
4. On the PC, type a sentence and press Enter to print it. On the Canon, type a reply, edit with Backspace, then send with Return.
5. On the PC, `/quit` followed by Enter closes the session and restores **31250/7E1** on the Canon. After stopping with **MARGIN RELEASE / BREAK**, type `BAUD 31250` before transferring with Studio.

Python uses **pySerial**: install it if needed with `python -m pip install pyserial`. On Linux/macOS, use `python3` if appropriate and a port such as `/dev/ttyUSB0` or `/dev/cu.usbserial-...`.

The LCD prefix `> ` leaves **30 characters** for a reply. Characters are ASCII. Accents in PC sentences are simplified (`café` → `cafe`); other unsupported symbols become `?`. Canon replies use CRLF. Received CR, LF or CRLF produces a paper line ending; CRLF counts once. Tabs advance to the next eight-column stop. Text continues after 72 columns.

Reception holds at most one byte at a time: the PC waits for ACK after each byte, including during printing. BASIC prepares groups of 36 characters, closes the session to print, reopens it, then acknowledges. The keyboard is polled between print operations; typing while the head is stopped avoids losing keys pressed during a batch.

For another speed, change `B=1200` at line 20 and use the same value with `--baud`, for example `--baud 2400`. Other choices are 7812, 15625 and 31250; the format remains 7E1.

The [manual chapter](../../docs/user-manual/en/09-terminal-papier.md) contains explanations and both complete listings. Electrical and mechanical validation on hardware remains to be done.
