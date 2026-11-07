from pathlib import Path
import sys

pytest_plugins = ["test_pilot_collector"]

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))
