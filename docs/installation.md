# Préparer la mémoire BASIC / Preparing the BASIC ROM

Le chapitre [Installation](user-manual/02-installation-firmware.md) décrit le remplacement d'IC8 et le sens de la puce. The [English installation chapter](user-manual/en/02-installation-firmware.md) covers the same procedure.

| Fichier généré / Generated file | Taille / Size | Puce / Chip |
|---|---|---|
| `typestar-basic-32k.bin` | 32 768 octets / bytes | OneROM configurée en 27C256, ou 27C256 DIP-28 |
| `typestar-basic-64k-mirror.bin` | 65 536 octets / bytes | W27C512 DIP-28 |

Le fichier de 64 Ko répète deux fois le contenu de 32 Ko. La sélection du programmateur correspond au modèle réel de la puce. Les fichiers de programmation et leurs empreintes se trouvent dans le dossier généré `release/installation/`.

The 64 KiB file repeats the 32 KiB image twice. Select the actual chip model in the programmer. Generated programming images and hashes go into `release/installation/`.

Pour régénérer les images de la version du manifeste du manuel / To prepare images for the firmware selected by the manual manifest:

```text
python docs/user-manual/prepare_installation_images.py
```

Le script vérifie le manifeste et le SHA-256 du firmware choisi. The script checks the selected firmware manifest and SHA-256 before creating images.
