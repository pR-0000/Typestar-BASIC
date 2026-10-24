"""Package .97 only after reports agree on the exact tested CPU image."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'build/tile-stream';cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    digest=hashlib.sha256(cpu).hexdigest();m=json.loads((out/'manifest.json').read_text())
    names=('validation','graphics-validation','tile-validation','piano-registers-validation','compatibility-validation')
    reports={n:json.loads((out/(n+'.json')).read_text()) for n in names}
    reports['quest-startup']=json.loads((ROOT/'build/quest-canon-s70-quest-fr-startup.json').read_text())
    reports['quest-rules']=json.loads((ROOT/'build/quest-rules-validation.json').read_text())
    assert len(cpu)==32768 and digest==m['sha256']
    assert all(r['result']=='PASS' and r['sha256']==digest for r in reports.values())
    assert reports['validation']['font_characters']==95 and reports['validation']['keyboard_cases']==1760
    assert len(reports['validation']['sound_cases'])==17
    assert reports['piano-registers-validation']['commands']==468
    assert reports['graphics-validation']['tokens']==37 and reports['graphics-validation']['commands']==54
    assert reports['tile-validation']['physical_break'] and reports['tile-validation']['unchanged_array_and_heap']
    assert reports['quest-startup']['jobs']==35 and reports['quest-startup']['tiles']==602
    assert m['explicit_free_bytes']==102
    socket=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.97-dev-canon-start-nh7'
    for suffix,data in [('',socket),('-64k-mirror',socket*2)]:
        p=ROOT/'release'/(name+suffix+'.bin');p.write_bytes(data)
        p.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+p.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),
             status='Software tile, graphics, sound, Piano, keyboard, font, tokenizer and Quest checks passed; hardware validation pending',
             validations={k:{n:v for n,v in r.items() if n not in ('events','motions')} for k,r in reports.items()})
    (ROOT/'release'/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(name+'.bin',m['nh7_sha256'])

if __name__=='__main__':main()
