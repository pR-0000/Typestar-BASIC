"""Package the .95 candidate only after sound and graphics regressions pass."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'build/sound-synth';cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    m=json.loads((out/'manifest.json').read_text());r=json.loads((out/'validation.json').read_text());g=json.loads((out/'graphics-validation.json').read_text())
    assert len(cpu)==32768 and hashlib.sha256(cpu).hexdigest()==m['sha256']==r['sha256']==g['sha256']
    assert r['result']==g['result']=='PASS' and r['font_characters']==95 and r['keyboard_cases']==1760
    assert len(r['sound_cases'])==15 and r['parser_cases']==19 and r['noise_heap_guard'] and r['break_cleanup']
    assert len(r['piano'])==2 and all(v['sound_commands']==26 for v in r['piano'])
    assert g['tokens']==37 and g['commands']==54 and g['free_basic_bytes']==5951
    socket=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.95-dev-canon-start-nh7'
    for suffix,data in [('',socket),('-64k-mirror',socket*2)]:
        path=ROOT/'release'/(name+suffix+'.bin');path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+path.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),status='Sound, keyboard, font and graphics regressions passed; hardware acoustic validation pending')
    (ROOT/'release'/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(name+'.bin',m['nh7_sha256'])

if __name__=='__main__':main()
