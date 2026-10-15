# Atelier - Un terminal papier pour converser

La Canon reçoit un message du PC et le garde sur le papier. Vous préparez votre réponse au clavier, la relisez sur le LCD, puis Return l’envoie au PC. Avec le câble série, la machine devient un petit **terminal papier**.

Notre exemple utilise un **mode ligne** : vous pouvez corriger votre réponse avant de l’envoyer. D’autres terminaux transmettent chaque touche dès la frappe ; le choix dépend de l’usage et du logiciel. Ici, nous privilégions une conversation simple, par phrases. [T1]

## Préparer les deux correspondants

Les deux fichiers se trouvent dans le dossier **examples/terminal** : [terminal-fr.bas](../../examples/terminal/terminal-fr.bas) pour la Canon et [terminal_pc_fr.py](../../examples/terminal/terminal_pc_fr.py) pour le PC. Le programme BASIC fonctionne avec le firmware décrit dans ce manuel.

1. Ouvrez **terminal-fr.bas** dans **Typestar BASIC Studio**, puis envoyez-le avec **Envoyer → LOAD**, aux réglages habituels **31250 / 7E1**. Attendez la fin du transfert.
2. Préparez une feuille, de préférence du papier thermique. Laissez encore la Canon au prompt `>`.
3. Sur le PC, ouvrez un terminal dans le dossier du projet et lancez la commande ci-dessous, en remplaçant COM28 par le port indiqué dans Studio.
4. Tapez **RUN** puis Return sur la Canon. L’écran affiche `> ` : la conversation est ouverte.

```text
python examples/terminal/terminal_pc_fr.py COM28
```

Sous Linux ou macOS, utilisez au besoin **python3** et le nom de votre port, par exemple `/dev/ttyUSB0` ou `/dev/cu.usbserial-...`. Le script utilise la bibliothèque **pySerial**, également employée par Studio. Si le Python choisi la demande, installez-la avec :

```text
python -m pip install pyserial
```

La conversation démarre à **1200 bauds, 7E1** : sept bits de données, parité paire et un bit de stop. Le programme BASIC règle lui-même ce format au démarrage ; le script PC applique les mêmes valeurs. [T2]

## Votre première conversation

Sur le PC, tapez **BONJOUR DEPUIS LE PC** puis Entrée. Le message s’imprime sur la feuille. Sur la Canon, tapez **BONJOUR DU TYPESTAR** : les lettres apparaissent sur le LCD. Vous pouvez retirer la dernière lettre avec **Backspace**. Appuyez sur **Return** pour transmettre la réponse ; elle apparaît dans la fenêtre du PC.

Le LCD présente un préfixe `> ` et **30 caractères de réponse**, soit ses 32 positions. Une touche maintenue compte comme une frappe ; relâchez-la pour répéter la même lettre. Les signes ASCII usuels sont acceptés. Un petit bip annonce une réponse pleine ou une touche hors de cette table.

Les lettres tapées sur la Canon attendent Return avant de partir. Ce choix laisse le temps de relire. La réponse part avec **CR puis LF**, les deux codes usuels de fin de ligne. Le texte reçu du PC est imprimé ; la réponse locale reste visible sur le LCD jusqu’à son envoi.

| Ce qui arrive sur la Canon | Résultat sur le papier |
|---|---|
| Texte ASCII | Lettres, chiffres et ponctuation de Courier 10. |
| CR ou LF | Termine la ligne et fait avancer le papier. |
| CR suivi de LF | Une seule fin de ligne. |
| Tabulation | Ajoute des espaces jusqu’au prochain taquet de huit colonnes. |
| Une ligne de plus de 72 caractères | Continue sur la ligne papier suivante. |

Le correspondant Python simplifie les accents des messages PC : **café** devient **cafe**, **Noël** devient **Noel**, **œuf** devient **oeuf**. Un signe sans équivalent devient `?`. Ce traitement concerne ce programme de terminal ; LLIST garde sa propre règle de remplacement décrite au chapitre du papier.

Pour terminer proprement, tapez **/quit** puis Entrée sur le PC. Le dernier texte en attente s’imprime, les deux correspondants ferment la liaison et la Canon affiche **TERMINAL FERME**. Elle retrouve alors les réglages **31250 / 7E1** pour les transferts dans Studio.

**MARGIN RELEASE / BREAK** permet aussi d’arrêter le programme. Après cet arrêt, tapez `BAUD 31250` avant le prochain transfert avec Studio.

## Pourquoi le PC attend-il une confirmation ?

Le BASIC relève les caractères reçus entre ses instructions. L’impression, elle, demande du temps. Pour accorder ces deux rythmes, le PC envoie **un octet**, puis attend le code **ACK**, de valeur 6, avant le suivant. La Canon confirme aussi qu’elle est prête au tout début.

Le texte reçu est préparé par groupes de **36 caractères**, une taille de tampon choisie pour cet exemple. Pendant leur impression, le programme ferme temporairement la session série, puis la rouvre avant d’envoyer ACK. Le PC attend pendant ce travail. Les groupes occupent la même ligne papier grâce au point-virgule de LPRINT ; l’avance a lieu à la fin de ligne ou lorsque la largeur de 72 caractères est atteinte.

Le clavier est relevé **entre les lots d’impression**. Préparez votre réponse lorsque la tête est à l’arrêt pour que toutes les frappes soient lues. Le correspondant PC continue, de son côté, à recevoir les réponses même pendant la saisie d’une nouvelle phrase.

Le débit et le format série sont standards ; **le dialogue utilise les confirmations de notre exemple**. Un autre correspondant doit respecter cette même règle. Un terminal pour des flux continus, des commandes de curseur ANSI ou une connexion directe à un système distant demanderait une gestion de réception plus complète dans le firmware.

## Lire le programme BASIC

Les lignes **100 à 230** alternent la réception et la lecture du clavier. La chaîne B$ garde la réponse locale. Les sous-programmes **500** et **600** traitent Return et Backspace ; **900** prépare le LCD.

À partir de **1000**, le programme reconnaît les caractères reçus et les fins de ligne. R$ garde le prochain groupe à imprimer ; C compte les colonnes. Les sous-programmes **2000** et **2100** impriment, puis rétablissent la liaison. Le code spécial **4**, envoyé par /quit, conduit à **3000** pour terminer proprement.

<!-- terminal-basic:start -->
```basic
10 REM TERMINAL PAPIER - 1200 BAUDS 7E1
20 B=1200:SERCFG 7E1:LSPACING 1.5
30 B$="":R$="":C=0:D=0:H=0
40 GOSUB 900:SEROPEN B:SEROUT 6
100 A=SERIN(0)
110 IF A>=0 THEN GOSUB 1000
120 K=INKEY(0)
130 IF K=0 THEN H=0:GOTO 100
140 IF K=H THEN 100
150 H=K
160 IF K=13 THEN GOSUB 500:GOTO 100
170 IF K=8 THEN GOSUB 600:GOTO 100
180 IF K<32 THEN 100
190 IF K>126 THEN BEEP 20:GOTO 100
200 IF LEN(B$)=30 THEN BEEP 20:GOTO 100
210 B$=B$+CHR$(K)
220 LOCATE 1,LEN(B$)+2:PRINT CHR$(K);
230 GOTO 100
500 N=LEN(B$):IF N=0 THEN 540
510 FOR I=1 TO N
520 SEROUT ASC(MID$(B$,I,1))
530 NEXT I
540 SEROUT 13:SEROUT 10
550 B$="":GOSUB 900:RETURN
600 IF LEN(B$)=0 THEN RETURN
610 LOCATE 1,LEN(B$)+2:PRINT " ";
620 B$=LEFT$(B$,LEN(B$)-1):RETURN
900 CLS:CURSOR 0:PRINT "> ";:RETURN
1000 IF A=4 THEN 3000
1010 IF A=10 AND D=13 THEN D=0:GOTO 1150
1020 IF A=13 THEN GOSUB 2000:D=13:GOTO 1150
1030 IF A=10 THEN GOSUB 2000:D=0:GOTO 1150
1040 D=0
1050 IF A=9 THEN GOSUB 1300:GOTO 1150
1060 IF A<32 OR A>126 THEN 1150
1070 GOSUB 1400
1150 SEROUT 6:RETURN
1300 T=8-(C MOD 8):A=32
1310 FOR J=1 TO T:GOSUB 1400:NEXT J
1320 RETURN
1400 IF C=72 THEN GOSUB 2000
1410 R$=R$+CHR$(A):C=C+1
1420 IF LEN(R$)=36 THEN GOSUB 2100
1430 RETURN
2000 SERCLOSE
2010 IF LEN(R$)>0 THEN LPRINT R$;
2020 R$="":LPRINT:C=0
2030 SEROPEN B:RETURN
2100 SERCLOSE:LPRINT R$;
2110 R$="":SEROPEN B:RETURN
3000 IF C>0 THEN GOSUB 2000
3010 SEROUT 6:SERCLOSE:BAUD 31250
3020 CLS:CURSOR 0:PRINT "TERMINAL FERME":END
```
<!-- terminal-basic:end -->

## Le petit correspondant Python

Le script lit le port et attend les confirmations. Un second fil d’exécution attend vos phrases au clavier du PC : ainsi, une réponse de la Canon peut s’afficher pendant que vous préparez la suivante. La bibliothèque pySerial s’occupe du port et de son format. [T2]

<!-- terminal-python:start -->
```python
"""Correspondant du terminal BASIC : 1200/7E1, un octet puis un ACK."""
import argparse
from collections import deque
from queue import Empty, Queue
from threading import Thread
from time import monotonic
import unicodedata


def ascii_text(text):
    """Les accents deviennent des lettres simples ; les autres signes, ?."""
    text = text.translate(str.maketrans({
        "\u0153": "oe", "\u0152": "OE", "\u00e6": "ae", "\u00c6": "AE",
        "\u00df": "ss", "\u2019": "'", "\u2018": "'", "\u201c": '"',
        "\u201d": '"', "\u2013": "-", "\u2014": "-",
    }))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    data = text.encode("ascii", "replace")
    return bytes(b if b == 9 or 32 <= b <= 126 else 63 for b in data)


def converse(port, lines, emit, timeout=60):
    """Recoit aussi les lignes Canon pendant l'attente d'une saisie PC."""
    pending = deque()
    waiting, closing, cr = True, False, False
    deadline = monotonic() + timeout
    while True:
        data = port.read(1)
        if data:
            b = data[0]
            if b == 6:
                if not waiting:
                    raise RuntimeError("ACK inattendu : relancer la session.")
                waiting = False
            elif b == 13:
                emit("\n")
                cr = True
            elif b == 10:
                if not cr:
                    emit("\n")
                cr = False
            elif 32 <= b <= 126 or b == 9:
                emit(chr(b))
                cr = False
        if closing and not pending and not waiting:
            return
        if not pending and not closing:
            try:
                text = lines.get_nowait()
                closing = text is None or text == "/quit"
                pending.extend(b"\x04" if closing else
                               ascii_text(text) + b"\r\n")
            except Empty:
                pass
        if pending and not waiting:
            if port.write(bytes([pending.popleft()])) != 1:
                raise OSError("Octet non transmis ; session interrompue.")
            waiting = True
            deadline = monotonic() + timeout
        if waiting and monotonic() > deadline:
            raise TimeoutError("ACK absent : verifier RUN, cable et reglages.")


def main():
    import sys
    try:
        import serial
    except ImportError:
        raise SystemExit("Installer : python -m pip install pyserial")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("port",
                        help="COM28, /dev/ttyUSB0, /dev/cu.usbserial...")
    parser.add_argument("--baud", type=int, default=1200,
                        choices=[1200, 2400, 7812, 15625, 31250])
    args = parser.parse_args()
    lines = Queue()
    def keyboard():
        for text in sys.stdin:
            lines.put(text.rstrip("\r\n"))
        lines.put(None)
    with serial.Serial(args.port, args.baud, bytesize=serial.SEVENBITS,
                       parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE,
                       timeout=0.05, write_timeout=60, rtscts=True) as port:
        port.reset_input_buffer()
        print(f"Terminal {args.baud}/7E1 : taper RUN sur la Canon.",
              flush=True)
        print("PC : texte puis Entree. /quit : fermer les deux cotes.")
        Thread(target=keyboard, daemon=True).start()
        converse(port, lines, lambda s: print(s, end="", flush=True))
    print("Session fermee. Canon revenue a 31250/7E1.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, TimeoutError) as exc:
        raise SystemExit(f"{exc}\nCanon : BREAK, puis BAUD 31250.")
    except KeyboardInterrupt:
        raise SystemExit("Interrompu. Canon : BREAK, puis BAUD 31250.")
```
<!-- terminal-python:end -->

## À vous de modifier l’exemple

Changez le préfixe du LCD à la ligne **900**, ou l’interligne de la ligne **20**. Pour essayer un autre débit, modifiez **B=1200** à la ligne 20 et lancez le correspondant avec le même nombre, par exemple `--baud 2400`. Conservez 7E1 des deux côtés et les confirmations ACK.

Les essais dans l’émulateur vérifient le programme, le correspondant Python et leur dialogue, avec une seule place de réception occupée à la fois. Le premier essai sur votre Canon permet de vérifier le câble, le rythme réel du clavier et l’impression.

[T1]: https://ftp.gnu.org/old-gnu/Manuals/glibc/html_node/Canonical-or-Not.html
[T2]: https://pyserial.readthedocs.io/en/latest/pyserial_api.html
