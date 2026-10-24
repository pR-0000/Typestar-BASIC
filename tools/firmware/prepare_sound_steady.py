"""Package the .96 candidate after sound, Piano and graphics regressions."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'build/sound-steady';cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    m=json.loads((out/'manifest.json').read_text())
    reports={name:json.loads((out/(name+'.json')).read_text()) for name in
             ('validation','graphics-validation','piano-registers-validation','batch-gap-validation')}
    r,g,p,b=(reports[k] for k in reports)
    assert len(cpu)==32768 and hashlib.sha256(cpu).hexdigest()==m['sha256']==r['sha256']==g['sha256']
    assert all(v['result']=='PASS' for v in reports.values())
    assert r['font_characters']==95 and r['keyboard_cases']==1760
    assert len(r['sound_cases'])==17 and r['noise_heap_guard'] and r['break_cleanup']
    assert len(r['piano'])==2 and all(v['sound_commands']==40 for v in r['piano'])
    assert p['commands']==468 and p['notes']==26 and p['registers']==3
    assert g['tokens']==37 and g['commands']==54 and g['free_basic_bytes']==5951
    socket=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.96-dev-canon-start-nh7'
    for suffix,data in [('',socket),('-64k-mirror',socket*2)]:
        path=ROOT/'release'/(name+suffix+'.bin');path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+path.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),
             status='Software sound, Piano, keyboard, font and graphics regressions passed; hardware acoustic validation pending')
    (ROOT/'release'/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(name+'.bin',m['nh7_sha256'])

if __name__=='__main__':main()
