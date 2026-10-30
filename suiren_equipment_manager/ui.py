"""Compact, status-first PySide6 interface for Maya 2026."""

from .constants import APP_NAME, SPACE_ATTRIBUTE, SPACE_JA, WINDOW_OBJECT
from .maya_utils import resolve, resolve_plug
from .rig_adapter import WEAPONS


def _maya_main_window():
    from maya import OpenMayaUI
    from shiboken6 import wrapInstance
    from PySide6 import QtWidgets
    pointer = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget) if pointer else None


class EquipmentManagerUI:
    def __init__(self, controller):
        from PySide6 import QtCore, QtWidgets
        self.QtWidgets = QtWidgets
        self.controller = controller
        controller.attach(self)
        self.window = QtWidgets.QDialog(_maya_main_window())
        self.window.setObjectName(WINDOW_OBJECT)
        self.window.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.window.setWindowTitle(APP_NAME)
        self.window.setMinimumWidth(240)
        self.window.setSizeGripEnabled(True)
        self.window.setStyleSheet("""
            QDialog { background:#292c31; color:#e8eaed; }
            QLabel#title { font-size:16px; font-weight:700; color:#8ecbff; padding:7px; }
            QGroupBox { border:1px solid #4a5059; border-radius:5px; margin-top:12px;
                        padding:12px 8px 8px; font-weight:600; }
            QGroupBox::title { subcontrol-origin:margin; left:10px; padding:0 5px; color:#b9dfff; }
            QComboBox,QDoubleSpinBox { min-height:26px; background:#363a41;
                                      border:1px solid #555c66; border-radius:3px; padding:2px 6px; }
            QPushButton { min-height:31px; background:#444a53; border:1px solid #5b636e;
                          border-radius:4px; padding:3px 10px; }
            QPushButton:hover { background:#525a65; }
            QPushButton#primary { background:#286a9b; border-color:#4296d2; font-weight:700; }
            QPushButton#keyButton { background:#785629; border-color:#b7863e; }
            QLabel#hint { color:#aeb5be; font-size:11px; padding:1px 3px 6px; }
            QLabel#detail { background:#202328; border:1px solid #47515c; border-radius:4px;
                            padding:7px; color:#b9c3cf; }
        """)
        root = QtWidgets.QVBoxLayout(self.window); root.setSpacing(7)
        self.root_layout = root
        title = QtWidgets.QLabel("SUIREN EQUIPMENT MANAGER")
        title.setObjectName("title"); title.setAlignment(QtCore.Qt.AlignCenter); root.addWidget(title)
        self.title_label = title
        self.compact_toggle = QtWidgets.QCheckBox("コンパクト表示")
        self.compact_toggle.setToolTip("アニメーション中に不要な編集項目と説明を畳みます")
        root.addWidget(self.compact_toggle, 0, QtCore.Qt.AlignRight)

        weapon_box = QtWidgets.QGroupBox("武器と装備先")
        self.weapon_box = weapon_box
        weapon_layout = QtWidgets.QVBoxLayout(weapon_box)
        self.weapon_layout = weapon_layout
        weapon_label = QtWidgets.QLabel("操作する武器（この1つだけを変更）")
        self.weapon_label = weapon_label
        weapon_label.setStyleSheet("font-weight:700; color:#d7e9f8; padding:2px;")
        weapon_layout.addWidget(weapon_label)
        self.weapon = QtWidgets.QComboBox()
        self.weapon.setSizePolicy(
            QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        for spec in WEAPONS: self.weapon.addItem(spec.label, spec.key)
        weapon_layout.addWidget(self.weapon)

        # Prominent, always-visible state indicators.
        badges = QtWidgets.QHBoxLayout()
        self.badges_layout = badges
        self.space_badge = self._badge(QtCore, QtWidgets, "この武器の装備先：－")
        self.space_badge.setToolTip("現在の装備先です")
        self.space_badge.setAttribute(
            QtCore.Qt.WA_TransparentForMouseEvents)
        self.follow_badge = self._state_button(QtWidgets, "追従 －")
        self.follow_badge.setToolTip("クリックでコンストレイント追従をON/OFF")
        self.visible_badge = self._state_button(QtWidgets, "表示 －")
        self.visible_badge.setToolTip("クリックで武器を表示/非表示")
        for badge in (self.space_badge, self.follow_badge, self.visible_badge): badges.addWidget(badge)
        weapon_layout.addLayout(badges)
        self.visible_summary = QtWidgets.QLabel("シーン全体で表示中：確認中…")
        self.visible_summary.setObjectName("detail")
        weapon_layout.addWidget(self.visible_summary)
        self.multi_mode = QtWidgets.QCheckBox("複数武器を同時表示")
        self.multi_mode.setToolTip(
            "OFFでは選択中の武器を表示すると、ほかの武器を自動で非表示にします")
        weapon_layout.addWidget(self.multi_mode)

        space_row = QtWidgets.QHBoxLayout(); self.spaces = []
        self.offset_save_labels = []
        self.space_group = QtWidgets.QButtonGroup(self.window)
        self.space_group.setExclusive(True)
        destination_labels = ("右手へ", "左手へ", "Worldへ")
        for index, label in enumerate(destination_labels):
            column = QtWidgets.QVBoxLayout()
            column.setSpacing(1)
            button = QtWidgets.QRadioButton(label)
            self.space_group.addButton(button, index)
            button.clicked.connect(
                lambda _checked=False, target=index:
                self._destination_clicked(target))
            status = QtWidgets.QLabel("未保存")
            status.setAlignment(QtCore.Qt.AlignCenter)
            status.setStyleSheet(
                "color:#b87872; font-size:10px; padding:1px;")
            column.addWidget(button, 0, QtCore.Qt.AlignCenter)
            column.addWidget(status)
            self.spaces.append(button)
            self.offset_save_labels.append(status)
            space_row.addLayout(column, 1)
        self.spaces[2].setChecked(True); weapon_layout.addLayout(space_row)
        root.addWidget(weapon_box)

        offset_box = QtWidgets.QGroupBox("握り位置の微調整")
        self.offset_box = offset_box
        offset_layout = QtWidgets.QVBoxLayout(offset_box); self.fields = []
        self.offset_destination = QtWidgets.QLabel("編集中・保存先：World")
        self.offset_destination.setStyleSheet(
            "background:#234d68; color:white; border-radius:4px;"
            "font-weight:700; padding:6px;")
        offset_layout.addWidget(self.offset_destination)
        offset_hint = QtWidgets.QLabel(
            "武器コントローラーのローカル軸です。数値変更は武器へ即時反映されます。")
        offset_hint.setObjectName("hint"); offset_layout.addWidget(offset_hint)
        for group_name in ("位置 (cm)", "回転 (度)"):
            row = QtWidgets.QHBoxLayout(); row.addWidget(QtWidgets.QLabel(group_name), 1)
            for axis in "XYZ":
                row.addWidget(QtWidgets.QLabel(axis))
                field = QtWidgets.QDoubleSpinBox(); field.setRange(-100000, 100000); field.setDecimals(4)
                self.fields.append(field); row.addWidget(field, 2)
            offset_layout.addLayout(row)
        offset_actions = QtWidgets.QHBoxLayout()
        save = QtWidgets.QPushButton("この握り位置を保存")
        save.setToolTip("現在の装備先専用の握り位置としてシーンに保存します")
        offset_actions.addWidget(save); offset_layout.addLayout(offset_actions)
        root.addWidget(offset_box)

        action_box = QtWidgets.QGroupBox("切替操作")
        self.action_box = action_box
        action_layout = QtWidgets.QVBoxLayout(action_box)
        self.action_layout = action_layout
        self.action_hints = []
        action_columns = QtWidgets.QHBoxLayout()
        action_columns.setSpacing(7)
        self.action_buttons_layout = action_columns

        switch_column = QtWidgets.QVBoxLayout()
        switch_column.setSpacing(2)
        switch = QtWidgets.QPushButton("装備先を切替"); switch.setObjectName("primary")
        self.switch_button = switch
        switch.setToolTip("切替先に保存済みの握り位置があれば自動で適用します")
        switch_column.addWidget(switch)
        hint = QtWidgets.QLabel(
            "保存済みの握り位置を自動適用します。未保存なら現在位置を維持します。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        switch_column.addWidget(hint)
        self.action_hints.append(hint)

        key_column = QtWidgets.QVBoxLayout()
        key_column.setSpacing(2)
        key = QtWidgets.QPushButton("現在の装備状態をキーフレーム登録"); key.setObjectName("keyButton")
        self.key_button = key
        key.setToolTip("装備先・追従状態・位置・回転をまとめて現在フレームに記録します")
        key_column.addWidget(key)
        hint = QtWidgets.QLabel("選択した装備先、追従ON/OFF、位置・回転をまとめて記録します。")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        key_column.addWidget(hint)
        self.action_hints.append(hint)

        compact_save = QtWidgets.QPushButton("握り保存")
        self.compact_save_button = compact_save
        compact_save.setToolTip(
            "現在の位置・回転を、現在の装備先用の握り位置として保存します")
        compact_save.setVisible(False)

        action_columns.addLayout(switch_column, 1)
        action_columns.addWidget(compact_save, 1, QtCore.Qt.AlignTop)
        action_columns.addLayout(key_column, 1)
        action_layout.addLayout(action_columns)
        root.addWidget(action_box)
        self.detail = QtWidgets.QLabel("準備状態を確認中…"); self.detail.setObjectName("detail")
        root.addWidget(self.detail)
        reset = QtWidgets.QPushButton("この武器を初期状態へリセット")
        self.reset_button = reset
        reset.setToolTip("選択中の武器だけをWorld・追従OFF・表示OFF・握り位置0へ戻します")
        reset.setMaximumHeight(24)
        reset.setStyleSheet(
            "QPushButton { color:#c6c9ce; background:#34383e; border:1px solid #555b63;"
            " border-radius:3px; font-size:10px; padding:1px 6px; }"
            "QPushButton:hover { color:white; background:#763d3d; }")
        root.addWidget(reset, 0, QtCore.Qt.AlignRight)

        save.clicked.connect(lambda: controller.save(self.key()))
        compact_save.clicked.connect(lambda: controller.save(self.key()))
        switch.clicked.connect(self._switch_selected_destination)
        key.clicked.connect(lambda: controller.key_state(
            self.key(), self.space(), self.follow_badge.isChecked()))
        self.follow_badge.clicked.connect(lambda value: controller.follow(self.key(), value))
        self.visible_badge.clicked.connect(lambda value: controller.visible(
            self.key(), value, self.multi_mode.isChecked()))
        self.weapon.currentIndexChanged.connect(lambda _i: controller.refresh())
        self.compact_toggle.toggled.connect(self._set_compact)
        reset.clicked.connect(self._confirm_reset)
        for field in self.fields:
            field.editingFinished.connect(self._apply_offset_fields)
        for widget in (
                self.space_badge, self.follow_badge, self.visible_badge,
                self.switch_button, self.compact_save_button,
                self.key_button, self.reset_button):
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        self.window.resize(400, self.window.sizeHint().height())
        self._channel_spaces = {}
        self._channel_time = controller.service.cmds.currentTime(query=True)
        self._sync_channel_cache()
        self._channel_timer = QtCore.QTimer(self.window)
        self._channel_timer.setInterval(150)
        self._channel_timer.timeout.connect(self._poll_channel_spaces)
        self._channel_timer.start()

    def _sync_channel_cache(self):
        cmds = self.controller.service.cmds
        for spec in WEAPONS:
            try:
                control = resolve(cmds, spec.control)
                plug = control + "." + SPACE_ATTRIBUTE
                if cmds.objExists(plug):
                    self._channel_spaces[spec.key] = int(cmds.getAttr(plug))
            except (RuntimeError, ValueError):
                continue

    def _poll_channel_spaces(self):
        """Fallback for Maya scenes where attributeChange jobs do not fire."""
        cmds = self.controller.service.cmds
        current_time = cmds.currentTime(query=True)
        if cmds.play(query=True, state=True) or current_time != self._channel_time:
            self._channel_time = current_time
            self._sync_channel_cache()
            return

        for spec in WEAPONS:
            try:
                control = resolve(cmds, spec.control)
                plug = control + "." + SPACE_ATTRIBUTE
                if not cmds.objExists(plug):
                    continue
                space = int(cmds.getAttr(plug))
                previous = self._channel_spaces.get(spec.key, space)
                self._channel_spaces[spec.key] = space
                if space != previous and not self.controller._switching:
                    self.controller.channel_space_changed(spec.key)
            except (RuntimeError, ValueError):
                continue

    @staticmethod
    def _badge(QtCore, QtWidgets, text):
        button = QtWidgets.QPushButton(text)
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setMinimumHeight(34)
        return button

    @staticmethod
    def _state_button(QtWidgets, text):
        button = QtWidgets.QPushButton(text)
        button.setCheckable(True); button.setMinimumHeight(34)
        return button

    @staticmethod
    def _badge_style(color):
        return (
            "min-height:34px; max-height:34px; padding:0px 5px;"
            "background:{}; color:white; border-radius:5px; font-weight:700;"
        ).format(color)

    def key(self): return self.weapon.currentData()
    def space(self):
        checked = self.space_group.checkedId()
        return checked if checked in (0, 1, 2) else 2
    def _switch_selected_destination(self, _checked=False):
        self.controller.switch(self.key(), self.space())
    def _apply_offset_fields(self):
        self.controller.edit_offset(
            self.key(), [field.value() for field in self.fields])
    def _destination_clicked(self, target):
        self.controller.switch(self.key(), target)
    def _set_compact(self, compact):
        self.offset_box.setVisible(not compact)
        self.title_label.setVisible(not compact)
        self.visible_summary.setVisible(not compact)
        self.multi_mode.setVisible(not compact)
        self.detail.setVisible(not compact)
        self.weapon_label.setVisible(not compact)
        for hint in self.action_hints:
            hint.setVisible(not compact)
        margin = 2 if compact else 9
        spacing = 2 if compact else 7
        self.root_layout.setContentsMargins(margin, margin, margin, margin)
        self.root_layout.setSpacing(spacing)
        for layout in (self.weapon_layout, self.action_layout):
            layout.setContentsMargins(
                3 if compact else 7,
                2 if compact else 12,
                3 if compact else 7,
                2 if compact else 7)
            layout.setSpacing(2 if compact else 6)
        self.compact_toggle.setText("コンパクト" if compact else "コンパクト表示")
        self.compact_toggle.setMaximumHeight(18 if compact else 16777215)
        self.weapon.setFixedHeight(24 if compact else 30)
        self.reset_button.setMaximumHeight(20 if compact else 24)
        self.weapon_box.setTitle("" if compact else "武器と装備先")
        self.action_box.setTitle("" if compact else "切替操作")
        self.weapon_box.setFlat(compact)
        self.action_box.setFlat(compact)
        compact_group_style = (
            "QGroupBox { border:1px solid #4a5059; border-radius:5px;"
            " margin:0px; padding:0px; }"
            if compact else "")
        self.weapon_box.setStyleSheet(compact_group_style)
        self.action_box.setStyleSheet(compact_group_style)
        self.switch_button.setVisible(not compact)
        self.action_buttons_layout.setStretch(0, 0 if compact else 1)
        self.key_button.setText("キー登録" if compact else "現在の装備状態をキーフレーム登録")
        self.compact_save_button.setVisible(compact)
        self.reset_button.setText("設定をリセット" if compact else "この武器を初期状態へリセット")
        button_height = 34
        for badge in (self.space_badge, self.follow_badge, self.visible_badge):
            badge.setMinimumHeight(button_height)
            badge.setMaximumHeight(44)
        for button in (
                self.switch_button, self.compact_save_button,
                self.key_button):
            button.setMinimumHeight(31)
            button.setMaximumHeight(40)
        self.window.setMinimumHeight(0)
        self.render()
        target_width = min(self.window.width(), 270) if compact else self.window.width()
        self.window.resize(max(240, target_width), self.window.sizeHint().height())
    def _confirm_reset(self):
        result = self.QtWidgets.QMessageBox.question(
            self.window,
            "装備設定をリセット",
            "選択中の武器だけを初期状態へ戻します。\n\n"
            "・装備先：World\n・追従：OFF\n・表示：OFF\n"
            "・握り位置：0\n・保存済み握り位置：消去\n\n"
            "既存のアニメーションキーは削除しません。",
            self.QtWidgets.QMessageBox.Yes | self.QtWidgets.QMessageBox.No,
            self.QtWidgets.QMessageBox.No)
        if result == self.QtWidgets.QMessageBox.Yes:
            self.controller.reset_settings(self.key())
    def set_status(self, text): self.detail.setText(text.removeprefix("状態："))

    def render(self):
        spec = self.controller.spec(self.key()); cmds = self.controller.service.cmds
        try:
            index = self.controller.service.current_space(spec)
            self.spaces[index].setChecked(True)
            control = resolve(cmds, spec.control)
            setup_done = cmds.attributeQuery(
                "semEquipmentSpace", node=control, exists=True)
            values = list(cmds.getAttr(control + ".translate")[0]) + list(cmds.getAttr(control + ".rotate")[0])
            for field, value in zip(self.fields, values): field.setValue(value)
            follow = self.controller.service.is_follow_enabled(spec)
            self.follow_badge.blockSignals(True); self.follow_badge.setChecked(follow); self.follow_badge.blockSignals(False)
            visible = bool(cmds.getAttr(resolve_plug(cmds, spec.visibility_plug, control)))
            self.visible_badge.blockSignals(True); self.visible_badge.setChecked(visible); self.visible_badge.blockSignals(False)
            compact = self.compact_toggle.isChecked()
            destination = SPACE_JA[index]
            self.offset_destination.setText(
                "編集中・保存先：{}の握り位置".format(destination))
            self.compact_save_button.setText(
                "{}へ保存".format(destination) if compact else "握り保存")
            self.space_badge.setText(
                destination if compact
                else "この武器の装備先：{}".format(destination))
            self.space_badge.setStyleSheet(self._badge_style("#2874a6"))
            for space_index, status in enumerate(self.offset_save_labels):
                offset_saved = self.controller.service.has_saved_offset(
                    spec, space_index)
                status.setText("保存済" if offset_saved else "未保存")
                status.setStyleSheet(
                    "color:{}; font-size:10px; padding:1px;".format(
                        "#63b3ed" if offset_saved else "#b87872"))
            self.follow_badge.setText("追従  {}".format("ON" if follow else "OFF"))
            self.follow_badge.setStyleSheet(self._badge_style("#2e8b57" if follow else "#a4493d"))
            self.visible_badge.setText("表示  {}".format("ON" if visible else "OFF"))
            self.visible_badge.setStyleSheet(self._badge_style("#2e8b57" if visible else "#666b73"))
            visible_groups = {}
            for weapon in WEAPONS:
                try:
                    plug = resolve_plug(
                        cmds, weapon.visibility_plug, weapon.control)
                    if bool(cmds.getAttr(plug)):
                        visible_groups.setdefault(plug, []).append(weapon.label)
                except Exception:
                    continue
            visible_weapons = []
            for labels in visible_groups.values():
                text = " + ".join(labels)
                if len(labels) > 1:
                    text += "（共有表示）"
                visible_weapons.append(text)
            summary = " / ".join(visible_weapons) if visible_weapons else "なし"
            selected_visible = any(
                spec.label in labels for labels in visible_groups.values())
            self.visible_summary.setText(
                "シーン全体で表示中：{}{}".format(
                    summary,
                    "  ※操作中の武器は非表示" if not selected_visible else ""))
            multiple = len(visible_groups) > 1
            self.visible_summary.setStyleSheet(
                "background:{}; color:white; border-radius:4px; padding:7px; font-weight:700;".format(
                    "#a4493d" if not selected_visible else (
                        "#9a6324" if multiple else "#25313b")))
            setup = "セットアップ済み" if setup_done else "未セットアップ（最初の操作時に自動作成）"
            self.detail.setText("{} / {}".format(spec.label, setup))
        except Exception as exc:
            self.space_badge.setText("この武器の装備先：－"); self.follow_badge.setText("追従 －"); self.visible_badge.setText("表示 －")
            for status in self.offset_save_labels:
                status.setText("未確認")
                status.setStyleSheet(
                    "color:#8f969e; font-size:10px; padding:1px;")
            for badge in (self.space_badge, self.follow_badge, self.visible_badge):
                badge.setStyleSheet(self._badge_style("#666b73"))
            self.visible_summary.setText("シーン全体で表示中：確認できません")
            self.detail.setText("{} — 最初の操作時に自動セットアップされます".format(spec.label))

    def show(self): self.window.show(); self.window.raise_(); self.window.activateWindow()
