# Essais graphiques 0.4.94-dev et diagnostic sonore v2

## Français

### Bande de deux glyphes

Le candidat **0.4.94-dev** accepte une source d'une largeur de **32 pixels** : chaque rangée est décrite par deux mots de 16 bits, d'abord la moitié gauche, puis la moitié droite. Pour une hauteur de 16 pixels, le tableau contient 32 valeurs. Les modes 1 à 4 et la répétition du motif complet sont conservés.

```basic
10 DIM G(31)
20 FOR I=0 TO 15
30 G(2*I)=32769:G(2*I+1)=255
40 NEXT I
50 GLYPH G(0),32,16,4,5
```

En mode 4, deux sprites de 16 × 16 pixels, à leur grande taille carrée, sont imprimés dans une même transaction : une passe pour leurs moitiés hautes et une pour leurs moitiés basses. L'exemple répète cinq fois la paire. Une paire utilise **476 octets temporaires**, contre 348 pour un seul motif ; les répétitions réutilisent cette bande. Un contrôle de la place disponible précède les mouvements.

Le programme `release/glyph-pair-test.bas` dessine dix grands motifs alternés mur/arbre en deux balayages. Charger le programme avec **Typestar BASIC Studio**, puis lancer `RUN` après avoir installé `release/s70-basic-0.4.94-dev-canon-start-nh7.bin`. Studio reconnaît également cette image et conserve son option Papier instantané.

Le pilote réutilise le décompactage numérique existant. La ROM occupe **32 705 octets sur 32 768**, avec **63 octets de réserve explicite fragmentée**. La RAM BASIC libre à vide reste de **5 951 octets** ; aucun token ni commande supplémentaire n'est nécessaire. Les routines moteur et la compensation Y gardent les mêmes octets que dans la 0.4.93. Les colonnes de garde sont désormais repérées dans le tampon physique, ce qui permet de conserver le dernier pixel des bandes larges.

Les essais CPU couvrent les quatre modes, les anciens formats 1D/2D, les répétitions, les 95 caractères papier, les bornes du tableau, les valeurs invalides, les bandes vides et BREAK. La précision physique et le gain de temps restent à confirmer sur machine. La 0.4.93 publiée reste la référence validée.

### Variante des Ruines 0.5 à essayer

`release/ruines-typestar-fr-0.5-test.bas` et `release/typestar-ruins-en-0.5-test.bas` conservent les règles et la grande taille des dessins. Le rendu lit deux motifs à la fois et parcourt la carte en cinq passes de palette. Il réunit les motifs voisins compatibles dans une bande de 32 pixels et conserve les répétitions pour les longs murs. Les motifs simples et la paire sont préparés une fois par palette, ce qui évite les copies entre groupes.

Tailles : **4 470 octets tokenisés** en français, **4 431** en anglais ; tableaux `M(79)` et `G(67)` : **758 octets**. Sur la carte de référence, les repositionnements papier passent de 6 608 à 5 264 unités (**environ 20 % de moins**) et ceux de la tête de 5 264 à 5 008 unités. Ces valeurs décrivent les déplacements entre groupes, pas une réduction de 20 % du temps total. Cette carte particulière ne contient aucun voisin compatible avec les cinq paires choisies : elle vérifie le réordonnancement ; le petit test mur/arbre vérifie séparément les bandes mixtes.

Le contrôle exécute le BASIC et le pilote natif, puis compare les bits de la tête aux bandes nominales. L'émulateur suit les pas supplémentaires de la compensation Y, sans simuler l'asymétrie des rouleaux ; l'ordre des déplacements change donc légèrement les coordonnées brutes de son tracé. Les traces brutes sont conservées et la vérification de la précision finale se fait sur machine. Les variantes restent dans le dossier local `release` pendant cet essai ; les exemples publiés gardent leur version validée.

### Enregistrement sonore

Le diagnostic est une **ROM séparée, fondée sur le firmware Canon S-70**. Enregistrer d'abord les programmes à conserver avec Studio. Le diagnostic emprunte une partie de la police Canon ; il est destiné uniquement à cette séance sonore.

1. Flasher `release/s70-buzzer-survey-v2-nh7.bin`, puis démarrer la machine et attendre son repos.
2. Préparer un enregistrement WAV, idéalement à 48 kHz ou plus, en gardant le microphone à la même place. Un niveau fixe et une réduction de bruit désactivée facilitent les comparaisons.
3. Appuyer brièvement sur **I/II**. La suite dure environ **48 secondes**, avec 0,6 seconde de silence entre les séquences. Le LCD affiche les numéros ci-dessous.
4. La fin est indiquée par `END - BUZZER OFF`. Le buzzer est coupé et le contexte d'interruption est restauré. Un nouvel appui sur I/II recommence la suite.
5. Réinstaller ensuite le firmware BASIC, par exemple le candidat graphique 0.4.94.

Les autres touches restent des touches du firmware Canon. Pendant la séquence, le clavier attend la fin du diagnostic ; l'interrupteur permet d'arrêter la machine. Le diagnostic ne lance aucune impression.

Toutes les commandes sonores utilisent **uniquement le bit 6 de $0034**, avec son miroir $1801. Les autres bits sont conservés. Le compteur matériel est lu pour régler les attentes, sans reprogrammer le timer. Les deux HOLD activent la porte une seule fois, puis la laissent maintenue : le deuxième essai permet de vérifier si le son subsiste sans l'assistance des interruptions Canon.

Les chiffres en Hz désignent le **hachage de la commande**, et non une fréquence garantie du son entendu. Les rapports cycliques et les durées d'impulsion sont des consignes à 1 MHz. Le temps des instructions décale les fronts, surtout pour les impulsions les plus courtes et les cadences élevées ; l'enregistrement permettra d'en mesurer le résultat. La porteuse précédemment observée vers 5,89 kHz reste à distinguer de cette modulation.

| N° | Séquence / sequence | Commande visée / target |
|---|---|---|
| 01 | HOLD IRQ ON | Porte maintenue 1,2 s, interruptions Canon actives / held gate, Canon IRQ enabled |
| 02 | HOLD IRQOFF | Même commande, interruptions masquées / same gate, IRQ masked |
| 03 | `DUTY 100HZ 10%` | ON 1000 µs, OFF 9000 µs, 100 cycles |
| 04 | `DUTY 100HZ 25%` | ON 2500 µs, OFF 7500 µs, 100 cycles |
| 05 | `DUTY 100HZ 50%` | ON 5000 µs, OFF 5000 µs, 100 cycles |
| 06 | `DUTY 100HZ 75%` | ON 7500 µs, OFF 2500 µs, 100 cycles |
| 07 | `DUTY 100HZ 90%` | ON 9000 µs, OFF 1000 µs, 100 cycles |
| 08 | `DUTY 400HZ 10%` | ON 250 µs, OFF 2250 µs, 400 cycles |
| 09 | `DUTY 400HZ 25%` | ON 625 µs, OFF 1875 µs, 400 cycles |
| 10 | `DUTY 400HZ 50%` | ON 1250 µs, OFF 1250 µs, 400 cycles |
| 11 | `DUTY 400HZ 75%` | ON 1875 µs, OFF 625 µs, 400 cycles |
| 12 | `DUTY 400HZ 90%` | ON 2250 µs, OFF 250 µs, 400 cycles |
| 13 | `GATE 60HZ 50%` | ON 8333 µs, OFF 8334 µs, 60 cycles |
| 14 | `GATE 100HZ 50%` | ON 5000 µs, OFF 5000 µs, 100 cycles |
| 15 | `GATE 200HZ 50%` | ON 2500 µs, OFF 2500 µs, 200 cycles |
| 16 | `GATE 400HZ 50%` | ON 1250 µs, OFF 1250 µs, 400 cycles |
| 17 | `GATE 750HZ 50%` | ON 666 µs, OFF 667 µs, 750 cycles |
| 18 | `GATE 1000HZ 50%` | ON 500 µs, OFF 500 µs, 1000 cycles |
| 19 | `GATE 1500HZ 50%` | ON 333 µs, OFF 334 µs, 1500 cycles |
| 20 | `GATE 2000HZ 50%` | ON 250 µs, OFF 250 µs, 2000 cycles |
| 21 | `GATE 3000HZ 50%` | ON 166 µs, OFF 167 µs, 3000 cycles |
| 22 | `GATE 4000HZ 50%` | ON 125 µs, OFF 125 µs, 4000 cycles |
| 23 | `GATE 5890HZ 50%` | ON 85 µs, OFF 85 µs, 5890 cycles |
| 24 | `GATE 6000HZ 50%` | ON 83 µs, OFF 84 µs, 6000 cycles |
| 25 | `PULSE 60US 50HZ` | ON 60 µs, OFF 19940 µs, 50 cycles |
| 26 | `PULSE 125US 50HZ` | ON 125 µs, OFF 19875 µs, 50 cycles |
| 27 | `PULSE 250US 50HZ` | ON 250 µs, OFF 19750 µs, 50 cycles |
| 28 | `PULSE 500US 50HZ` | ON 500 µs, OFF 19500 µs, 50 cycles |
| 29 | `PULSE 1000US 50HZ` | ON 1000 µs, OFF 19000 µs, 50 cycles |
| 30 | `PULSE 4000US 50HZ` | ON 4000 µs, OFF 16000 µs, 50 cycles |

Les familles comparées sont : commande maintenue avec/sans IRQ, rapports cycliques 10/25/50/75/90 % à 100 et 400 Hz, hachage de 60 à 6 000 Hz, et impulsions brèves de 60 à 4 000 µs à 50 Hz. L'enregistrement peut révéler des timbres ou niveaux plus utiles. Les registres ASIC inconnus restent hors de cette exploration : aucun réglage matériel de hauteur sonore n'a été identifié.

Le test fonctionnel vérifie trois suites complètes avec des miroirs initiaux différents, 254 codes clavier transmis sans changement, les écritures autorisées, la restauration des dix octets empruntés, le masque IRQ et la coupure finale. Les attentes timer sont simulées dans ce contrôle ; le comportement électrique et les interruptions réelles se vérifient sur la machine.

### Résultat de l'enregistrement v2

L'enregistrement `buzzer_survey_v2.wav`, fourni après le diagnostic, contient les trente séquences (44,1 kHz, stéréo, 8 bits, 48,25 s). Les mesures portent sur le son enregistré ; elles donnent des fréquences acoustiques et des niveaux relatifs, avec une résolution spectrale de l'ordre de 1 à 1,3 Hz dans les fenêtres retenues.

- **Commande maintenue :** la composante dominante est identique avec les interruptions Canon actives ou masquées, vers **5 889 Hz**. Les deux sons restent soutenus. Le fonctionnement sonore autonome avec la porte activée est donc confirmé, y compris sans assistance des IRQ Canon.
- **Structure du son :** les HOLD présentent également des composantes vers **1 963, 3 926, 7 852 et 9 814 Hz**. Elles forment une série harmonique compatible avec une fondamentale voisine de 1 963 Hz et un troisième harmonique particulièrement fort à 5 889 Hz. L'ancienne désignation « porteuse 5,89 kHz » décrit donc surtout la composante dominante mesurée ; elle suffit moins à identifier la fréquence fondamentale ou le circuit qui l'engendre.
- **Modulation lente :** les commandes 60, 100, 200 et 400 Hz donnent des enveloppes proches de **60,3, 100,5, 201 et 402 Hz**. À 100 Hz, le passage de 10 % à 90 % d'activation augmente le niveau RMS enregistré d'environ **17 dB**, avec un changement de timbre. Ce résultat fournit une piste de réglage du niveau par hachage ; le microphone, un éventuel gain automatique et la réponse du buzzer participent aux valeurs mesurées.
- **Modulation rapide :** le pic dominant devient **5 135 Hz** pour la commande 750 Hz, **5 025 Hz** pour 1 000 Hz et **4 981 Hz** pour 3 000 Hz. Ces déplacements s'accompagnent de raies latérales et de produits de mélange ; par exemple, 5 135 Hz correspond à environ 5 889 − 754 Hz. Pour les commandes 5 890 et 6 000 Hz, des pics dominants apparaissent vers **5 912 et 6 018 Hz**, tandis que la composante fixe à 5 889 Hz reste présente. Le spectre et la hauteur dominante peuvent donc varier, sans qu'une commande de fréquence propre de l'oscillateur ait été identifiée.
- **Impulsions brèves :** les essais à 50 Hz produisent des trains faibles de transitoires/résonances. Les fenêtres retenues montrent des niveaux RMS environ 22, 19 et 8 dB sous le HOLD pour les impulsions visées de 125, 1 000 et 4 000 µs respectivement. Ils peuvent enrichir les clics et effets, avec une faible énergie pour les impulsions courtes.

Le bilan valide le hachage comme moyen de faire varier **niveau, timbre et composantes spectrales**. Une gamme musicale dont la fréquence acoustique suit directement chaque consigne reste à démontrer. Le diagnostic conserve uniquement le bit de commande déjà connu ; cet enregistrement apporte des indications acoustiques, pas une identification électrique de l'oscillateur ni un nouveau registre de hauteur. Le firmware BASIC sonore reste inchangé pendant cette analyse. Les mesures détaillées et le comparatif spectral sont conservés localement dans `build/buzzer-survey/audio-analysis.json` et `audio-spectra.png`.

### Fichiers et flash

Exécuter ces commandes depuis le dossier `BASIC firmware`.

```text
onerom program --slot "file=release/s70-basic-0.4.94-dev-canon-start-nh7.bin,type=27C256" --plugin usb
```

```text
onerom program --slot "file=release/s70-buzzer-survey-v2-nh7.bin,type=27C256" --plugin usb
```

Les variantes `-64k-mirror.bin` contiennent deux copies pour une ROM 64 Kio, comme une W27C512. Les fichiers 32 Kio ci-dessus sont dans l'ordre du support IC8/OneROM ; les fichiers de travail nommés CPU servent uniquement aux contrôles locaux.

## Diagnostic sonore v3 — essais approfondis

Le diagnostic **v3** est prêt dans `release/s70-buzzer-survey-v3-nh7.bin` (32 Kio, ordre IC8/OneROM), avec une variante `release/s70-buzzer-survey-v3-64k-mirror.bin` pour les puces de 64 Kio. Il remplace temporairement le firmware par une ROM de diagnostic fondée sur Canon ; après l'enregistrement, réinstaller le BASIC habituel. Le pilote graphique et les commandes sonores du BASIC restent inchangés.

### Lancer l'enregistrement

1. Flasher la ROM de diagnostic, puis laisser la machine terminer son démarrage.
2. Lancer un enregistrement WAV, idéalement à 44,1 ou 48 kHz, avec un niveau et une position du microphone constants. La désactivation du gain automatique et de la réduction de bruit facilite la comparaison des niveaux.
3. Appuyer brièvement sur **I/II** : les cinq groupes s'enchaînent en environ **1 minute 52 secondes**. Le LCD affiche un identifiant à trois chiffres pour chaque séquence, avec **0,35 seconde de silence** entre les séquences.
4. Attendre `END V3 - I/II OR 1-5`, puis arrêter l'enregistrement. Le clavier redevient disponible à la fin. Un nouvel appui sur I/II recommence la suite.

Les touches **1 à 5** lancent uniquement le groupe correspondant. Elles permettent de refaire un essai plus court sans réenregistrer toute la suite.

| Touche | Identifiants | Durée indicative | Ce qui est testé |
|---|---|---|---|
| 1 | 101–143 | 41 s | Référence continue puis 42 fréquences de hachage de 250 à 31 250 Hz, avec des pas resserrés autour de 1 963 et 5 889 Hz |
| 2 | 201–218 | 18 s | Rapports cycliques à 100, 1 963, 5 890 et 8 000 Hz ; niveau sonore, timbre et éventuel accrochage |
| 3 | 301–324 | 23 s | Impulsions actives et coupures de 3 à 4 000 µs à 50 Hz ; comparaison entre activation maintenue et réécriture répétée du même état |
| 4 | 401–408 | 14 s | Balayages aller-retour, enveloppes montantes/descendantes et trois motifs pseudo-aléatoires d'excitation |
| 5 | 501–507 | 16 s | Gammes et petite mélodie : hachage direct, puis deux tentatives de mélange autour de 5 889 Hz ; référence continue finale |

Les deux essais de mélange utilisent une commande proche de **5 888,6 Hz moins ou plus la note visée**. Ils cherchent une composante de différence exploitable. Les notes indiquées dans le manifeste décrivent l'objectif de l'essai ; leur présence et leur niveau restent à mesurer dans le son obtenu. La tolérance d'horloge et la fréquence propre de l'exemplaire influencent ce résultat.

### Une commande plus précise

Le v2 utilisait des échéances timer et des fonctions d'activation/extinction. Le v3 génère les plateaux directement, avec un **nombre compté de cycles HD6301** et les interruptions masquées. Les deux valeurs de commande sont préparées à partir du miroir `$1801`, en conservant tous les bits autres que le bit 6. Le miroir reste dans l'état muet pendant la génération ; les valeurs mises en cache alimentent `$0034`. La sortie est remise au repos avant la restauration du masque d'interruption.

Cette méthode permet de comparer des impulsions de **3 µs** et des fréquences jusqu'à **31 250 Hz**, sous l'hypothèse d'un cycle E de 1 µs. Les périodes sont arrondies au nombre entier de cycles le plus proche. Il s'agit de valeurs de **commande**, dont l'enregistrement établira les effets acoustiques. Les silences et les références continues utilisent le compteur libre en lecture seule. Les registres d'horloge, de ports, de configuration timer et les registres ASIC inconnus gardent leur configuration Canon.

Le plan comporte **100 séquences**, reposant sur **105 formes de commande**. Les sources et tables occupent **10 118 octets** dans la région de ressources de la ROM Canon, avec le seul appel clavier détourné à `$682E`. Les routines exécutables Canon à partir de `$67C2` sont conservées. La maskROM reste intacte.

### Vérifications et fichiers de mesure

Les vérifications exécutent les instructions réelles des 105 formes, pendant trois périodes chacune, et les 11 temporisations partagées, avec les nombres de cycles du manuel Hitachi. Huit suites fonctionnelles vérifient les choix de groupe, les 244 codes clavier transmis au firmware Canon, les écritures autorisées, les dix octets temporaires restaurés, le retour du masque IRQ et la coupure finale. Le démarrage depuis le vecteur reset Canon, les six touches de lancement et six affichages sont également vérifiés avec les routines natives dans le modèle matériel de Studio.

Ces contrôles établissent la cohérence du programme et du minutage CPU théorique. La latence électrique de l'ASIC, son oscillateur et la réponse acoustique du transducteur se mesurent sur la machine réelle. L'émulateur sonore actuel représente le comportement déjà connu et sert aux contrôles logiciels ; l'enregistrement matériel permettra d'évaluer ces nouvelles pistes.

- `release/s70-buzzer-survey-v3-manifest.json` : paramètres de chaque séquence et de chaque note, formes de commande, hashes et résultats de validation.
- `release/s70-buzzer-survey-v3-sequences.csv` : repères temporels approximatifs pour retrouver les séquences dans l'enregistrement. Les temps d'affichage et la tolérance d'horloge peuvent décaler ces repères.
- `tools/diagnostics/build_buzzer_survey_v3.py` puis `validate_buzzer_survey_v3.py` : reconstruction et validation à partir des dumps Canon fournis localement.

Commande à exécuter depuis le dossier `BASIC firmware` :

```text
onerom program --slot "file=release/s70-buzzer-survey-v3-nh7.bin,type=27C256" --plugin usb
```

### Résultat de l'enregistrement v3

Le fichier fourni `buzzer_survey_v3.wav` contient la suite complète (44,1 kHz, stéréo, 8 bits, 111,43 s). Le rapprochement du plan et des débuts de sons utilise 77 repères, avec un résidu de l'ordre de 3 ms. Les niveaux ci-dessous restent ceux de l'enregistrement, avec la réponse du microphone et un éventuel gain automatique. Les fréquences sont acoustiques ; elles ne constituent pas une mesure électrique de BZR.

**Une plage de hauteur directement exploitable apparaît dans l'aigu.** Plusieurs commandes entre 5 et 6,4 kHz rendent la composante liée au hachage dominante :

| Séquence | Commande visée | Pic dominant mesuré | Composante fixe vers 5 889 Hz |
|---|---|---|---|
| 121 | 5 000 Hz | 5 025 Hz | −15,2 dB sous le pic dominant |
| 122 | 5 500 Hz | 5 522 Hz | −7,3 dB |
| 123 | 5 700 Hz | 5 743 Hz | −6,9 dB |
| 124 | 5 800 Hz | 5 843 Hz | −7,0 dB |
| 133 | 6 200 Hz | 6 242 Hz | −8,0 dB |
| 134 | 6 400 Hz | 6 442 Hz | −1,5 dB |

Le pic variable suit donc la commande dans plusieurs points de cette zone, au lieu de se limiter à une enveloppe lente. Le niveau et les autres composantes changent fortement selon le réglage : cette plage offre une matière sonore intéressante, avec une réponse irrégulière. Les cibles sont arrondies à des périodes entières ; le calage temporel de l'enregistrement diffère aussi légèrement de l'hypothèse d'horloge nominale. L'oscillation fixe vers 5 889 Hz reste présente, sans nouveau registre de hauteur identifié.

**Les sons de fin de suite constituent une priorité d'intégration**, en accord avec le retour utilisateur :

| Temps approximatif | Séquence | Résultat |
|---|---|---|
| 83,2–85,3 s | 402 | Balayage 5–8 kHz : composantes mobiles et changements de timbre |
| 86,7–90,9 s | 404–405 | Deux enveloppes de rapport cyclique : variation nette du niveau et du timbre |
| 91,3–95,0 s | 406–408 | Trois textures distinctes issues du motif pseudo-aléatoire de 31 bits |
| 98,2–100,8 s | 502 | « MIX MINUS » : sept premiers paliers dominants d'environ 5 403 à 4 926 Hz ; composante fixe souvent 10 à 19 dB plus faible |
| 106,1–110,0 s | 505–506 | Petites mélodies avec les deux mélanges : mouvements aigus et produits de mélange reproductibles |

La mesure précise le sens des essais musicaux : les noms C5–C6 désignaient des notes recherchées. Les trois gammes produisent surtout des composantes dans l'aigu. Dans les fenêtres de « MIX MINUS », les composantes graves de différence recherchées restent autour de 58 à 65 dB sous le pic principal. La gamme entendue tire donc principalement sa variation des composantes aiguës et des mélanges, plutôt que de notes graves isolées. Une correspondance de notes comparable à celle d'un générateur programmable reste à établir.

Les rapports cycliques offrent un autre résultat solide : de 10 à 90 %, l'écart RMS enregistré atteint environ **18,3 dB à 100 Hz**, et **17,8 dB à 1 963 Hz**. Cela soutient l'ajout d'un paramètre de rapport cyclique pour varier niveau et timbre ; sa réponse dépend de la fréquence et du transducteur.

Les impulsions actives de 3 à 8 µs restent proches du bruit de fond ; les impulsions plus longues donnent des clics et résonances progressivement plus marqués. Les brèves coupures gardent surtout le sifflement fixe. La réécriture de l'état actif à 1, 6 et 31,25 kHz conserve un pic dominant identique vers 5 889 Hz : cette piste n'a pas révélé de verrouillage de fréquence à l'écriture. Les excitations très rapides jusqu'à 31,25 kHz ne donnent pas une extension uniforme de la plage sonore utile.

Pour le prochain candidat BASIC, les priorités retenues sont **l'élargissement de SOUND avec un pilote correctement minuté**, **un rapport cyclique optionnel**, et **un mode de texture pseudo-aléatoire**. Les balayages et enveloppes pourront ensuite être composés à partir de courts segments. Le motif de bruit testé est périodique et pseudo-aléatoire, ce qui donne des textures reproductibles. Le BASIC de production reste inchangé à ce stade d'analyse. Les mesures par séquence et par note sont conservées dans `build/buzzer-survey-v3/audio-v3-analysis.json` et `audio-v3-analysis.csv` ; l'analyse reproductible est dans `_local/development/tools/analyze_buzzer_survey_v3.py`.

## English

### Mixed glyph bands

Test firmware **0.4.94-dev** adds **32-pixel sources**. Each row consists of two unsigned 16-bit words, left half then right half, interleaved by row. A 16-row source uses 32 array values. Modes 1–4 and repetition of the complete source remain available; the BASIC example above repeats a pair five times.

Mode 4 retains the large square pixels. Two 16 × 16 sprites share one transaction and two horizontal sweeps. The temporary buffer and native workspace backup total **476 bytes**, independent of the repeat count, compared with 348 bytes for a single sprite. Memory is checked before moving the mechanism.

After installing `release/s70-basic-0.4.94-dev-canon-start-nh7.bin`, transfer `release/glyph-pair-test.bas` using **Typestar BASIC Studio** and run it. It prints ten alternating large wall/tree sprites in two sweeps. Studio recognises the candidate and retains Instant paper support.

The candidate reuses the existing numeric unpacker. ROM use is **32,705 / 32,768 bytes**, with **63 explicitly free fragmented bytes**; empty BASIC RAM remains **5,951 bytes**. No keyword or command was added. Motor code and Y compensation are byte-identical to .93. Physical buffer offsets now identify guard columns, preserving the final pixels of wide sources.

CPU checks cover all four modes, legacy packed/matrix formats, repetitions, all 95 paper characters, source boundaries, invalid values, blank bands and BREAK. Physical precision and speed need hardware confirmation. Published .93 remains the validated reference.

### Ruins 0.5 test variant

`release/typestar-ruins-en-0.5-test.bas` and its French counterpart retain the rules and large drawings. Two motifs are loaded at a time, giving five palette passes. Compatible neighbours share a 32-pixel band; long uniform walls retain the repeat path. Both simple motifs and their combined band are prepared once per palette, avoiding per-group copies.

Sizes are **4,470 tokenized bytes** in French and **4,431** in English; `M(79)` and `G(67)` use **758 bytes** including headers. On the reference map, paper repositioning drops from 6,608 to 5,264 units (**about 20%**) and head repositioning from 5,264 to 5,008. These are movements between groups, not a 20% total-time claim. This particular map has no compatible neighbours for the selected palette pairs: it checks ordering, while the small alternating wall/tree demo checks mixed bands separately.

The check runs actual BASIC and native drawing code and compares exact head bits at nominal band positions. The emulator follows additional Y compensation steps without modelling roller asymmetry, so different travel orders slightly change raw trace positions. Raw traces are retained; final physical accuracy requires hardware verification. These variants remain local in `release` during testing; published examples retain their validated version.

### Recording the sound survey

This is a **separate diagnostic ROM based on the Canon S-70 firmware**. Save any programs through Studio first. Part of the original font is borrowed for the diagnostic, so use this image for the sound session only.

Flash `release/s70-buzzer-survey-v2-nh7.bin`, start the machine and let its mechanism settle. Begin a WAV recording, preferably 48 kHz or higher, with a fixed microphone position and recording level. Press **I/II once**. The numbered sequence above takes about **48 seconds**, with 0.6 seconds of silence between sections. `END - BUZZER OFF` indicates completion; another brief I/II press restarts the survey. Restore BASIC afterwards. The 32 KiB flashing commands above use IC8/OneROM socket byte order; `-64k-mirror.bin` variants provide two copies for 64 KiB chips such as W27C512.

The keyboard waits until the bounded sequence finishes; the power switch can stop the machine. No printing is requested. Only the known buzzer gate, **$0034 bit 6**, is written through shadow $1801, preserving unrelated bits. The free-running timer is read, without reprogramming it. HOLD enables the gate once and holds it, first with Canon IRQ enabled, then with IRQ masked.

Tests compare held enable, 10/25/50/75/90% duty at 100 and 400 Hz, 60–6,000 Hz gating, and 60–4,000 µs pulses at 50 Hz. These are **gate targets**, not guaranteed acoustic pitches. Targets assume a 1 MHz timer; instruction overhead affects edges, especially short pulses and high rates. The recording will establish actual modulation and any useful timbre or level changes. The previously observed ~5.89 kHz carrier should be distinguished from the envelope. Unknown ASIC registers are not swept; no hardware pitch-control register has been identified.

Functional checks cover three complete sequences with different initial shadow values, 254 unchanged pass-through key codes, the write allowlist, restoration of borrowed scratch and IRQ state, and final mute. Timer waits are mocked in these checks; electrical audio and real interrupt behaviour require the hardware recording.

### Results from the v2 recording

The supplied `buzzer_survey_v2.wav` contains all thirty sections (44.1 kHz, stereo, 8-bit, 48.25 seconds). These measurements describe recorded sound and relative levels, with approximately 1–1.3 Hz spectral resolution in the selected windows.

- **Held gate:** the dominant component stays at approximately **5,889 Hz** with Canon IRQ enabled or masked. Both tones remain sustained, confirming autonomous sound production while the gate is enabled, including without Canon IRQ assistance.
- **Tone structure:** the HOLD spectra also contain components near **1,963, 3,926, 7,852 and 9,814 Hz**. This harmonic series is consistent with a fundamental near 1,963 Hz and a particularly strong third harmonic at 5,889 Hz. The earlier “5.89 kHz carrier” description therefore primarily identifies the measured dominant component; it is less sufficient to identify the fundamental or its generating circuit.
- **Slow gating:** commands of 60, 100, 200 and 400 Hz yield envelopes around **60.3, 100.5, 201 and 402 Hz**. At 100 Hz, increasing activation duty from 10% to 90% raises recorded RMS by approximately **17 dB**, while changing timbre. This suggests useful level control through gating; microphone response, possible automatic gain and buzzer response affect the measured values.
- **Fast gating:** the dominant peak moves to **5,135 Hz** for the 750 Hz command, **5,025 Hz** for 1,000 Hz and **4,981 Hz** for 3,000 Hz. Sidebands and mixing products accompany these changes; for example, 5,135 Hz is approximately 5,889 − 754 Hz. Commands of 5,890 and 6,000 Hz produce dominant peaks near **5,912 and 6,018 Hz**, while the fixed 5,889 Hz component remains. The spectrum and dominant pitch can therefore change, without identifying a control for the oscillator's own frequency.
- **Short pulses:** the 50 Hz tests produce weak trains of transients/ringing. In the selected windows, target pulses of 125, 1,000 and 4,000 µs have recorded RMS approximately 22, 19 and 8 dB below HOLD respectively. They offer additional clicks/effects, with low energy for short pulses.

The recording validates gating as a way to vary **level, timbre and spectral components**. A musical scale whose acoustic frequency directly follows each requested note remains to be demonstrated. The diagnostic uses only the known gate bit; this recording provides acoustic evidence, rather than electrical identification of the oscillator or a new pitch register. Production BASIC sound remains unchanged during this analysis. Detailed measurements and spectral comparisons are retained locally in `build/buzzer-survey/audio-analysis.json` and `audio-spectra.png`.

### Sound survey v3 — extended exploration

Flash `release/s70-buzzer-survey-v3-nh7.bin` (32 KiB, IC8/OneROM socket order), or the `-64k-mirror.bin` variant for a 64 KiB chip. This is a separate Canon-based diagnostic ROM; restore BASIC after recording. Production graphics and sound remain unchanged.

Start a WAV recording at 44.1 or 48 kHz, keeping microphone position and recording level constant. Disabling automatic gain and noise reduction makes level comparisons easier. Briefly press **I/II** to run all five groups, taking approximately **1 minute 52 seconds**. Three-digit LCD identifiers mark the sections, separated by **0.35 seconds of silence**. Wait for `END V3 - I/II OR 1-5`, then stop recording. Keyboard operation resumes at the end; another I/II press repeats the suite. Number keys **1–5** select individual groups.

| Key | Section IDs | Approximate duration | Purpose |
|---|---|---|---|
| 1 | 101–143 | 41 s | Held reference and 42 gating rates from 250 to 31,250 Hz, with closer spacing near 1,963 and 5,889 Hz |
| 2 | 201–218 | 18 s | Duty ratios at 100, 1,963, 5,890 and 8,000 Hz; level, timbre and possible locking |
| 3 | 301–324 | 23 s | Active pulses and brief cuts of 3–4,000 µs at 50 Hz; held enable versus repeated writes of the same state |
| 4 | 401–408 | 14 s | Up/down stepped sweeps, rising/falling amplitude envelopes and three pseudo-random excitation patterns |
| 5 | 501–507 | 16 s | Scales and a short tune using direct gating and two mixing attempts around 5,889 Hz; final held reference |

Mixing attempts use gate targets of approximately **5,888.6 Hz minus or plus the intended note**, seeking a usable difference component. Intended notes in the manifest describe experimental goals; their presence and level require acoustic measurement. Clock tolerance and the particular machine's oscillator affect the result.

Unlike the v2 timer-deadline driver, v3 uses **counted HD6301 instruction cycles** with IRQ masked. Two cached copies of shadow `$1801`, differing only in bit 6, drive `$0034`. The shadow remains muted during generation; the physical output is muted before restoring the IRQ mask. This supports target plateaus down to **3 µs** and gating up to **31,250 Hz**, assuming a 1 MHz E clock. Periods are rounded to integer cycle counts. These are command values; the recording will establish their acoustic effects. Silences and held references read the free-running counter. MCU clock, port, timer configuration and unknown ASIC registers retain their Canon configuration.

The plan contains **100 sections** using **105 command waveforms**. Diagnostic code and tables occupy **10,118 bytes** of Canon's resource region; the sole code hook is the keyboard call at `$682E`. Canon executable routines from `$67C2` onwards and the maskROM are preserved.

Checks execute actual instructions for three periods of every waveform and all 11 shared padding routines, with cycle counts from the Hitachi handbook. Eight functional suites cover selection, 244 pass-through key codes, allowed writes, restoration of ten scratch bytes and IRQ mask, and final mute. Native reset-vector startup, six matrix keys and six LCD displays are also checked using Canon routines in Studio's functional hardware model. These establish software consistency and theoretical CPU timing; electrical ASIC latency, oscillation and acoustic response require hardware measurement. Studio's current audio model represents established behaviour and supports software checks; the physical recording will evaluate the new possibilities.

`release/s70-buzzer-survey-v3-manifest.json` contains per-section and per-note parameters, waveforms, hashes and validation results. `release/s70-buzzer-survey-v3-sequences.csv` provides approximate recording anchors, subject to display overhead and clock tolerance. Rebuild and validate with `tools/diagnostics/build_buzzer_survey_v3.py` and `validate_buzzer_survey_v3.py`, using locally supplied Canon dumps. The flashing command above runs from the `BASIC firmware` directory.

### Results from the v3 recording

The supplied `buzzer_survey_v3.wav` contains the complete suite (44.1 kHz, stereo, 8-bit, 111.43 seconds). Alignment uses 77 onset anchors with a residual of about 3 ms. Levels remain relative recording measurements, including microphone response and possible automatic gain. Frequencies describe sound, rather than electrical measurements of BZR.

**A directly useful high-pitched range emerges.** Several gate commands between 5 and 6.4 kHz make the gate-related component dominant:

| Section | Target command | Measured dominant peak | Fixed component near 5,889 Hz |
|---|---|---|---|
| 121 | 5,000 Hz | 5,025 Hz | 15.2 dB below the dominant peak |
| 122 | 5,500 Hz | 5,522 Hz | 7.3 dB below |
| 123 | 5,700 Hz | 5,743 Hz | 6.9 dB below |
| 124 | 5,800 Hz | 5,843 Hz | 7.0 dB below |
| 133 | 6,200 Hz | 6,242 Hz | 8.0 dB below |
| 134 | 6,400 Hz | 6,442 Hz | 1.5 dB below |

The variable peak follows the command at several points in this range, extending beyond slow envelope modulation. Level and other components vary strongly with the setting: this offers useful sounds with an uneven response. Targets are rounded to integer periods, and recording alignment also differs slightly from the nominal clock assumption. The fixed 5,889 Hz oscillation remains present; no new pitch register has been identified.

**The final sounds are an integration priority**, matching the user's preference:

| Approximate recording time | Section | Result |
|---|---|---|
| 83.2–85.3 s | 402 | 5–8 kHz sweep: moving components and timbre changes |
| 86.7–90.9 s | 404–405 | Two duty envelopes: clear level and timbre variation |
| 91.3–95.0 s | 406–408 | Three distinct textures from the 31-bit pseudo-random pattern |
| 98.2–100.8 s | 502 | MINUS scale: first seven dominant steps run from about 5,403 to 4,926 Hz; the fixed component is often 10–19 dB weaker |
| 106.1–110.0 s | 505–506 | Short tunes using both mixing attempts: repeatable high-pitched motion and mixing products |

The musical interpretation needs precision: C5–C6 names described intended notes. All three scales primarily produce high-frequency components. In MINUS-scale windows, intended low difference components remain roughly 58–65 dB below the main peak. Audible variation therefore mainly comes from high components and mixing products, rather than isolated low notes. A note mapping comparable to a programmable tone generator remains to be established.

Duty control provides another solid result: moving from 10% to 90% produces a recorded RMS difference of about **18.3 dB at 100 Hz** and **17.8 dB at 1,963 Hz**. This supports an optional duty parameter for level/timbre control, with a response dependent on frequency and transducer.

Active 3–8 µs pulses remain near background; longer pulses produce progressively clearer clicks and ringing. Brief cuts mainly retain the fixed tone. Rewriting the enabled state at 1, 6 and 31.25 kHz retains the same dominant 5,889 Hz peak, providing no evidence of a pitch latch triggered by writing. Very fast excitation up to 31.25 kHz does not uniformly extend the useful acoustic range.

Priorities for the next BASIC candidate are **an extended SOUND range with a properly timed driver**, **an optional duty ratio**, and **a pseudo-random texture mode**. Sweeps and envelopes can then be composed from short segments. The tested noise pattern is periodic and pseudo-random, producing repeatable textures. Production BASIC remains unchanged at this analysis stage. Per-section and per-note measurements are retained in `build/buzzer-survey-v3/audio-v3-analysis.json` and `audio-v3-analysis.csv`; the reproducible analysis is `_local/development/tools/analyze_buzzer_survey_v3.py`.
