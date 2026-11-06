"""UI-independent application controller."""

from typing import Any

from .constants import SPACE_LABELS
from .maya_utils import SceneError
from .rig_adapter import WEAPONS, by_key


class EquipmentController:
    def __init__(self, cmds: Any, service: Any):
        self.cmds, self.service, self.ui = cmds, service, None
        self._switching = False

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
        status = SPACE_LABELS[space].split()[0].upper()
        self._switching = True
        try:
            return self._switch(key, space, keyframe, status)
        finally:
            self._switching = False

    def _switch(self, key, space, keyframe, status):
        if keyframe:
            return self.run(
                lambda: self.service.switch(self.spec(key), space, True),
                status)

        def operation():
            applied = self.service.switch_and_apply_saved_offset(
                self.spec(key), space)
            message = status
            if applied:
                message += " / 保存済み握り位置を適用"
            self._show_message(message)
        return self.run(operation)

    def channel_space_changed(self, key):
        """Apply a saved grip after a manual Channel Box space change."""
        if self._switching:
            return None

        def operation():
            spec = self.spec(key)
            space = self.service.current_space(spec)
            applied = self.service.apply_current_saved_offset(spec)
            status = SPACE_LABELS[space].split()[0].upper()
            if applied:
                status += " / SAVED GRIP"
            self._show_message(status)
            return applied

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

