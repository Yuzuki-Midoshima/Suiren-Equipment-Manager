"""Manual/headless Maya 2026 smoke test; never saves the source scene."""

from pathlib import Path

import maya.standalone

maya.standalone.initialize(name="python")

from maya import cmds
from suiren_equipment_manager.rig_adapter import WEAPONS
from suiren_equipment_manager.services import EquipmentService


scene = Path(__file__).parents[1] / "ab_rig_B" / "rig" / "ab_rig_B.ma"
if not scene.exists():
    print("MAYA_SMOKE_SKIPPED: place the Suiren test rig at {}".format(scene))
    maya.standalone.uninitialize()
    raise SystemExit(0)
cmds.file(str(scene), open=True, force=True, prompt=False,
          ignoreVersion=True, executeScriptNodes=False)
service = EquipmentService(cmds)

before = set(cmds.ls("SEM_*"))
for weapon in WEAPONS:
    service.setup(weapon)
    initial = cmds.xform(weapon.control, query=True, worldSpace=True, matrix=True)
    for space in (0, 1, 2):
        service.switch(weapon, space, key=False)
        current = cmds.xform(weapon.control, query=True, worldSpace=True, matrix=True)
        assert all(abs(a - b) < 1e-5 for a, b in zip(initial, current)), weapon.key
    service.save_offset(weapon)
    service.restore_offset(weapon)

first_setup = set(cmds.ls("SEM_*"))
for weapon in WEAPONS:
    service.setup(weapon)
assert set(cmds.ls("SEM_*")) == first_setup, "setup created duplicate nodes"
assert len(first_setup - before) == 26, sorted(first_setup - before)

print("MAYA_SMOKE_OK weapons=6 sem_nodes={}".format(len(first_setup)))
cmds.file(new=True, force=True)
maya.standalone.uninitialize()
