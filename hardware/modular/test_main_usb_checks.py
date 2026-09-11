"""Run the USB fault-injection suite against the shaped main board."""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'kicad'))
spec = importlib.util.spec_from_file_location('shaped_usb_tests', HERE.parent / 'kicad/test_usb_layout_checks.py')
suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suite)


class MainUsbLayout(suite.UsbLayoutChecks):
    @classmethod
    def setUpClass(cls):
        cls.source = (HERE / 'main/Main.kicad_pcb').read_text(encoding='utf-8')
