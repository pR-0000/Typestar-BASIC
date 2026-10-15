# Un terminal papier en BASIC

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

## English version

Load `terminal-en.bas` with Studio, then start `terminal_pc_en.py` on the PC before running the BASIC program. The pair uses 1200 baud, 7E1 with one ACK per transmitted byte. Use `/quit` in the PC script to finish and restore the default transfer speed. See the [English workshop](../../docs/user-manual/en/09-terminal-papier.md) for complete instructions.
