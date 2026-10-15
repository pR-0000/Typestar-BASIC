"""Package the first linked PBOX hardware-test image, after CPU regressions."""

import sys as _build_sys
from pathlib import Path as _BuildPath
_build_sys.path.insert(0, str(_BuildPath(__file__).resolve().parents[2] / "tools"))
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'build/paper-rom-bridge'
def main():
 cpu=(base/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes();digest=hashlib.sha256(cpu).hexdigest();m=json.loads((base/'manifest.json').read_text())
 assert len(cpu)==32768 and digest==m['sha256'] and m['paper_real_ram'] and m['version']=='0.4.56-dev'
 paths=[base/'graphics-packed-validation.json',base/'retention-validation.json',base/'decimal-for-validation.json',base/'paper-errors-validation.json',base/'native-rom-audit.json',ROOT/'build/paper-rom-bridge-test/validation.json']
 for p in paths:
  r=json.loads(p.read_text());assert r['sha256']==digest,p
  if 'result' in r:assert r['result']=='PASS',p
 audit=json.loads((base/'native-rom-audit.json').read_text())
 for group in ('decimal_add','decimal_subtract','decimal_multiply','decimal_divide','keyboard_translate','startup_helper','motion_scheduler','periodic_irq','pattern_decoder'):
  assert not audit['groups'][group]['first_code_collisions'],group
 raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.56-dev-canon-start-nh7';out=ROOT/'release'
 target=out/(name+'.bin');assert not target.exists() or target.read_bytes()==raw
 report=dict(version='0.4.56-dev',status='Hardware test image; S-70 validation pending',cpu_sha256=digest,nh7_sha256=hashlib.sha256(raw).hexdigest(),paper_code_bytes=869,known_free_fragmented_bytes=97,ram=json.loads((ROOT/'tools/firmware/paper_ram_map.json').read_text()),validation_reports=[str(p.relative_to(ROOT)) for p in paths],candidate_manifest=m,limits=['One PBOX or CODE+P job per boot','Native paper font descriptor table partially replaced; LPRINT unavailable','Physical geometry and real motor timing not validated by CPU model'],source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ('src','tools') for p in sorted((ROOT/d).glob('*')) if p.is_file()})
 target.write_bytes(raw);(out/(name+'-manifest.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 old=(ROOT/'docs/status/0.4.55-dev.md').read_text(encoding='utf-8');a=old.index('## Commandes intégrées');b=old.index('## Vérification',a);commands=old[a:b].replace('`RANDOMIZE`,','`PBOX`, `RANDOMIZE`,').replace('LPRINT ou instructions graphiques papier BASIC.','LPRINT. PBOX propose un premier rectangle papier vide/plein.')
 text="""# État de Typestar BASIC — 0.4.56-dev

Image de test S-70 prête ; validation matérielle attendue. Dernière référence
matérielle précédente : 0.4.55-dev. [Instructions](basic-0.4.56.md).

PBOX imprime un rectangle par bandes, depuis des expressions BASIC et des
éléments de tableaux. Le programme et les variables sont conservés. BREAK
est testé entre bandes. Une seule impression (PBOX ou CODE+P) par démarrage.

| Statistique | Valeur |
|---|---:|
| Image IC8 | 32768 octets |
| Arène BASIC | 5952 octets |
| Libre à vide | 5951 octets |
| Code papier intégré | 869 octets |
| Trous ROM suivis restants | 97 octets fragmentés |
| Tampon/sauvegarde papier | 284..732 octets temporaires |
| Contrôle/glyphe papier | 108 octets partagés ou interstitiels |
| Tokens | 37 (PBOX conservé en ASCII) |
| Numéros de lignes | 1..65535 |
| Saisie | 63 caractères, numéro compris |
| Précision | 8 chiffres significatifs, au plus 7 décimales |
| Profondeur FOR/GOSUB | 8/8 |

Les 97 octets ne mesurent pas toute la ROM potentiellement récupérable. Les
anciens descripteurs de police papier à 4000..41FF sont remplacés ; la future
police LPRINT devra être reconstruite et compactée. La police LCD est conservée.

Tests CPU : onze scénarios papier (succès, défauts, manque de RAM, BREAK),
PBOX dans FOR avec paramètres issus d'un tableau, reprise du calcul après
impression, mode graphique série, rétention et boucles décimales. Les erreurs
PBOX sont dirigées vers BASIC ; les erreurs CODE+P gardent leur retour éditeur.
Minuterie/capteurs simulés : l'essai sur machine reste nécessaire.

"""+commands+'\nSHA-256 NH7 : `'+report['nh7_sha256']+'`.\n\n[Budget et perspectives](memory-roadmap.md) — [Intégration papier](paper-basic-integration.md).\n'
 (ROOT/'docs/firmware-status.md').write_text(text,encoding='utf-8');(ROOT/'docs/status/0.4.56-dev.md').write_text(text.replace('(basic-','(../basic-').replace('(memory-roadmap','(../memory-roadmap').replace('(paper-basic-integration','(../paper-basic-integration'),encoding='utf-8')
 print('READY',target.name,report['nh7_sha256'])
if __name__=='__main__':main()
