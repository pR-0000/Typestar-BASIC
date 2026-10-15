"""Start Typestar BASIC Studio; implementation files live in internal/."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'internal'))
from bootstrap import launch
if __name__=='__main__':launch(HERE)
