# Typestar BASIC — firmware

[Français](#français) · [English](#english)

## Français

Version courante : **0.4.100-dev**, pour Canon S-70 / Typestar 7. Les fichiers ci-dessous sont identiques aux pièces jointes de la [release](https://github.com/pR-0000/Typestar-BASIC/releases/tag/v0.4.100-dev).

| Fichier | Taille | Usage |
|---|---:|---|
| [typestar-basic-32k.bin](0.4.100-dev/typestar-basic-32k.bin) | 32 768 octets | IC8 : OneROM configurée en 27C256 ou puce 27C256 compatible. Également utilisable dans Studio comme ROM externe. |
| [typestar-basic-64k-mirror.bin](0.4.100-dev/typestar-basic-64k-mirror.bin) | 65 536 octets | IC8 : W27C512 compatible. L'image 32 Ko est répétée deux fois. |
| [SHA256SUMS.txt](0.4.100-dev/SHA256SUMS.txt) | Texte | Empreintes SHA-256 des deux binaires. |

Les fichiers suivent l'ordre physique des octets de la puce IC8. Le programmateur doit être réglé sur le modèle exact de la puce utilisée. Consultez le [manuel français en PDF](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.100-dev/typestar-basic-manuel-fr.pdf) pour le remplacement de la ROM et son orientation.

Le démarrage BASIC et les transferts Studio jusqu'à **31250/7E1** sont également validés sur S-60 / Typestar 6, PCB **NG3-0672 / NH1-0159-065**, après ajout de l'interface. Le [guide S-60](../docs/hardware/typestar-6-serial-upgrade.md) donne les composants, le repère carré de la broche 7 et les six résistances de RA1. Les autres révisions restent à caractériser. Le firmware BASIC sur S-90 / Typestar 7-II reste à adapter et à valider.

Les sources assembleur sont dans [src/](../src/README.md) et les étapes de construction dans [tools/firmware/](../tools/firmware/README.md). Le firmware utilise les services de la maskROM Canon d'origine ; l'émulateur demande à l'utilisateur de fournir cette maskROM séparément. Voir les [attributions et conditions](../THIRD_PARTY_NOTICES.md).

Les [notes de version et statistiques](0.4.100-dev/README.md) présentent les rangées GLYPH de 40 motifs, le son continu, les correctifs et les jeux actualisés. La ROM de 32 768 octets conserve 58 octets explicitement libres ; les **5 951 octets BASIC libres à vide** restent partagés par le programme et les données.

## English

Current version: **0.4.100-dev**, for Canon S-70 / Typestar 7. The files below are identical to the [release](https://github.com/pR-0000/Typestar-BASIC/releases/tag/v0.4.100-dev) attachments.

| File | Size | Use |
|---|---:|---|
| [typestar-basic-32k.bin](0.4.100-dev/typestar-basic-32k.bin) | 32,768 bytes | IC8: OneROM configured as a 27C256 or a compatible 27C256 chip. Also usable in Studio as the external ROM. |
| [typestar-basic-64k-mirror.bin](0.4.100-dev/typestar-basic-64k-mirror.bin) | 65,536 bytes | IC8: compatible W27C512. The 32 KiB image is repeated twice. |
| [SHA256SUMS.txt](0.4.100-dev/SHA256SUMS.txt) | Text | SHA-256 checksums for both binaries. |

The files use physical IC8 chip byte order. Set the programmer to the exact chip model being used. See the [English PDF manual](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.100-dev/typestar-basic-manuel-en.pdf) for ROM replacement and orientation.

BASIC startup and Studio transfers up to **31250/7E1** are also validated on S-60 / Typestar 6, PCB **NG3-0672 / NH1-0159-065**, after adding the interface. The [S-60 guide](../docs/hardware/typestar-6-serial-upgrade.md#english) details the components, square pin-7 pad and all six RA1 resistors. Other revisions remain to be characterized. BASIC firmware support for S-90 / Typestar 7-II still needs adaptation and validation.

Assembly sources are in [src/](../src/README.md), with build stages in [tools/firmware/](../tools/firmware/README.md). The firmware uses services from the original Canon maskROM; emulator users supply that maskROM separately. See the [attributions and terms](../THIRD_PARTY_NOTICES.md).

The [release notes and statistics](0.4.100-dev/README.md#english) describe 40-tile GLYPH rows, continuous sound, fixes and updated games. The 32,768-byte ROM has 58 explicitly free bytes; **5,951 BASIC bytes free with an empty program** remain shared by the program and data.
