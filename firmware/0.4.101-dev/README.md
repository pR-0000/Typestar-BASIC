# Typestar BASIC 0.4.101-dev

[Français](#français) · [English](#english)

## Français

Firmware du **24 novembre 2026**, publié après confirmation du déplacement de la tête sur machine. Studio **0.2.41** reconnaît cette version.

- **typestar-basic-32k.bin** : OneROM en 27C256, puce 27C256 compatible, ou ROM externe dans Studio.
- **typestar-basic-64k-mirror.bin** : deux copies identiques pour une W27C512 compatible.

Au prompt BASIC, maintenez **CODE + LEFT MARGIN** ou **CODE + RIGHT MARGIN**. La tête se déplace par pas d'un caractère Courier 10. Relâchez l'une des touches pour l'arrêter. Le papier conserve sa hauteur et le programme ainsi que la ligne en cours restent en mémoire. L'impression suivante utilise la position choisie.

Les touches de marge seules conservent l'historique ; CODE + flèches conserve `<` et `>`. Les programmes et INPUT gardent leur fonctionnement habituel. La course est bornée et le pilote arrête une impression qui atteindrait sa limite droite avec `?PAPER`.

La réserve explicite de ROM est de **57 octets** ; la RAM BASIC libre à vide reste de **5 951 octets**. [Notes de version](../../docs/releases/0.4.101-dev.md), [empreintes SHA-256](SHA256SUMS.txt), [informations du firmware](release-info.json) et [contrôles logiciels](validation-summary.json).

## English

Firmware dated **24 November 2026**, published after hardware confirmation of head positioning. Studio **0.2.41** recognizes this version.

- **typestar-basic-32k.bin**: OneROM in 27C256 mode, a compatible 27C256 chip, or Studio's external ROM.
- **typestar-basic-64k-mirror.bin**: two identical copies for a compatible W27C512.

At the BASIC prompt, hold **CODE + LEFT MARGIN** or **CODE + RIGHT MARGIN**. The head moves one Courier 10 character pitch at a time. Release either key to stop. The paper stays at the same height, and the program and line being edited remain in memory. The next printout uses the selected position.

Margin keys alone retain history browsing; CODE + arrows retains `<` and `>`. Programs and INPUT keep their usual behavior. Travel is bounded, and the driver stops a printout that would reach its right limit with `?PAPER`.

Explicit ROM reserve is **57 bytes**; empty BASIC free RAM remains **5,951 bytes**. [Release notes](../../docs/releases/0.4.101-dev.md#english), [SHA-256 checksums](SHA256SUMS.txt), [firmware information](release-info.json) and [software checks](validation-summary.json).
