import unittest

from suiren_equipment_manager.maya_utils import resolve, resolve_plug


class PrefixedCmds:
    nodes = {
        "ab_rig_B_Rig_C_SwordARoot",
        "ab_rig_B_Rig_Other",
    }

    def ls(self, pattern, long=False):
        if pattern in self.nodes:
            return ["|root|" + pattern] if long else [pattern]
        if pattern.startswith("*_"):
            suffix = pattern[2:]
            result = [item for item in self.nodes if item.endswith("_" + suffix)]
            return ["|root|" + item for item in result] if long else result
        return []

    def objExists(self, name):
        return name == "|root|ab_rig_B_Rig_Other.sword_A"


class MayaUtilsTests(unittest.TestCase):
    def test_import_prefix_is_resolved(self):
        self.assertEqual(
            resolve(PrefixedCmds(), "Rig_C_SwordARoot"),
            "|root|ab_rig_B_Rig_C_SwordARoot",
        )

    def test_attribute_owner_uses_same_prefix_resolution(self):
        self.assertEqual(
            resolve_plug(PrefixedCmds(), "Rig_Other.sword_A"),
            "|root|ab_rig_B_Rig_Other.sword_A",
        )


if __name__ == "__main__":
    unittest.main()
