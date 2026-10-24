"""Package .100 only after every required report passes for its exact SHA-256."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[2]


def main():
    folder=ROOT/'build/release-candidate'
    cpu=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    m=json.loads((folder/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
    assert len(cpu)==32768 and digest==m['sha256'] and m['version']=='0.4.100-dev'
    assert m['explicit_free_bytes']==58 and m['tile_stream']['maximum_columns']==40
    audit=ROOT/'build/release-audit-0.4.100'
    reports={}
    for parent,names in ((folder,(
            'validation','graphics-validation','continuous-validation','tile-validation',
            'compatibility-validation','scene-validation','games-validation',
            'quest-startup-validation','quest-rules-validation','piano-registers-validation')),
            (audit,('rom-links','rom-data','core','memory','serial','state'))):
        for name in names:
            report=json.loads((parent/(name+'.json')).read_text())
            assert report['result']=='PASS' and report['sha256']==digest,(name,report.get('result'),report.get('sha256'))
            # Keep the release manifest compact; the complete disassembly map
            # remains in the generated audit directory for local inspection.
            reports[name]={k:v for k,v in report.items() if k!='decoded'}
    assert len(reports['core']['cases'])>=114 and not reports['core']['failures']
    assert len(reports['memory']['boots'])==5 and len(reports['serial']['cases'])==40
    assert len(reports['rom-data']['error_messages'])==25
    socket=cpu[16384:]+cpu[:16384];name='s70-basic-0.4.100-dev-canon-start-nh7'
    dest=ROOT/'release';dest.mkdir(exist_ok=True);images=[]
    for suffix,data in (('',socket),('-64k-mirror',socket*2)):
        path=dest/(name+suffix+'.bin');sha=hashlib.sha256(data).hexdigest()
        path.write_bytes(data);path.with_suffix('.sha256').write_text(sha+'  '+path.name+'\n')
        assert path.read_bytes()==data
        images.append(dict(file=path.name,bytes=len(data),sha256=sha))
    m.update(nh7_sha256=images[0]['sha256'],images=images,validations=reports,
             status='All software audit gates passed; hardware smoke test pending',
             hardware_scope='Functional mechanical model; physical registration, acoustics and electrical cable faults require real hardware')
    (dest/(name+'-manifest.json')).write_text(json.dumps(m,indent=2)+'\n')
    for row in images:print(row)
    print('PASS packaging gated by',len(reports),'matching software reports')


if __name__=='__main__':main()
