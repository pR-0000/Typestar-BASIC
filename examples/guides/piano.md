# Piano

[Programme français / French program](../piano-fr.bas) · [English program](../piano-en.bas)

## Français

Les lettres **A à Z** déclenchent chacune un son court. Majuscules et minuscules sont acceptées ; **Entrée** termine le programme. Lancez-le avec F5 dans Studio ou `RUN` sur la Canon. Dans Studio, activez le son du buzzer et choisissez votre sortie audio.

Alternez deux ou trois touches pour construire une petite phrase sonore. Les nombres DATA règlent la **modulation d'amplitude** du buzzer ; timbre et hauteur perçue dépendent de la modulation et de la machine.

Changez une valeur DATA puis relancez pour comparer. `SOUND F(C-65),80` choisit la modulation associée à la lettre et une durée de **80 ms**. Essayez 160 pour allonger les sons. Cet exemple montre `DIM`, `READ`, `INKEY`, `AND` et `SOUND`.

## English

Each letter **A to Z** plays a short sound. Uppercase and lowercase both work; **Enter** exits. Run with F5 in Studio or `RUN` on the Canon. In Studio, enable buzzer sound and select your audio output.

Alternate two or three keys to build a short sound pattern. DATA values control the buzzer's **amplitude modulation**; timbre and perceived pitch depend on both the modulation and the machine.

Change a DATA value, then run again to compare. `SOUND F(C-65),80` selects the letter's modulation and a duration of **80 ms**. Try 160 for longer sounds. This example demonstrates `DIM`, `READ`, `INKEY`, `AND` and `SOUND`.
