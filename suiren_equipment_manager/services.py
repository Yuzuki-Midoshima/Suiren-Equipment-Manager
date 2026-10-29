"""Safe scene setup, switching, offset and visibility services."""

import json
from typing import Any, Dict, List

from .constants import (HAND_MAPPING_ATTRIBUTE, HAND_MAPPING_VERSION,
                        MANAGER_GROUP, NODE_PREFIX, OFFSET_ATTRIBUTE,
                        SPACE_ATTRIBUTE, SPACE_LABELS, WORLD_TARGET)
from .maya_utils import SceneError, incoming, resolve, resolve_plug, undo_chunk
from .rig_adapter import LEFT_HAND, RIGHT_HAND, WeaponSpec


class EquipmentService:
    def __init__(self, cmds: Any):
        self.cmds = cmds

    def validate(self, spec: WeaponSpec) -> None:
        for node in (spec.control, spec.driven, RIGHT_HAND, LEFT_HAND):
            resolve(self.cmds, node, context=spec.control)
        resolve_plug(self.cmds, spec.visibility_plug, context=spec.control)

    def setup(self, spec: WeaponSpec) -> str:
        self.validate(spec)
        control = resolve(self.cmds, spec.control)
        driven = resolve(self.cmds, spec.driven, context=control)
        constraint_name = "{}_{}_parentConstraint".format(NODE_PREFIX, spec.key)
        if self.cmds.objExists(constraint_name):
            self._migrate_hand_mapping(control)
            self._sync_hand_condition_mapping(spec, constraint_name)
            return constraint_name

        occupied = incoming(self.cmds, driven,
                            ("translate", "rotate", "tx", "ty", "tz", "rx", "ry", "rz"))
        if occupied:
            raise SceneError("既存接続と競合するため中断しました: {} <- {}".format(
                driven, ", ".join(sorted(set(occupied)))))

        with undo_chunk(self.cmds, "Suiren Equipment Setup"):
            if not self.cmds.objExists(MANAGER_GROUP):
                self.cmds.createNode("transform", name=MANAGER_GROUP)
                self.cmds.setAttr(MANAGER_GROUP + ".visibility", 0)
            if not self.cmds.objExists(WORLD_TARGET):
                self.cmds.createNode("transform", name=WORLD_TARGET,
                                     parent=MANAGER_GROUP)
            if not self.cmds.attributeQuery(SPACE_ATTRIBUTE, node=control, exists=True):
                self.cmds.addAttr(control, longName=SPACE_ATTRIBUTE,
                                  attributeType="enum",
                                  enumName=":".join(SPACE_LABELS), keyable=True)
            if not self.cmds.attributeQuery(OFFSET_ATTRIBUTE, node=control, exists=True):
                self.cmds.addAttr(control, longName=OFFSET_ATTRIBUTE,
                                  dataType="string", hidden=True)
                self.cmds.setAttr(control + "." + OFFSET_ATTRIBUTE, "{}", type="string")
            self._migrate_hand_mapping(control)

            targets = [resolve(self.cmds, RIGHT_HAND, control),
                       resolve(self.cmds, LEFT_HAND, control), WORLD_TARGET]
            constraint = self.cmds.parentConstraint(
                targets, driven, maintainOffset=True, name=constraint_name)[0]
            aliases = self.cmds.parentConstraint(constraint, query=True,
                                                 weightAliasList=True)
            for index, alias in enumerate(aliases):
                condition = self.cmds.createNode(
                    "condition", name="{}_{}_space{}_COND".format(
                        NODE_PREFIX, spec.key, index))
                self.cmds.setAttr(condition + ".operation", 0)
                self.cmds.setAttr(condition + ".secondTerm", index)
                self.cmds.setAttr(condition + ".colorIfTrueR", 1)
                self.cmds.setAttr(condition + ".colorIfFalseR", 0)
                self.cmds.connectAttr(control + "." + SPACE_ATTRIBUTE,
                                      condition + ".firstTerm", force=False)
                self.cmds.connectAttr(condition + ".outColorR",
                                      constraint + "." + alias, force=False)
            self._sync_hand_condition_mapping(spec, constraint)
        return constraint_name

    def _sync_hand_condition_mapping(
        self, spec: WeaponSpec, constraint: str
    ) -> None:
        """Make existing and new constraints follow corrected character sides."""
        targets = self.cmds.parentConstraint(
            constraint, query=True, targetList=True) or []
        for index, target in enumerate(targets):
            condition = "{}_{}_space{}_COND".format(
                NODE_PREFIX, spec.key, index)
            if not self.cmds.objExists(condition):
                continue
            leaf = target.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
            if leaf.endswith(RIGHT_HAND):
                enum_value = 0
            elif leaf.endswith(LEFT_HAND):
                enum_value = 1
            else:
                enum_value = 2
            self.cmds.setAttr(condition + ".secondTerm", enum_value)

    def _migrate_hand_mapping(self, control: str) -> None:
        """Swap legacy right/left saved grips once after hand-map correction."""
        if self.cmds.attributeQuery(
                HAND_MAPPING_ATTRIBUTE, node=control, exists=True):
            return
        raw = self.cmds.getAttr(
            control + "." + OFFSET_ATTRIBUTE) or "{}"
        try:
            data = json.loads(raw)
        except (TypeError, ValueError):
            data = {}
        right = data.pop("0", None)
        left = data.pop("1", None)
        if left is not None:
            data["0"] = left
        if right is not None:
            data["1"] = right
        self.cmds.setAttr(
            control + "." + OFFSET_ATTRIBUTE,
            json.dumps(data, separators=(",", ":")), type="string")
        self.cmds.addAttr(
            control, longName=HAND_MAPPING_ATTRIBUTE,
            attributeType="long", defaultValue=HAND_MAPPING_VERSION,
            hidden=True)
        self.cmds.setAttr(
            control + "." + HAND_MAPPING_ATTRIBUTE,
            HAND_MAPPING_VERSION)

    def current_space(self, spec: WeaponSpec) -> int:
        control = resolve(self.cmds, spec.control)
        if not self.cmds.attributeQuery(SPACE_ATTRIBUTE, node=control, exists=True):
            return 2
        return int(self.cmds.getAttr(control + "." + SPACE_ATTRIBUTE))

    def is_follow_enabled(self, spec: WeaponSpec) -> bool:
        constraint = "{}_{}_parentConstraint".format(NODE_PREFIX, spec.key)
        if not self.cmds.objExists(constraint):
            return False
        return int(self.cmds.getAttr(constraint + ".nodeState")) == 0

    def _evaluate_space_change(self, control: str, space: int) -> None:
        """Force hand/root parent-switch chains to settle before matching."""
        target = (RIGHT_HAND, LEFT_HAND, WORLD_TARGET)[space]
        resolved_target = resolve(self.cmds, target, context=control)
        # Reading both matrices forces Maya to evaluate the hand IK parent
        # switch (root/waist/spine) and the equipment constraint in order.
        self.cmds.getAttr(resolved_target + ".worldMatrix[0]")
        self.cmds.getAttr(control + ".worldMatrix[0]")

    def set_follow(self, spec: WeaponSpec, enabled: bool, key=False) -> None:
        constraint = self.setup(spec)
        control = resolve(self.cmds, spec.control)
        matrix = self.cmds.xform(control, query=True, worldSpace=True, matrix=True)
        with undo_chunk(self.cmds, "Suiren Equipment Follow"):
            self.cmds.setAttr(constraint + ".nodeState", 0 if enabled else 1)
            self.cmds.xform(control, worldSpace=True, matrix=matrix)
            if key:
                self.cmds.setKeyframe(constraint, attribute="nodeState",
                                      outTangentType="step")
                self.cmds.setKeyframe(control,
                                      attribute=("translate", "rotate"))

    def switch(self, spec: WeaponSpec, space: int, key=False) -> None:
        if space not in (0, 1, 2):
            raise ValueError("Invalid space: {}".format(space))
        self.setup(spec)
        control = resolve(self.cmds, spec.control)
        matrix = self.cmds.xform(control, query=True, worldSpace=True, matrix=True)
        with undo_chunk(self.cmds, "Suiren Equipment Switch"):
            constraint = "{}_{}_parentConstraint".format(NODE_PREFIX, spec.key)
            self.cmds.setAttr(constraint + ".nodeState", 0)
            self.cmds.setAttr(control + "." + SPACE_ATTRIBUTE, space)
            self._evaluate_space_change(control, space)
            self.cmds.xform(control, worldSpace=True, matrix=matrix)
            if key:
                self.cmds.setKeyframe(control, attribute=SPACE_ATTRIBUTE,
                                      outTangentType="step")
                self.cmds.setKeyframe(control, attribute=("translate", "rotate"))

    def switch_and_apply_saved_offset(
        self, spec: WeaponSpec, space: int
    ) -> bool:
        """Switch destination and apply its saved grip when one exists."""
        if space not in (0, 1, 2):
            raise ValueError("Invalid space: {}".format(space))
        self.setup(spec)
        control = resolve(self.cmds, spec.control)
        matrix = self.cmds.xform(
            control, query=True, worldSpace=True, matrix=True)
        values = self._offsets(control).get(str(space))
        constraint = "{}_{}_parentConstraint".format(
            NODE_PREFIX, spec.key)
        with undo_chunk(self.cmds, "Suiren Equipment Switch and Grip"):
            self.cmds.setAttr(constraint + ".nodeState", 0)
            self.cmds.setAttr(
                control + "." + SPACE_ATTRIBUTE, space)
            self._evaluate_space_change(control, space)
            self.cmds.xform(control, worldSpace=True, matrix=matrix)
            if values:
                self.cmds.setAttr(
                    control + ".translate", *values[:3], type="double3")
                self.cmds.setAttr(
                    control + ".rotate", *values[3:], type="double3")
        return bool(values)

    def key_equipment_state(
        self, spec: WeaponSpec, space: int, follow_enabled: bool
    ) -> None:
        """Record destination, follow state and pose as one animator action."""
        if space not in (0, 1, 2):
            raise ValueError("Invalid space: {}".format(space))
        constraint = self.setup(spec)
        control = resolve(self.cmds, spec.control)
        matrix = self.cmds.xform(control, query=True, worldSpace=True, matrix=True)
        with undo_chunk(self.cmds, "Suiren Equipment Key State"):
            self.cmds.setAttr(control + "." + SPACE_ATTRIBUTE, space)
            self.cmds.setAttr(
                constraint + ".nodeState", 0 if follow_enabled else 1)
            self._evaluate_space_change(control, space)
            self.cmds.xform(control, worldSpace=True, matrix=matrix)
            self.cmds.setKeyframe(
                control, attribute=SPACE_ATTRIBUTE, outTangentType="step")
            self.cmds.setKeyframe(
                constraint, attribute="nodeState", outTangentType="step")
            self.cmds.setKeyframe(
                control, attribute=("translate", "rotate"))

    def _offsets(self, control: str) -> Dict[str, List[float]]:
        raw = self.cmds.getAttr(control + "." + OFFSET_ATTRIBUTE) or "{}"
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return {}

    def has_saved_offset(self, spec: WeaponSpec, space: int) -> bool:
        """Return whether this destination has a stored grip pose."""
        control = resolve(self.cmds, spec.control)
        if not self.cmds.attributeQuery(
                OFFSET_ATTRIBUTE, node=control, exists=True):
            return False
        return str(space) in self._offsets(control)

    def save_offset(self, spec: WeaponSpec) -> List[float]:
        self.setup(spec)
        control = resolve(self.cmds, spec.control)
        values = list(self.cmds.getAttr(control + ".translate")[0])
        values += list(self.cmds.getAttr(control + ".rotate")[0])
        data = self._offsets(control)
        data[str(self.current_space(spec))] = values
        self.cmds.setAttr(control + "." + OFFSET_ATTRIBUTE,
                          json.dumps(data, separators=(",", ":")), type="string")
        return values

    def set_offset_values(self, spec: WeaponSpec, values: List[float]) -> None:
        """Apply editable local grip values to the selected weapon control."""
        if len(values) != 6:
            raise ValueError("Offset values must contain Translate XYZ and Rotate XYZ")
        self.setup(spec)
        control = resolve(self.cmds, spec.control)
        with undo_chunk(self.cmds, "Suiren Equipment Edit Grip"):
            self.cmds.setAttr(control + ".translate", *values[:3], type="double3")
            self.cmds.setAttr(control + ".rotate", *values[3:], type="double3")

    def restore_offset(self, spec: WeaponSpec) -> List[float]:
        self.setup(spec)
        control = resolve(self.cmds, spec.control)
        values = self._offsets(control).get(str(self.current_space(spec)))
        if not values:
            raise SceneError("この装備先には保存済みオフセットがありません")
        with undo_chunk(self.cmds, "Suiren Equipment Restore Offset"):
            self.cmds.setAttr(control + ".translate", *values[:3], type="double3")
            self.cmds.setAttr(control + ".rotate", *values[3:], type="double3")
        return values

    def set_visibility(self, spec: WeaponSpec, visible: bool) -> None:
        plug = resolve_plug(self.cmds, spec.visibility_plug,
                            context=spec.control)
        self.cmds.setAttr(plug, bool(visible))

    def reset_settings(self, spec: WeaponSpec) -> None:
        """Reset only tool-managed state for one weapon; preserve keyframes."""
        constraint = self.setup(spec)
        control = resolve(self.cmds, spec.control)
        visibility = resolve_plug(
            self.cmds, spec.visibility_plug, context=control)
        with undo_chunk(self.cmds, "Suiren Equipment Reset Settings"):
            # Disable evaluation first, then return the editable grip to zero.
            self.cmds.setAttr(constraint + ".nodeState", 1)
            self.cmds.setAttr(control + "." + SPACE_ATTRIBUTE, 2)
            self.cmds.setAttr(
                control + ".translate", 0.0, 0.0, 0.0, type="double3")
            self.cmds.setAttr(
                control + ".rotate", 0.0, 0.0, 0.0, type="double3")
            self.cmds.setAttr(
                control + "." + OFFSET_ATTRIBUTE, "{}", type="string")
            self.cmds.setAttr(visibility, False)

