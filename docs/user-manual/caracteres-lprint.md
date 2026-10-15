# Les caractères de LPRINT

La commande d'impression papier s'appelle **LPRINT**, avec un seul L. Sa police comprend **95 caractères ASCII imprimables**, codes décimaux **32 à 126**, espace compris. Elle est différente de la table de caractères LCD utilisée par PRINT.

## Alphabet, chiffres et signes

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZ
abcdefghijklmnopqrstuvwxyz
0123456789
! " # $ % & ' ( ) * + , - . /
: ; < = > ? @
[ \ ] ^ _ `
{ | } ~
```

Le caractère 32 est un espace. Voici la table dans l'ordre des codes ; chaque caractère après le séparateur occupe la position suivante. La première position de la ligne 32 est donc vide.

```text
 32–47  | !"#$%&'()*+,-./
 48–63  |0123456789:;<=>?
 64–79  |@ABCDEFGHIJKLMNO
 80–95  |PQRSTUVWXYZ[\]^_
 96–111 |`abcdefghijklmno
112–126 |pqrstuvwxyz{|}~
```

Les antislashs, barres verticales, crochets, accolades et autres signes de cette table sont bien les glyphes ASCII corrigés de notre firmware, indépendamment des substitutions régionales du firmware Canon d'origine.

## Utilisation

```basic
10 LPRINT "Bonjour ! Score : ";123
20 LPRINT CHR$(34);"Un texte entre guillemets";CHR$(34)
30 LPRINT "Antislash : ";CHR$(92);" Barre : ";CHR$(124)
```

CHR$(34) permet d'imprimer un guillemet sans fermer prématurément la chaîne BASIC. CHR$(92) imprime l'antislash, CHR$(124) la barre verticale. Il n'est pas nécessaire de doubler l'antislash comme dans certains langages modernes.

Les accents, le signe euro et les codes LCD étendus ne sont pas disponibles dans cette police papier. Un code hors de 32–126 provoque une erreur de plage ; il n'est pas translittéré automatiquement. Pour les fins de ligne, utiliser LPRINT sans point-virgule final ou LPRINT seul, plutôt que CHR$(10) ou CHR$(13).

Pour imprimer un dessin ou un caractère personnel, utiliser les fonctions graphiques ou GLYPH ; cela n'ajoute pas de caractère à la police LPRINT. La ligne de texte peut contenir jusqu'à 72 caractères, sans retour automatique.

## Imprimer sa propre référence

Ouvrez la palette des caractères de Studio pour consulter la police papier et insérer le caractère choisi. Le chapitre consacré aux caractères reproduit également la table complète.

Voici le rendu obtenu avec le programme de référence dans le papier simulé de Studio :

![Police papier LPRINT, codes 32 à 126](images/lprint-characters.png)
