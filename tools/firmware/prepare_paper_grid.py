"""Package .99 after exact-image graphics, sound and example regressions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'build/paper-grid';cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(cpu).hexdigest();m=json.loads((out/'manifest.json').read_text())
    reports={n:json.loads((out/(n+'.json')).read_text()) for n in (
        'validation','graphics-validation','continuous-validation','tile-validation',
        'compatibility-validation','scene-validation','games-validation')}
    reports['quest-rules']=json.loads((ROOT/'build/quest-rules-validation.json').read_text())
    assert len(cpu)==32768 and digest==m['sha256']
    assert all(r['result']=='PASS' and r['sha256']==digest for r in reports.values())
    assert m['explicit_free_bytes']==59 and m['tile_stream']['maximum_columns']==40
    socket=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.99-dev-canon-start-nh7'
    for suffix,data in (('',socket),('-64k-mirror',socket*2)):
        path=ROOT/'release'/(name+suffix+'.bin');path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+path.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),status='Software regressions passed; paper alignment and gameplay feedback pending on hardware',
             validations=reports)
    (ROOT/'release'/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(name+'.bin',m['nh7_sha256'])


if __name__=='__main__':main()
