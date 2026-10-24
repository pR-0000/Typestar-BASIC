# Typestar BASIC 0.4.100-dev

[Français](#français) · [English](#english)

## Français

Images du **24 octobre 2026**, accompagnées de **Studio 0.2.40**. Utilisez l’image **32 Kio** pour OneROM configurée en **27C256**, une puce 27C256 compatible ou la ROM externe de Studio. L’image **64 Kio miroir** contient deux copies identiques pour une **W27C512** compatible.

| Ressource | Valeur |
|---|---:|
| ROM IC8 | 32 768 octets |
| ROM occupée / réserve explicite | 32 710 / 58 octets |
| Image miroir | 65 536 octets |
| RAM BASIC libre à vide | 5 951 octets |
| Tokens / commandes | 37 / 54 |
| Rangée GLYPH mode 5 | 1 à 40 motifs différents ou vides |

Les fichiers sont rangés dans l’ordre physique d’IC8. Le programmateur doit utiliser le modèle exact de votre puce. Le [manuel](../../docs/user-manual/README.md) décrit l’installation et le [guide S-60](../../docs/hardware/typestar-6-serial-upgrade.md) identifie la révision et les composants validés. Le programme, les variables et les tampons partagent la RAM disponible.

Les [notes de version](../../docs/releases/0.4.100-dev.md) présentent le son continu, les cartes rapides, Quest, Piano et les corrections. [SHA256SUMS.txt](SHA256SUMS.txt) couvre les deux binaires ; [release-info.json](release-info.json) contient les statistiques et empreintes, et [validation-summary.json](validation-summary.json) résume les contrôles. Le conditionnement exige seize rapports logiciels réussis pour le hash exact de la ROM. Les mouvements et l’acoustique se valident aussi sur la machine réelle.

## English

Images dated **24 October 2026**, accompanied by **Studio 0.2.40**. Use the **32 KiB** image for OneROM configured as a **27C256**, a compatible 27C256 chip or Studio’s external ROM. The **64 KiB mirrored** image contains two identical copies for a compatible **W27C512**.

| Resource | Value |
|---|---:|
| IC8 ROM | 32,768 bytes |
| Occupied ROM / explicit reserve | 32,710 / 58 bytes |
| Mirrored image | 65,536 bytes |
| Empty BASIC free RAM | 5,951 bytes |
| Tokens / commands | 37 / 54 |
| GLYPH mode 5 row | 1 to 40 different or blank tiles |

Files use physical IC8 byte order. Set the programmer to your exact chip model. The [manual](../../docs/user-manual/en/README.md) describes installation, and the [S-60 guide](../../docs/hardware/typestar-6-serial-upgrade.md#english) identifies the tested revision and components. Programs, variables and temporary buffers share the available RAM.

The [release notes](../../docs/releases/0.4.100-dev.md#english) cover continuous sound, fast maps, Quest, Piano and fixes. [SHA256SUMS.txt](SHA256SUMS.txt) covers both binaries; [release-info.json](release-info.json) records statistics and hashes, and [validation-summary.json](validation-summary.json) summarizes checks. Packaging requires sixteen passing software reports for the exact ROM hash. Movement and acoustics also require real-machine checks.
