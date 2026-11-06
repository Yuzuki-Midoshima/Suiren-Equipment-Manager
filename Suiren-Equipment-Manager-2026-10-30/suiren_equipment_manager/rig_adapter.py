"""All Suiren-specific scene knowledge lives here."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class WeaponSpec:
    key: str
    label: str
    control: str
    driven: str
    meshes: Tuple[str, ...]
    visibility_plug: str


# The .ma shows three independently rigged swords. Sword B's second mesh is a
# rig display/dummy and therefore belongs to the same weapon entry.
WEAPONS = (
    WeaponSpec("sword_a", "剣 01", "Rig_C_SwordARoot",
               "Rig_C_SwordARoot_parent_target", ("Geo_C_Sword_001",),
               "Rig_Other.sword_A"),
    WeaponSpec("sword_b", "剣 02", "Rig_C_SwordBRoot_001",
               "Rig_C_SwordBRoot_001_parent_target",
               ("Geo_C_Sword_002", "Geo_C_Sword_002_002"),
               "Rig_Other.sword_B"),
    WeaponSpec("sheath", "鞘", "Rig_C_SwordBSaya_001",
               "Rig_C_SwordBSaya_001_parent_target", ("Geo_C_Sheath",),
               "Rig_Other.sword_B"),
    WeaponSpec("sword_a02", "剣 03", "Rig_C_SwordARoot_02",
               "Rig_C_SwordARoot_02_parent_target", ("Geo_C_Sword_003",),
               "Rig_Other.sword_A_02"),
    WeaponSpec("spear", "槍", "Rig_C_Spear_001",
               "Rig_C_Spear_001_parent_target",
               ("Geo_C_Spear", "Geo_C_Spear_ghost"),
               "Rig_Other.spear"),
    WeaponSpec("stick", "棒", "Rig_C_Stick_001",
               "Rig_C_Stick_001_parent_target", ("Geo_C_Stick",),
               "Rig_Other.stick"),
)

# In this delivered Suiren rig the artist-facing character sides are opposite
# the joint-name letters.  Keep UI semantics anatomical: キャラ右 / キャラ左.
RIGHT_HAND = "Jnt_L_Hand"
LEFT_HAND = "Jnt_R_Hand"


def by_key(key: str) -> Optional[WeaponSpec]:
    return next((item for item in WEAPONS if item.key == key), None)

