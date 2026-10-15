"""Shared CPU adapter required by firmware assembly helpers."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'studio/internal'))
from hd6301 import CPUBase as CPU
