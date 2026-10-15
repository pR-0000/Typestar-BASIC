# Construire les manuels / Building the manuals

Les chapitres Markdown, illustrations et fichiers `manuel-fr.json` et `manuel-en.json` constituent les sources des deux éditions. Les fichiers BASIC publiés dans `examples/` alimentent les listings complets.

The Markdown chapters, illustrations and edition manifests are the source files. Complete listings are synchronized from the programs in `examples/`.

Depuis la racine du projet / From the project root:

```text
python -m pip install -r docs/user-manual/requirements-manual.txt
python docs/user-manual/build_manual.py --config docs/user-manual/manuel-fr.json --output output/pdf/typestar-basic-manuel-fr.pdf
python docs/user-manual/build_manual.py --config docs/user-manual/manuel-en.json --output output/pdf/typestar-basic-manuel-en.pdf
```

La pagination, le sommaire et l'index sont recalculés automatiquement. Chaque PDF est accompagné d'un fichier `.pages.json` décrivant les pages et les références. Les sorties sont ignorées par Git et peuvent être ajoutées aux versions publiées.

Page numbers, contents and index are calculated automatically. Each PDF has a `.pages.json` map. Generated output is ignored by Git and can be attached to a release.

## Illustrations

Une reconstruction du PDF conserve les images existantes, y compris celles retouchées à la main. Les générateurs `render_manual_*.py` servent uniquement à recréer volontairement leurs illustrations ; certains demandent les ROM choisies par l'utilisateur pour exécuter Studio.

Rebuilding a PDF retains existing images, including manual edits. Run `render_manual_*.py` only when deliberately regenerating their illustrations. Studio captures require user-supplied ROM files.

## Vérifications / Checks

```text
python docs/user-manual/validate_manual.py --config docs/user-manual/manuel-fr.json
python docs/user-manual/validate_manual.py --config docs/user-manual/manuel-en.json
```

Ces contrôles vérifient les exemples, leur encodage, leur format tokenisé, l'index et les liens internes. Les options `--mask-rom` et `--firmware-rom` ajoutent l'exécution des ateliers dans l'émulateur. Les rapports vont dans le dossier ignoré `build/user-manual/`.

Checks cover examples, native encoding, tokenized records, index coverage and internal links. Supply `--mask-rom` and `--firmware-rom` to run workshops in the emulator. Reports go into the ignored `build/user-manual/` folder.
