"""Drag this file into Maya's viewport to register the shelf button."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def onMayaDroppedPythonFile(*_args):
    root = Path(__file__).resolve().parent
    installer = root / "register_shelf.py"
    spec = spec_from_file_location("suiren_equipment_manager_shelf", installer)
    if spec is None or spec.loader is None:
        raise RuntimeError("登録スクリプトを読み込めません: {}".format(installer))
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.register()
