# Enquête — Typestar BASIC 1.0

D’après **Enquête**, d’**Éric Flament**, paru dans **Hebdogiciel n°23** pour Sharp PC-1211. Version française sur LCD, sans impression. Charger `enquete-fr.bas` depuis Studio, avec le firmware courant. Les accents utilisent directement les caractères natifs.

## Gaston a été tué

Neuf personnes sont suspectes : Albert, Gustave, Dudule, Henri, Marcel, Hélène, Katie, Sylvie et Aline. Retrouvez le coupable grâce à leurs déclarations. La durée d’attente au titre initialise le hasard ; aucun nombre à saisir.

Le lieu de découverte du corps apparaît après l’introduction. Chaque affaire possède un seul responsable. Il connaissait la victime, n’a pas d’alibi sûr et donne un faux lieu. Les réponses restent les mêmes lorsqu’on repose une question.

## Interroger

Choisissez une personne avec les flèches gauche/droite, puis Return. A1 ou A2 rappelle l’affaire active. Q abandonne depuis cette sélection. Les questions se présentent sur deux pages :

- **1 Lieu** : lieu déclaré par cette personne.
- **2 Alibi** : un alibi sûr l’innocente dans l’affaire active.
- **3 Lien** : demande si elle connaissait la victime ; « non » l’innocente.
- **4 Vu** : choisissez une autre personne pour confronter les témoignages.
- **5 Accuser** : choisissez un nom puis confirmez avec O. Toute autre touche annule. **Une accusation fausse termine la partie.**
- **6 Affaire** : après le second décès, bascule entre les affaires 1 (Gaston) et 2 (nouvelle victime), avec rappel du nom.

Les flèches changent de page ; les touches 1 à 6 fonctionnent sur les deux pages. Backspace retourne à la sélection des suspects, ou annule la sélection d’un nom dans « Vu » et « Accuser ». Après chaque réponse, le menu de la personne interrogée reste ouvert. Backspace permet de changer de suspect ; la découverte du second corps interrompt la conversation. Une touche passe les messages. Le compteur final compte les réponses obtenues, pas la navigation.

## Comment confronter les témoignages

Notez les lieux déclarés. Utilisez **Vu** entre deux personnes **déclarant le même lieu** :

- « Oui » : leurs déclarations se corroborent, toutes deux sont innocentes dans cette affaire.
- « Non » : l’une des deux ment. Confrontez-les à une troisième personne et recoupez avec les alibis et les liens avec la victime.

Un « non » entre deux lieux différents ne prouve rien ! Cette règle représente un rapprochement des déclarations, pas une simulation détaillée des déplacements. Les personnages sont regroupés sur trois lieux parmi les neuf noms de lieux du jeu. Il existe toujours des comparaisons permettant de progresser ; les alibis et les liens ne suffisent pas nécessairement à eux seuls.

## Un second corps

Après six réponses, ou dès la résolution de la première affaire si elle survient avant, un second corps est découvert. La victime est l’un des neuf suspects, mais jamais le responsable de la mort de Gaston. Les faits du second décès sont distincts : les alibis, relations et déclarations de lieu doivent être vérifiés à nouveau. Le coupable peut être le même pour les deux affaires.

La personne morte ne peut plus répondre. Vous pouvez cependant demander aux vivants s’ils l’ont vue, y compris pour compléter la première affaire. Les informations sur Gaston restent valables. Le second corps peut être celui du responsable lui-même : **un suicide**. Si les témoignages innocentent les huit vivants, accusez la personne décédée dans l’affaire 2. Les deux affaires doivent être résolues pour gagner. L’ordre de résolution est libre après la découverte du second corps.

Conseil : notez sur une feuille les noms, lieux et réponses pour chacune des deux affaires. Le jeu n’imprime rien et ne propose pas encore de carnet intégré ni de sauvegarde de partie.

## Fidélité et corrections

Sources : [index Hebdogiciel PC-1211](http://www.hebdogiciel.free.fr/PC1211_1.htm) et [archive Enquête](http://www.hebdogiciel.free.fr/hd-roms/PC1211/HEB23_Enquete.zip). Attribution conservée à Éric Flament ; les droits du jeu d’origine ne sont pas modifiés.

Le listing présente plusieurs coquilles et incohérences : comparaison d’une personne avec elle-même, réponses renouvelées au hasard, code de question peu explicite, succès de la seconde accusation suivi d’un échec. Cette adaptation conserve les neuf noms, les lieux, les cinq actions principales, le second décès possible avec suicide. Elle reconstruit la génération des indices : réponses stables, règles de confrontation cohérentes, second décès après six réponses, sélection par menus et victoire lorsque les deux affaires sont résolues. L’accusation fausse devient une défaite pour empêcher une résolution par essais successifs. La limite originale de deux questions par sélection a été retirée pour garder une conversation continue. Les sons et le mode multijoueur formel ne sont pas repris ; plusieurs joueurs peuvent toutefois enquêter ensemble.

## Vérification

Le programme est contrôlé par l’analyseur de Studio. `tools/validate_enquete.py` exécute des scénarios avec la ROM BASIC dans l’émulateur : interrogatoires, second corps, deux accusations correctes, suicide et accusation erronée. Les coupables sont fixés uniquement pour ces tests. La jouabilité et le confort de navigation restent à confirmer sur la Canon.

Taille : **2 718 octets tokenisés**, **3 233 octets libres avant variables**. Les trois scénarios CPU ont réussi ; la cohérence des confrontations a aussi été vérifiée pour les 81 combinaisons coupable/personne décédée, en autorisant les témoignages des vivants sur les morts.
