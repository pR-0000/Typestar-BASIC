# Enquête / Investigation — Typestar BASIC 1.0

## Français

D’après **Enquête**, d’**Éric Flament**, paru dans **Hebdogiciel n°23** pour Sharp PC-1211. Version française sur LCD, sans impression. Charger `enquete-fr.bas` depuis Studio, avec le firmware courant. Les accents utilisent directement les caractères natifs.

### Gaston a été tué

Neuf personnes sont suspectes : Albert, Gustave, Dudule, Henri, Marcel, Hélène, Katie, Sylvie et Aline. Retrouvez le coupable grâce à leurs déclarations. La durée d’attente au titre initialise le hasard ; aucun nombre à saisir.

Le lieu de découverte du corps apparaît après l’introduction. Chaque affaire possède un seul responsable. Il connaissait la victime, n’a pas d’alibi sûr et donne un faux lieu. Les réponses restent les mêmes lorsqu’on repose une question.

### Interroger

Choisissez une personne avec les flèches gauche/droite, puis Return. A1 ou A2 rappelle l’affaire active. Q abandonne depuis cette sélection. Les questions se présentent sur deux pages :

- **1 Lieu** : lieu déclaré par cette personne.
- **2 Alibi** : un alibi sûr l’innocente dans l’affaire active.
- **3 Lien** : demande si elle connaissait la victime ; « non » l’innocente.
- **4 Vu** : choisissez une autre personne pour confronter les témoignages.
- **5 Accuser** : choisissez un nom puis confirmez avec O. Toute autre touche annule. **Une accusation fausse termine la partie.**
- **6 Affaire** : après le second décès, bascule entre les affaires 1 (Gaston) et 2 (nouvelle victime), avec rappel du nom.

Les flèches changent de page ; les touches 1 à 6 fonctionnent sur les deux pages. Backspace retourne à la sélection des suspects, ou annule la sélection d’un nom dans « Vu » et « Accuser ». Après chaque réponse, le menu de la personne interrogée reste ouvert. Backspace permet de changer de suspect ; la découverte du second corps interrompt la conversation. Une touche passe les messages. Le compteur final compte les réponses obtenues, pas la navigation.

### Comment confronter les témoignages

Notez les lieux déclarés. Utilisez **Vu** entre deux personnes **déclarant le même lieu** :

- « Oui » : leurs déclarations se corroborent, toutes deux sont innocentes dans cette affaire.
- « Non » : l’une des deux ment. Confrontez-les à une troisième personne et recoupez avec les alibis et les liens avec la victime.

Un « non » entre deux lieux différents ne prouve rien ! Cette règle représente un rapprochement des déclarations, pas une simulation détaillée des déplacements. Les personnages sont regroupés sur trois lieux parmi les neuf noms de lieux du jeu. Il existe toujours des comparaisons permettant de progresser ; les alibis et les liens ne suffisent pas nécessairement à eux seuls.

### Un second corps

Après six réponses, ou dès la résolution de la première affaire si elle survient avant, un second corps est découvert. La victime est l’un des neuf suspects, mais jamais le responsable de la mort de Gaston. Les faits du second décès sont distincts : les alibis, relations et déclarations de lieu doivent être vérifiés à nouveau. Le coupable peut être le même pour les deux affaires.

La personne morte ne peut plus répondre. Vous pouvez cependant demander aux vivants s’ils l’ont vue, y compris pour compléter la première affaire. Les informations sur Gaston restent valables. Le second corps peut être celui du responsable lui-même : **un suicide**. Si les témoignages innocentent les huit vivants, accusez la personne décédée dans l’affaire 2. Les deux affaires doivent être résolues pour gagner. L’ordre de résolution est libre après la découverte du second corps.

Conseil : notez sur une feuille les noms, lieux et réponses pour chacune des deux affaires. Le jeu n’imprime rien et ne propose pas encore de carnet intégré ni de sauvegarde de partie.

### Fidélité et corrections

Sources : [index Hebdogiciel PC-1211](http://www.hebdogiciel.free.fr/PC1211_1.htm) et [archive Enquête](http://www.hebdogiciel.free.fr/hd-roms/PC1211/HEB23_Enquete.zip). Attribution conservée à Éric Flament ; les droits du jeu d’origine ne sont pas modifiés.

Le listing présente plusieurs coquilles et incohérences : comparaison d’une personne avec elle-même, réponses renouvelées au hasard, code de question peu explicite, succès de la seconde accusation suivi d’un échec. Cette adaptation conserve les neuf noms, les lieux, les cinq actions principales, le second décès possible avec suicide. Elle reconstruit la génération des indices : réponses stables, règles de confrontation cohérentes, second décès après six réponses, sélection par menus et victoire lorsque les deux affaires sont résolues. L’accusation fausse devient une défaite pour empêcher une résolution par essais successifs. La limite originale de deux questions par sélection a été retirée pour garder une conversation continue. Les sons et le mode multijoueur formel ne sont pas repris ; plusieurs joueurs peuvent toutefois enquêter ensemble.

### Vérification

Le programme est contrôlé par l’analyseur de Studio. `tools/validate_enquete.py` exécute des scénarios avec la ROM BASIC dans l’émulateur : interrogatoires, second corps, deux accusations correctes, suicide et accusation erronée. Les coupables sont fixés uniquement pour ces tests. La jouabilité et le confort de navigation restent à confirmer sur la Canon.

Taille : **2 718 octets tokenisés**, **3 233 octets libres avant variables**. Les trois scénarios CPU ont réussi ; la cohérence des confrontations a aussi été vérifiée pour les 81 combinaisons coupable/personne décédée, en autorisant les témoignages des vivants sur les morts.

## English

Based on **Enquête**, by **Éric Flament**, published in **Hebdogiciel issue 23** for the Sharp PC-1211. This French version uses the LCD, without printing. Load the [program](../games/enquete-fr.bas) from Studio with the current firmware. Accents use native characters directly.

### Gaston has been killed

Nine people are suspects: Albert, Gustave, Dudule, Henri, Marcel, Hélène, Katie, Sylvie and Aline. Identify the culprit from their statements. The time spent at the title seeds randomness; there is no seed to enter.

The body's location appears after the introduction. Each case has one culprit. That person knew the victim, has no reliable alibi and gives a false location. Answers stay the same when a question is repeated.

### Questioning suspects

Choose a person with the left/right arrows, then Return. A1 or A2 identifies the active case. Q quits from this selection. Questions are arranged on two pages:

- **1 Lieu (Location):** the person's stated location.
- **2 Alibi:** a reliable alibi clears the person in the active case.
- **3 Lien (Connection):** asks whether the person knew the victim; “no” clears them.
- **4 Vu (Seen):** choose another person to compare their statements.
- **5 Accuser (Accuse):** choose a name, then confirm with O. Any other key cancels. **A false accusation ends the game.**
- **6 Affaire (Case):** after the second death, switches between case 1 (Gaston) and case 2 (the new victim), displaying the victim's name.

Arrows change pages; keys 1 to 6 work on both pages. Backspace returns to suspect selection, or cancels name selection in “Vu” and “Accuser”. After an answer, the questioned person's menu stays open. Backspace lets you change suspects; discovery of the second body interrupts the conversation. A key passes messages. The final counter counts answers obtained, not menu navigation.

### Comparing statements

Record stated locations. Use **Vu** between two people **claiming to be in the same place**:

- “Oui” (Yes): their statements corroborate each other; both are innocent in this case.
- “Non” (No): one of them is lying. Compare them with a third person, then cross-check alibis and connections to the victim.

A “no” between two different locations proves nothing! This rule compares statements rather than simulating detailed movements. Characters are grouped into three locations chosen from the game's nine location names. Comparisons always offer a way forward; alibis and connections alone may be insufficient.

### A second body

After six answers, or immediately after solving the first case if that happens sooner, a second body is found. The victim is one of the nine suspects, but never Gaston's killer. The facts of the second death are separate: alibis, connections and stated locations must be checked again. The same person may be responsible for both cases.

The dead person can no longer answer. However, you may ask the living whether they saw that person, including to complete the first case. Information about Gaston remains valid. The second victim can be responsible for their own death: **suicide**. If the statements clear all eight living people, accuse the deceased in case 2. Solve both cases to win. After discovery of the second body, either case can be solved first.

Tip: use paper to record names, locations and answers for each case. The game prints nothing and currently provides neither an integrated notebook nor saved games.

### Fidelity and corrections

Sources: [Hebdogiciel PC-1211 index](http://www.hebdogiciel.free.fr/PC1211_1.htm) and [Enquête archive](http://www.hebdogiciel.free.fr/hd-roms/PC1211/HEB23_Enquete.zip). Attribution remains with Éric Flament; the original game's rights are unchanged.

The listing has several errors and inconsistencies: comparing a person with themselves, randomly changing answers, unclear question codes and a successful second accusation followed by failure. This adaptation retains the nine names, locations, five main actions and possible second death including suicide. It rebuilds clue generation: stable answers, consistent comparison rules, the second death after six answers, menu selection and victory when both cases are solved. A false accusation becomes a defeat to prevent solving by repeated guesses. The original two-question limit per selection is removed to allow a continuous conversation. Sound and a formal multiplayer mode are not included; several players can still investigate together.

### Verification

Studio's analyser checks the program. `tools/validate_enquete.py` runs scenarios with the BASIC ROM in the emulator: questioning, a second body, two correct accusations, suicide and an incorrect accusation. Culprits are fixed only for these tests. Playability and navigation comfort still need confirmation on the Canon.

Size: **2,718 tokenized bytes**, **3,233 bytes free before variables**. All three CPU scenarios passed; consistency of comparisons was also checked for all 81 culprit/deceased combinations, allowing living witnesses to give statements about the dead.
