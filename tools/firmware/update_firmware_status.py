"""Generate current + per-version Markdown status from the actual built image.
The capability catalogue must be reviewed for each firmware version. No ROM edits.
"""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
# Exclusive limits of the current linker allocations, NOT globally free ROM.
LIMITS = {0x4200: 0x4400, 0x4400: 0x4800, 0x4800: 0x5000}


def measure(manifest, symbols):
    blocks = [('Interpréteur principal', 0x5000, 0x67C2, manifest['code_bytes'])]
    for module in sorted(manifest['modules'], key=lambda m: m['origin']):
        start = module['origin']
        blocks.append((module['name'], start, LIMITS[start], module['bytes']))
    assert symbols['CODEEND'] == 0x5000 + manifest['code_bytes']
    assert all(0 < size <= end-start for _, start, end, size in blocks)
    payload = sum(b[3] for b in blocks)
    headroom = sum(b[2]-b[1]-b[3] for b in blocks)
    regions = [(int(a, 16), int(b, 16)+1) for a,b in manifest['replaced_cpu_regions']]
    ordered = sorted(regions)
    assert all(a[1] <= b[0] for a,b in zip(ordered, ordered[1:])), 'Overlapping ROM regions'
    replaced = sum(b-a for a,b in regions)
    hooks = replaced-payload
    assert hooks == 54, 'Review startup trampoline sizes'
    return blocks, payload, headroom, hooks


def render(manifest, symbols, budget, catalog):
    version = manifest['version']
    if catalog['reviewed_version'] != version:
        raise ValueError('Review tools/firmware/basic_capabilities.json for version '+version)
    blocks, payload, headroom, hooks = measure(manifest, symbols)
    rom = manifest['images']['s70-basic-nh7.bin']['size']
    arena = symbols['PROGRAMEND']-symbols['PROGRAM']+1
    lines = [f'# État de Typestar BASIC — {version}', '',
        'Boot: titre puis compteur BYTES FREE, chacun attend une touche.', '',
        'RAM documentaire integree : 5952 octets, soit 5951 libres a vide ; lignes 1..255.', '',
        '> Généré par tools/firmware/update_firmware_status.py à partir du manifeste et des symboles assemblés.',
        '> Ne pas éditer ce fichier directement : modifier le catalogue ou le générateur, puis reconstruire.', '',
        f"Image : `{manifest['images']['s70-basic-nh7.bin']['sha256']}` (SHA-256).", '',
        f"Validation matérielle confirmée jusqu’à **{catalog['hardware_validated_through']}**. Les ajouts ultérieurs restent à confirmer ; une compilation ne constitue pas une validation matérielle.", '',
        '## ROM', '',
        '| Mesure | Octets |', '|---|---:|',
        f'| Image IC8/NH7 complète | {rom} (32 Kio) |',
        f'| Blocs propres au BASIC, données constantes comprises | {payload} |',
        f'| Deux modifications du démarrage Canon (6 + 48) | {hooks} |',
        f'| Total implanté par notre firmware | {payload+hooks} |',
        f'| Octets Canon conservés dans IC8 (pas de la place libre) | {rom-payload-hooks} |',
        f'| Marge dans les allocations actuelles du BASIC | {headroom} |', '',
        '| Bloc | Début CPU | Limite exclusive | Occupé | Marge |', '|---|---|---|---:|---:|']
    for name,start,end,size in blocks:
        lines.append(f'| {name} | ${start:04X} | ${end:04X} | {size} | {end-start-size} |')
    lines += ['', 'La marge est fragmentée : elle ne forme pas un bloc contigu. Les autres octets',
        'appartiennent aux tables/polices ou au code Canon conservés, ou à des limites',
        'protégées. Leur réaffectation demande une analyse et une modification du placement.',
        'La maskROM IC9 de 16 Kio reste dans le MCU ; elle ne fait pas partie de cette image.',
        'Dans la zone $6800..$BFFF (22528 octets), 22474 octets restent inchangés et 54 sont remplacés.', '',
        '## RAM et limites', '',
        f'- Programme : **{arena} octets**, dont une sentinelle finale, soit **{arena-1} octets** pour les enregistrements.',
        '- Ce budget comprend les numéros et terminateurs de lignes ; ce ne sont pas 5951 caractères utiles garantis.',
        '- Les zones partagées ne s’additionnent pas : leur utilisation dépend du mode (démarrage, édition ou RUN).', '',
        '| Adresses | Taille | Utilisation / contrainte |', '|---|---:|---|']
    for row in budget['ram_current']:
        lines.append(f"| {row['region']} | {row['bytes'] if row['bytes'] is not None else 'variable'} | {row['owner']} |")
    lines += ['', 'Le trou $1B5B..$1B5F (5 octets) n’est affecté à aucun bloc de cette carte ;',
        'il ne constitue pas une réserve suffisante pour des variables réelles.', '',
        '### Contraintes du langage et du matériel', '']
    lines += ['- '+c for c in catalog['constraints']]
    for title,key in [('Commandes intégrées','commands'),('Fonctions intégrées','functions')]:
        lines += ['', '## '+title, '', '| Syntaxe | Comportement / limite |', '|---|---|']
        lines += [f'| `{syntax}` | {description} |' for syntax,description in catalog[key]]
    lines += ['', '## Non intégré à cette image', '']
    lines += ['- '+c for c in catalog['not_integrated']]
    comp = budget['compression']
    lines += ['', '## Nombres décimaux : faisabilité', '',
        f'**Non intégré ; {headroom} octets de marge actuels.** Les 32 Kio',
        'ne sont pas tous disponibles pour l’interpréteur. Un calculateur réel demande les',
        'opérations arithmétiques, les conversions texte/nombre, PRINT, les comparaisons,',
        'les erreurs de domaine/débordement et l’adaptation des variables, boucles et fonctions.',
        'Le coût ROM n’est pas mesuré : aucune bibliothèque flottante HD6301 n’est intégrée',
        'ou estimée comme tenant déjà dans la place disponible.', '',
        'Pour 26 variables : 4 octets par nombre demanderaient 104 octets (+52) ;',
        '5 octets demanderaient 130 (+78) ; 8 octets demanderaient 208 (+156).',
        'Ces chiffres excluent les temporaires, les cadres FOR et les tableaux. La zone',
        'actuelle des variables est suivie immédiatement des états FOR/GOSUB : on ne peut',
        'pas simplement élargir les variables sur place. Une allocation à la demande',
        'éviterait de réserver tous les nombres, mais ajouterait index et métadonnées.', '',
        'Le moteur décimal Canon a été identifié après confirmation de CODE+C sur S-70.',
        'Les routines maskROM +/−/×/÷ passent 28 cas exacts et 11 cas limites simulés.',
        'Elles utilisent huit chiffres décimaux et un octet signe/échelle. Leur scratch',
        'chevauche le programme BASIC, avec une écriture supplémentaire observée à $1EE6.',
        'Priorité : adaptateur protégeant la RAM, conversions et stockage compact ;',
        'cette découverte ne signifie pas que les décimaux sont déjà intégrés.',
        'Prototype séparé : 353 octets de code, 194 octets de sauvegarde temporaire',
        'sur pile ; 294 calculs et 9 refus contrôlés. Voir `native-decimal-adapter.md`.',
        'Variante réservée : 237 octets de code, 36 octets sauvegardés sur pile,',
        '294 calculs et 9 refus valides ; ancienne variante temoin a 587 octets, remplacee par la piste documentaire.',
        'Codec compact : 114 octets, 672 tests, cinq octets par nombre sans perte.',
        'Noyau expressions/affectations : 805 octets ; constantes, priorités, parenthèses,',
        'formatage et variables allouées à la demande (6 octets par variable créée).',
        'CRC du texte utilisé : 103 octets, 21 tests. Voir `decimal-integration.md`.',
        'Ces fragments totalisent 1259 octets ; ils ne sont pas dans cette image.',
        '60 expressions, 11 erreurs, 4 séparateurs et 36 scénarios de variables validés.',
        'Prototype decimal historique separe : PRINT/LET/MEM et RUN raccordes ; passerelle 181 octets.',
        'Rétention candidate 899 octets : programme de 541 octets conservé lors de',
        'quatre boots simulés. Ancienne signature rejetée, aucune migration ni release.',
        'Les autres commandes numériques et le placement papier restent à adapter.', '',
        'Une réorganisation hors publication est décrite dans `docs/decimal-engine-preparation.md`.',
        'Ses marges expérimentales ne sont pas incluses dans les chiffres de cette version.', '',
        'La virgule fixe suffirait à certains tracés, mais ne remplacerait pas une gestion',
        'générale des nombres réels de type BASIC Microsoft.', '',
        '### Compression : mesures exploratoires, pas espace récupéré', '',
        f"Sur les {comp['raw_bytes']} octets de ressources originales : RLE {comp['byte_rle_bytes']} octets",
        f"(gain brut {comp['byte_rle_gross_saving']}) ; zlib {comp['zlib9_bytes']} octets (gain brut {comp['zlib_gross_saving']}).",
        'Ce ne sont pas des gains nets disponibles dans le firmware : ils portent sur',
        'les ressources originales entières, dont une partie est déjà remplacée par le BASIC.',
        'Il manque le décodeur embarqué, les index et un accès aux glyphes à la demande.',
        'Décompresser ces ressources intégralement demanderait 10 Kio de RAM, indisponibles',
        'dans notre allocation actuelle. Ne pas additionner ces gains à la marge ROM.', '',
        '## Mise à jour à chaque version', '',
        '1. Mettre à jour src/firmware.json et réviser tools/firmware/basic_capabilities.json (version, commandes, limites, validation matérielle).',
        '2. Exécuter python tools/firmware/build.py : le budget JSON et ce rapport sont régénérés après assemblage.',
        '3. Exécuter python tools/firmware/package_canon_basic.py : les rapports sont contrôlés/régénérés et inclus dans l’archive.',
        '4. docs/firmware-status.md décrit la dernière construction ; docs/status/<version>.md conserve un état par version.',
        '', 'Le générateur refuse un catalogue d’une autre version et vérifie les empreintes',
        'des sources et de l’image. Une modification de capacité nécessite aussi de mettre',
        'à jour ses limites de placement ; aucune marge n’est extrapolée automatiquement.', '']
    return '\n'.join(lines)


def main():
    manifest = json.loads((ROOT/'build/canon-basic/manifest.json').read_text())
    symbols = json.loads((ROOT/'build/canon-basic/symbols.json').read_text())
    catalog = json.loads((ROOT/'tools/firmware/basic_capabilities.json').read_text(encoding='utf-8'))
    if catalog['reviewed_version'] != manifest['version']:
        raise ValueError('Review tools/firmware/basic_capabilities.json for '+manifest['version'])
    for name,digest in manifest['source_files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, 'Stale build: '+name
    for name,record in manifest['images'].items():
        data = (ROOT/'build/canon-basic'/name).read_bytes()
        assert len(data) == record['size'] and hashlib.sha256(data).hexdigest() == record['sha256'], name
    subprocess.run([sys.executable,str(ROOT/'tools/audit_memory_budget.py')],check=True,capture_output=True)
    budget = json.loads((ROOT/'_local/development/analysis/typestar-basic-budget.json').read_text())
    assert budget['identity']['version'] == manifest['version']
    content = render(manifest,symbols,budget,catalog)
    history = ROOT/'docs/status'
    history.mkdir(exist_ok=True)
    (history/(manifest['version']+'.md')).write_text(content,encoding='utf-8')
    (ROOT/'docs/firmware-status.md').write_text(content,encoding='utf-8')
    print('Updated firmware status for '+manifest['version'])


if __name__ == '__main__':
    main()
