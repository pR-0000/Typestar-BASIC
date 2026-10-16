# Typestar BASIC — firmware

[Français](#français) · [English](#english)

## Français

Version courante : **0.4.88-dev**, pour Canon S-70 / Typestar 7. Les fichiers ci-dessous sont identiques aux pièces jointes de la [release](https://github.com/pR-0000/Typestar-BASIC/releases/tag/v0.4.88-dev).

| Fichier | Taille | Usage |
|---|---:|---|
| [typestar-basic-32k.bin](0.4.88-dev/typestar-basic-32k.bin) | 32 768 octets | IC8 : OneROM configurée en 27C256 ou puce 27C256 compatible. Également utilisable dans Studio comme ROM externe. |
| [typestar-basic-64k-mirror.bin](0.4.88-dev/typestar-basic-64k-mirror.bin) | 65 536 octets | IC8 : W27C512 compatible. L'image 32 Ko est répétée deux fois. |
| [SHA256SUMS.txt](0.4.88-dev/SHA256SUMS.txt) | Texte | Empreintes SHA-256 des deux binaires. |

Les fichiers suivent l'ordre physique des octets de la puce IC8. Le programmateur doit être réglé sur le modèle exact de la puce utilisée. Consultez le [manuel français en PDF](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.88-dev/typestar-basic-manuel-fr.pdf) pour le remplacement de la ROM et son orientation.

Le démarrage du BASIC est également validé sur S-60 / Typestar 6 ; l'ajout d'une liaison série nécessite les composants correspondants. Le firmware BASIC sur S-90 / Typestar 7-II reste à adapter et à valider.

Les sources assembleur sont dans [src/](../src/README.md) et les étapes de construction dans [tools/firmware/](../tools/firmware/README.md). Le firmware utilise les services de la maskROM Canon d'origine ; l'émulateur demande à l'utilisateur de fournir cette maskROM séparément. Voir les [attributions et conditions](../THIRD_PARTY_NOTICES.md).

## English

Current version: **0.4.88-dev**, for Canon S-70 / Typestar 7. The files below are identical to the [release](https://github.com/pR-0000/Typestar-BASIC/releases/tag/v0.4.88-dev) attachments.

| File | Size | Use |
|---|---:|---|
| [typestar-basic-32k.bin](0.4.88-dev/typestar-basic-32k.bin) | 32,768 bytes | IC8: OneROM configured as a 27C256 or a compatible 27C256 chip. Also usable in Studio as the external ROM. |
| [typestar-basic-64k-mirror.bin](0.4.88-dev/typestar-basic-64k-mirror.bin) | 65,536 bytes | IC8: compatible W27C512. The 32 KiB image is repeated twice. |
| [SHA256SUMS.txt](0.4.88-dev/SHA256SUMS.txt) | Text | SHA-256 checksums for both binaries. |

The files use physical IC8 chip byte order. Set the programmer to the exact chip model being used. See the [English PDF manual](https://github.com/pR-0000/Typestar-BASIC/releases/download/v0.4.88-dev/typestar-basic-manuel-en.pdf) for ROM replacement and orientation.

BASIC boot is also validated on S-60 / Typestar 6; adding serial communication requires the corresponding components. BASIC firmware support for S-90 / Typestar 7-II still needs adaptation and validation.

Assembly sources are in [src/](../src/README.md), with build stages in [tools/firmware/](../tools/firmware/README.md). The firmware uses services from the original Canon maskROM; emulator users supply that maskROM separately. See the [attributions and terms](../THIRD_PARTY_NOTICES.md).
