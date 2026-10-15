"""Read-only S-70 font cartridge window, as observed through the CPU bus.

This models the measured $4000..$67FF window, not an inferred physical chip
capacity or RAM banking scheme. No ROM content is bundled with Studio.
"""
from pathlib import Path
from dataclasses import dataclass
import hashlib

WINDOW_SIZE=0x2800
CAPTURE_HASHES={
    '3450adc700689a89a877420ac49ae767e8bcc2485acc6dd22d27f078579753e7':'COURIER 12II',
    'f5992f95335cf9441ce5c32e83db330fdddea0be0c4591f281e129bb03ca8105':'DICTIONARY PSII',
}

@dataclass(frozen=True)
class FontCartridge:
    data: bytes
    name: str
    sha256: str
    source_format: str

    def read(self,address):
        if not 0x4000<=address<0x6800:raise ValueError('Outside font cartridge window')
        return self.data[address-0x4000]

    def metadata(self):
        return dict(name=self.name,sha256=self.sha256,format=self.source_format,
                    window='4000-67FF',bytes=len(self.data))

def load_cartridge(path):
    if not path:return None
    raw=Path(path).read_bytes();digest=hashlib.sha256(raw).hexdigest()
    if len(raw)==32768 and digest in CAPTURE_HASHES:
        data=raw[:WINDOW_SIZE];kind='verified CPU capture'
    elif len(raw)==WINDOW_SIZE:
        data=raw;kind='CPU resource window'
    else:
        raise ValueError('Font cartridge: expected a 10240-byte CPU resource window or a recognised 32768-byte cartridge capture')
    name=CAPTURE_HASHES.get(digest)
    if not name:
        header=data[1:31]
        name=header.decode('ascii').strip() if all(32<=v<127 for v in header) else ''
    return FontCartridge(bytes(data),name or Path(path).name,digest,kind)
