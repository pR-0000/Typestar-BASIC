"""Package .91 after native-command equivalence, X/Y and relocated-data checks."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'build/paper-y-poststep'
    cpu=(out/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    m=json.loads((out/'manifest.json').read_text())
    report=json.loads((out/'validation.json').read_text())
    digest=hashlib.sha256(cpu).hexdigest()
    assert len(cpu)==32768 and digest==m['sha256']==report['sha256']
    assert report['result']=='PASS'
    assert report['native_call_equivalence'] and report['coil_state_equivalence']
    assert report['normalization_cases']==3840 and report['x_commanded_drift']==0
    assert report['font_glyphs']==95 and report['token_entries']==37 and report['command_entries']==54
    assert report['origin_spacing_preserved'] and m['explicit_free_bytes']==70
    raw=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.91-dev-canon-start-nh7'
    for suffix,data in [('',raw),('-64k-mirror',raw*2)]:
        path=ROOT/'release'/(name+suffix+'.bin')
        assert not path.exists() or path.read_bytes()==data
        path.write_bytes(data)
        path.with_suffix('.sha256').write_text(hashlib.sha256(data).hexdigest()+'  '+path.name+'\n')
    m.update(nh7_sha256=hashlib.sha256(raw).hexdigest(),
        status='Native call/coil-state equivalence, X/Y and font checks passed; physical paper validation pending')
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
    (ROOT/'release'/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    print(name+'.bin',m['nh7_sha256'])


if __name__=='__main__':main()
