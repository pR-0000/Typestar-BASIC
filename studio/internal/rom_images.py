from i18n import tr
"""Explicit file-backed ROM loading for the supported functional machine profile."""
from pathlib import Path
import hashlib
import json

CPU_SHA = 'dfa8c68a0292de7c96e1f0719f5a4701fd416eb230632026af1504869d31c7f6'
NATIVE_SHA = 'feedfc9d73e1e07ce06c8e6c39a1dda28d82e3e889023ebff0629e2c2b034b1e'
PROFILES = {CPU_SHA:'0.4.82', NATIVE_SHA:'0.4.83',
    'b737bae8f0f2b20921758b1e2237c8fef86135d0f0145893fec86de2cd2d5a69':'0.4.84',
    '294c03f31beca5ed7691c6c7014d5e7a66b652d58df7a34f004f080d32f8d9f7':'0.4.85',
    '776a563501b8c5ad8e248c67ff113b3996be576e1d7545ee778f604ce6cd9e58':'0.4.86',
    '330d00173287c65576bb3ee988008750c2953265929441964a08711af59859da':'0.4.87',
    'c6c4a5b26e1b61fa6ff05936c30e8f220a0dce0fbd95d861f4965204d066647e':'0.4.88'}
MASK_SHA = '9679e78d87398c918818aa76f608cdd72132075fe7286cf1333cf6d1a8f1cf3d'

def load_roms(mask_path, firmware_path, mode='auto', layout='auto'):
    """Load bytes without executing them. Unknown images require explicit layout.

    mode: auto enables BASIC conveniences only for a known pair; generic never
    applies them. Layout describes the external ROM, not the internal maskROM.
    """
    if mode not in ('auto', 'generic', 'basic'):
        raise ValueError('Unknown emulation mode: '+str(mode))
    if layout not in ('auto', 'socket', 'cpu'):
        raise ValueError('Unknown ROM layout: '+str(layout))
    mask = Path(mask_path).read_bytes()
    raw = Path(firmware_path).read_bytes()
    if len(mask) != 16384:raise ValueError(tr('La maskROM doit faire 16 384 octets.'))
    if len(raw) != 32768:raise ValueError(tr('La ROM externe doit faire 32 768 octets.'))
    mask_sha = hashlib.sha256(mask).hexdigest()
    raw_sha = hashlib.sha256(raw).hexdigest()
    swapped = raw[16384:] + raw[:16384]
    swapped_sha = hashlib.sha256(swapped).hexdigest()
    # Both layouts are supported, but never guess the order of unknown bytes.
    known_socket = {
        '5eb09f28e9e93989631544f1f13defe32679e86300702692e5c7d137f168f03c',
        '5588488ad4435da3ec5812e5eafb1a457d4a3a23d40eecc2a5fa92cff82d7990',
        'cf444967bc00586706ff1bc96a051a4e007c2abeda2fb609740c386135c95731',
    }
    if layout == 'auto':
        if raw_sha in PROFILES or swapped_sha in known_socket:layout='cpu'
        elif swapped_sha in PROFILES or raw_sha in known_socket:layout='socket'
        else:
            raise ValueError(tr('ROM inconnue : choisir explicitement l’ordre IC8/OneROM ou CPU.'))
    image = raw if layout == 'cpu' else swapped
    version = PROFILES.get(hashlib.sha256(image).hexdigest())
    basic = version is not None and mask_sha == MASK_SHA and mode != 'generic'
    if mode == 'basic' and not basic:
        raise ValueError(tr('Cette paire de ROM ne possède pas de profil BASIC reconnu.'))
    symbols = {}
    if basic:
        symbols = json.loads((Path(__file__).parent/f'profiles/basic-{version}-symbols.json').read_text(encoding='utf-8'))
    info = dict(mask=str(Path(mask_path).resolve()), firmware=str(Path(firmware_path).resolve()),
                mask_sha256=mask_sha, firmware_sha256=raw_sha,
                layout=layout, mode='basic' if basic else 'generic',
                profile=f'S-70 / BASIC {version}-dev' if basic else 'S-70 functional hardware / experimental',
                basic_available=basic)
    return image,mask,symbols,info
