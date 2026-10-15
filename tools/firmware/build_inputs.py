"""Resolve read-only inputs from the active release folder or a local archive."""
from configparser import ConfigParser
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]


def release_input(name):
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Expected a filename relative to the release directory')
    roots = [ROOT / 'release']
    configured = os.environ.get('TYPESTAR_FIRMWARE_ARCHIVE')
    if configured:
        roots.append(Path(configured).expanduser())
    config = ConfigParser()
    config.read(ROOT / '_local/build-inputs.ini', encoding='utf8')
    if config.has_option('inputs', 'firmware_archive'):
        roots.append(Path(config['inputs']['firmware_archive']).expanduser())
    for directory in roots:
        candidate = directory / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f'Build input {name} is missing; set TYPESTAR_FIRMWARE_ARCHIVE or _local/build-inputs.ini')
