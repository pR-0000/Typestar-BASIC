"""Run the release's actual-ROM regressions, stopping on the first failure.

Run from the repository with a Python environment containing the Studio and
diagnostic dependencies. The incremental firmware build must exist first.
"""
from pathlib import Path
import argparse,subprocess,sys

ROOT=Path(__file__).resolve().parents[2]
SUITES=(
    'tools/diagnostics/audit_rom_links.py',
    'tools/diagnostics/audit_rom_data.py',
    'tools/diagnostics/release_core_suite.py',
    'tools/diagnostics/release_memory_suite.py',
    'tools/diagnostics/release_serial_suite.py',
    'tools/diagnostics/release_state_suite.py',
    'tools/diagnostics/validate_sound_synth.py',
    'tools/diagnostics/validate_sound_continuous.py',
    'tools/diagnostics/validate_piano_registers.py',
    'tools/diagnostics/validate_glyph_pair.py',
    'tools/diagnostics/validate_tile_stream.py',
    'tools/diagnostics/validate_tile_compatibility.py',
    'tools/diagnostics/validate_paper_grid.py',
    'tools/examples/validate_game_update.py',
    'tools/diagnostics/validate_quest_rules.py',
)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',default='release-candidate');args=parser.parse_args()
    for script in SUITES:
        print('\nRunning',script,flush=True)
        subprocess.run([sys.executable,str(ROOT/script),'--build',args.build],cwd=ROOT,check=True)
    print('\nPASS all release suites; exact-image reports are ready for packaging.',flush=True)


if __name__=='__main__':main()
