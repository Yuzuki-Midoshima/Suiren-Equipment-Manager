import unittest

from suiren_equipment_manager.rig_adapter import WEAPONS, by_key


class RigAdapterTests(unittest.TestCase):
    def test_all_rigged_weapons_are_registered(self):
        self.assertEqual([item.label for item in WEAPONS],
                         ["剣 01", "剣 02", "鞘", "剣 03", "槍", "棒"])

    def test_every_weapon_has_distinct_control_and_driven_node(self):
        self.assertEqual(len({item.control for item in WEAPONS}), 6)
        self.assertEqual(len({item.driven for item in WEAPONS}), 6)
        self.assertTrue(all(item.control != item.driven for item in WEAPONS))

    def test_sword_b_dummy_is_not_a_separate_weapon(self):
        sword_b = by_key("sword_b")
        self.assertIn("Geo_C_Sword_002_002", sword_b.meshes)
        self.assertEqual(len([item for item in WEAPONS
                              if item.key.startswith("sword")]), 3)

    def test_spear_and_stick_use_existing_rig_roots(self):
        spear = by_key("spear")
        stick = by_key("stick")
        self.assertEqual(spear.control, "Rig_C_Spear_001")
        self.assertEqual(spear.driven, "Rig_C_Spear_001_parent_target")
        self.assertEqual(stick.control, "Rig_C_Stick_001")
        self.assertEqual(stick.driven, "Rig_C_Stick_001_parent_target")

    def test_sheath_has_independent_transform_rig(self):
        sheath = by_key("sheath")
        sword_b = by_key("sword_b")
        self.assertEqual(sheath.control, "Rig_C_SwordBSaya_001")
        self.assertEqual(
            sheath.driven, "Rig_C_SwordBSaya_001_parent_target")
        self.assertNotEqual(sheath.control, sword_b.control)
        self.assertEqual(sheath.visibility_plug, sword_b.visibility_plug)

    def test_visibility_uses_existing_rig_attributes(self):
        self.assertTrue(all(item.visibility_plug.startswith("Rig_Other.")
                            for item in WEAPONS))


if __name__ == "__main__":
    unittest.main()

