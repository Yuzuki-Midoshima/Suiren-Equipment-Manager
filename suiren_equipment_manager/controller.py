"""UI-independent application controller."""

from typing import Any

from .constants import SPACE_LABELS
from .maya_utils import SceneError
from .rig_adapter import WEAPONS, by_key


class EquipmentController:
    def __init__(self, cmds: Any, service: Any):
        self.cmds, self.service, self.ui = cmds, service, None

    def attach(self, ui: Any) -> None:
        self.ui = ui

    def spec(self, key: str):
        value = by_key(key)
        if value is None:
            raise ValueError("Unknown weapon: {}".format(key))
        return value

    def run(self, operation, success=""):
        try:
            result = operation()
            if success:
                self.cmds.inViewMessage(amg="<hl>{}</hl>".format(success),
                                        pos="midCenter", fade=True)
            self.refresh()
            return result
        except (SceneError, RuntimeError, ValueError) as exc:
            self.cmds.warning("Suiren Equipment Manager: {}".format(exc))
            if self.ui:
                self.ui.set_status("エラー: {}".format(exc))
            return None

    def setup_selected(self, key):
        """Set up only the weapon currently shown in the UI."""
        spec = self.spec(key)
        return self.run(lambda: self.service.setup(spec),
                        "{} をセットアップしました".format(spec.label))

    def switch(self, key, space, keyframe=False):
        if keyframe:
            return self.run(
                lambda: self.service.switch(self.spec(key), space, True),
                "{} に切替".format(SPACE_LABELS[space]))

        def operation():
            applied = self.service.switch_and_apply_saved_offset(
                self.spec(key), space)
            message = "{} に切替".format(SPACE_LABELS[space])
            if applied:
                message += " / 保存済み握り位置を適用"
            self._show_message(message)
        return self.run(operation)

    def _show_message(self, message):
        self.cmds.inViewMessage(
            amg="<hl>{}</hl>".format(message),
            pos="midCenter", fade=True)

    def save(self, key):
        return self.run(lambda: self.service.save_offset(self.spec(key)),
                        "オフセットを保存しました")

    def restore(self, key):
        return self.run(lambda: self.service.restore_offset(self.spec(key)),
                        "オフセットを復元しました")

    def edit_offset(self, key, values):
        return self.run(
            lambda: self.service.set_offset_values(self.spec(key), values))

    def visible(self, key, value, allow_multiple=False):
        def operation():
            spec = self.spec(key)
            if value and not allow_multiple:
                for other in WEAPONS:
                    if other.key != spec.key:
                        try:
                            self.service.set_visibility(other, False)
                        except SceneError:
                            # Optional/missing equipment in a scene is ignored.
                            pass
            self.service.set_visibility(spec, value)
        return self.run(operation)

    def follow(self, key, value, keyframe=False):
        label = "追従 ON" if value else "追従 OFF"
        return self.run(
            lambda: self.service.set_follow(self.spec(key), value, keyframe),
            label)

    def key_state(self, key, space, follow_enabled):
        return self.run(
            lambda: self.service.key_equipment_state(
                self.spec(key), space, follow_enabled),
            "装備状態をキーフレーム登録しました")

    def reset_settings(self, key):
        spec = self.spec(key)
        return self.run(
            lambda: self.service.reset_settings(spec),
            "{} を初期状態へ戻しました".format(spec.label))

    def refresh(self):
        if self.ui:
            self.ui.render()

