"""Make backend modules importable from tests regardless of invocation dir."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
