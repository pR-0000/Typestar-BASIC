"""Package the .94 test candidate only after regressions on the exact image."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'build/glyph-pair';cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    m=json.loads((out/'manifest.json').read_text());r=json.loads((out/'validation.json').read_text())
    assert len(cpu)==32768 and hashlib.sha256(cpu).hexdigest()==m['sha256']==r['sha256']
    assert r['result']=='PASS' and r['legacy_cases']==6 and r['font_characters']==95
    assert r['tokens']==37 and r['commands']==54 and r['free_basic_bytes']==5951
    assert len(r['wide_cases'])==4 and r['break_cleanup'] and r['blank_skip']
    assert r.get('wide_matrix') and r.get('offset_source_and_if')
    assert m['explicit_free_bytes']==63
    socket=cpu[16384:]+cpu[:16384];release=ROOT/'release'
    name='s70-basic-0.4.94-dev-canon-start-nh7'
    for suffix,data in [('',socket),('-64k-mirror',socket*2)]:
        path=release/(name+suffix+'.bin');path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+path.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(socket).hexdigest(),status='CPU glyph/font/bounds/BREAK regressions passed; hardware validation pending')
    (release/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    (release/'glyph-pair-test.bas').write_bytes((ROOT/'tools/diagnostics/glyph-pair-test.bas').read_bytes())
    print(name+'.bin',m['nh7_sha256'])
if __name__=='__main__':main()
