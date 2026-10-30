import unittest

from suiren_equipment_manager.controller import EquipmentController
from suiren_equipment_manager.rig_adapter import WEAPONS
from suiren_equipment_manager.services import EquipmentService


class FakeCmds:
    def __init__(self):
        self.calls = []

    def ls(self, name, long=False):
        return [name]

    def xform(self, node, **kwargs):
        self.calls.append(("xform", node, kwargs))
        if kwargs.get("query"):
            return list(range(16))

    def setAttr(self, plug, *values, **kwargs):
        self.calls.append(("setAttr", plug, values, kwargs))

    def undoInfo(self, **kwargs):
        pass


class TestService(EquipmentService):
    __test__ = False

    def __init__(self, cmds, saved):
        super().__init__(cmds)
        self.saved = saved

    def setup(self, spec):
        return "SEM_{}_parentConstraint".format(spec.key)

    def _offsets(self, control):
        return self.saved

    def _evaluate_space_change(self, control, space):
        self.cmds.calls.append(("evaluate", control, space))


class SwitchingTests(unittest.TestCase):
    def test_manual_channel_change_applies_current_saved_grip(self):
        class ChannelCmds(FakeCmds):
            def getAttr(self, plug):
                return 1

        cmds = ChannelCmds()
        values = [1.0, 2.0, 3.0, 10.0, 20.0, 30.0]
        service = TestService(cmds, {"1": values})

        self.assertTrue(service.apply_current_saved_offset(WEAPONS[0]))
        self.assertIn(
            ("setAttr", WEAPONS[0].control + ".translate",
             tuple(values[:3]), {"type": "double3"}),
            cmds.calls,
        )
        self.assertIn(
            ("setAttr", WEAPONS[0].control + ".rotate",
             tuple(values[3:]), {"type": "double3"}),
            cmds.calls,
        )

    def test_saved_grip_skips_world_matrix_write(self):
        cmds = FakeCmds()
        values = [1.0, 2.0, 3.0, 10.0, 20.0, 30.0]
        service = TestService(cmds, {"1": values})

        self.assertTrue(service.switch_and_apply_saved_offset(WEAPONS[0], 1))

        xforms = [call for call in cmds.calls if call[0] == "xform"]
        self.assertEqual(len(xforms), 1)
        self.assertTrue(xforms[0][2]["query"])
        self.assertIn(
            ("setAttr", WEAPONS[0].control + ".translate",
             tuple(values[:3]), {"type": "double3"}),
            cmds.calls,
        )
        self.assertIn(
            ("setAttr", WEAPONS[0].control + ".rotate",
             tuple(values[3:]), {"type": "double3"}),
            cmds.calls,
        )

    def test_missing_grip_still_preserves_world_matrix(self):
        cmds = FakeCmds()
        service = TestService(cmds, {})

        self.assertFalse(service.switch_and_apply_saved_offset(WEAPONS[0], 2))

        xforms = [call for call in cmds.calls if call[0] == "xform"]
        self.assertEqual(len(xforms), 2)
        self.assertTrue(xforms[0][2]["query"])
        self.assertEqual(xforms[1][2]["matrix"], list(range(16)))

    def test_ui_switch_announces_uppercase_destination(self):
        class StatusCmds:
            def __init__(self):
                self.messages = []

            def inViewMessage(self, **kwargs):
                self.messages.append(kwargs["amg"])

        class StatusService:
            def switch_and_apply_saved_offset(self, spec, space):
                return False

        cmds = StatusCmds()
        controller = EquipmentController(cmds, StatusService())

        controller.switch("sword_a", 1)

        self.assertEqual(cmds.messages, ["<hl>LEFT</hl>"])


if __name__ == "__main__":
    unittest.main()
