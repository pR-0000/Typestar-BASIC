"""Package .101 only after the complete audit and physical-key checks pass."""
from pathlib import Path
import argparse, hashlib, json

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hardware-validated',action='store_true',
        help='Record the user-confirmed hardware trial of head positioning on 2026-11-24.')
    args=parser.parse_args()
    folder=ROOT/'build/head-jog';audit=ROOT/'build/release-audit-0.4.101'
    cpu=(folder/'EXPERIMENT-NOT-FOR-FLASH-cpu.bin').read_bytes()
    manifest=json.loads((folder/'manifest.json').read_text());digest=hashlib.sha256(cpu).hexdigest()
    assert len(cpu)==32768 and digest==manifest['sha256'] and manifest['version']=='0.4.101-dev'
    reports={}
    for parent,names in ((folder,('validation','graphics-validation','continuous-validation','tile-validation',
            'compatibility-validation','scene-validation','games-validation','quest-startup-validation',
            'quest-rules-validation','piano-registers-validation','head-jog-validation')),
            (audit,('rom-links','rom-data','core','memory','serial','state'))):
        for name in names:
            report=json.loads((parent/(name+'.json')).read_text())
            assert report['result']=='PASS' and report['sha256']==digest,(name,report.get('result'))
            reports[name]={k:v for k,v in report.items() if k!='decoded'}
    assert len(reports['core']['cases'])>=114 and not reports['core']['failures']
    assert len(reports['memory']['boots'])==5 and len(reports['serial']['cases'])==40
    dest=ROOT/'firmware/0.4.101-dev';dest.mkdir(parents=True,exist_ok=True)
    socket=cpu[16384:]+cpu[:16384];images=[]
    for name,data in [('typestar-basic-32k.bin',socket),('typestar-basic-64k-mirror.bin',socket*2)]:
        path=dest/name;path.write_bytes(data)
        images.append(dict(file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    (dest/'SHA256SUMS.txt').write_text(''.join(row['sha256']+'  '+row['file']+'\n' for row in images))
    hardware=('Head-positioning shortcuts confirmed on hardware by user on 2026-11-24'
        if args.hardware_validated else 'Head-positioning hardware trial pending')
    summary=dict(result='PASS',cpu_sha256=digest,reports=reports,hardware=hardware)
    (dest/'validation-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    info=dict(version=manifest['version'],date='2026-11-24',cpu_sha256=digest,images=images,
        occupied_rom_bytes=32768-manifest['explicit_free_bytes'],explicit_free_bytes=manifest['explicit_free_bytes'],
        basic_free_ram_bytes=5951,tokens=37,commands=54,head_jog=manifest['head_jog'],
        software_reports=len(reports),hardware_status=hardware)
    (dest/'release-info.json').write_text(json.dumps(info,indent=2)+'\n')
    for row in images:print(row)
    print('PASS packaging gated by',len(reports),'matching reports')


if __name__=='__main__':main()
