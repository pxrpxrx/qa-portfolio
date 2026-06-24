import pytest
import sys
from pathlib import Path

_src_root = (Path(__file__).parent.parent / "src").resolve()
_src_str = str(_src_root)
if _src_str not in sys.path:
    sys.path.insert(0, _src_str)
