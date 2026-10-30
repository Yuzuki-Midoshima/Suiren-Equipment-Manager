"""Register Suiren Equipment Manager on Maya's active shelf.

Run in Maya's Python Script Editor::

    import register_shelf
    register_shelf.register()
"""

from __future__ import annotations

from pathlib import Path

from maya import cmds, mel


BUTTON_TAG = "SuirenEquipmentManagerShelfButton"
BUTTON_LABEL = "Suiren\nEquip"
ANNOTATION = "Suiren Equipment Manager を開く"
ICON_FILENAME = "suiren_equipment_manager.png"


def _project_root() -> str:
    """Resolve this distribution's root without a user-specific path."""
    module_file = globals().get("__file__")
    if module_file:
        return str(Path(module_file).resolve().parent)
    module_spec = globals().get("__spec__")
    origin = getattr(module_spec, "origin", None)
    if origin:
        return str(Path(origin).resolve().parent)
    raise RuntimeError(
        "register_shelf.py の場所を取得できません。"
        "drag_and_drop_install.py をMayaへドロップして登録してください。")


def _icon_path() -> str:
    """Return the project-local 32 px shelf icon."""
    # Maya/Qt resolves Unicode paths more reliably with forward slashes.
    return str(
        Path(_project_root()) / "icons" / ICON_FILENAME
    ).replace("\\", "/")


def _icon_flags() -> dict:
    """Use the custom image at every Maya shelf icon size."""
    icon = _icon_path()
    return {
        "image": icon,
        "image1": icon,
        "image2": icon,
        "image3": icon,
        "style": "iconOnly",
        "scaleIcon": True,
        "imageOverlayLabel": "",
    }


def _launch_command() -> str:
    """Return a self-contained command that works outside Maya's sys.path."""
    return """import importlib
import sys
project_root = {project_root!r}
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import suiren_equipment_manager.constants as sem_constants
importlib.reload(sem_constants)
import suiren_equipment_manager.maya_utils as sem_maya_utils
importlib.reload(sem_maya_utils)
import suiren_equipment_manager.rig_adapter as sem_rig_adapter
importlib.reload(sem_rig_adapter)
import suiren_equipment_manager.services as sem_services
importlib.reload(sem_services)
import suiren_equipment_manager.controller as sem_controller
importlib.reload(sem_controller)
import suiren_equipment_manager.ui as sem_ui
importlib.reload(sem_ui)
import suiren_equipment_manager.app as suiren_equipment_manager_app
importlib.reload(suiren_equipment_manager_app)
suiren_equipment_manager_app.show()""".format(project_root=_project_root())


def _active_shelf() -> str:
    shelf_top = mel.eval("$tmp = $gShelfTopLevel")
    shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)
    if not shelf:
        raise RuntimeError("選択中のMayaシェルフを取得できませんでした。")
    return shelf


def _matching_buttons(shelf: str) -> list[str]:
    matches = []
    for child in cmds.shelfLayout(shelf, query=True, childArray=True) or []:
        if not cmds.objectTypeUI(child, isType="shelfButton"):
            continue
        try:
            doc_tag = cmds.shelfButton(child, query=True, docTag=True) or ""
            label = cmds.shelfButton(child, query=True, label=True) or ""
            annotation = cmds.shelfButton(
                child, query=True, annotation=True) or ""
            if (
                doc_tag == BUTTON_TAG
                or label.replace("\n", " ") in ("Suiren Equip", "SUIREN EQUIP")
                or "Suiren Equipment Manager" in annotation
            ):
                matches.append(child)
        except RuntimeError:
            continue
    return matches


def register() -> str:
    """Create or update one button on the currently selected shelf."""
    shelf_top = mel.eval("$tmp = $gShelfTopLevel")
    shelf = _active_shelf()
    matches = _matching_buttons(shelf)

    if matches:
        button = matches[0]
        icon_flags = _icon_flags()
        cmds.shelfButton(
            button,
            edit=True,
            label=BUTTON_LABEL,
            annotation=ANNOTATION,
            command=_launch_command(),
            sourceType="python",
            docTag=BUTTON_TAG,
            **icon_flags
        )
        # Clean up duplicates left by older/manual registrations.
        for duplicate in matches[1:]:
            cmds.deleteUI(duplicate)
    else:
        icon_flags = _icon_flags()
        button = cmds.shelfButton(
            parent=shelf,
            label=BUTTON_LABEL,
            annotation=ANNOTATION,
            command=_launch_command(),
            sourceType="python",
            docTag=BUTTON_TAG,
            **icon_flags
        )

    # saveAllShelves is a Maya MEL procedure rather than a cmds command.
    mel.eval('saveAllShelves "{}"'.format(shelf_top))
    message = "Suiren Equipment Manager をシェルフ '{}' に登録しました。".format(shelf)
    cmds.inViewMessage(amg="<hl>{}</hl>".format(message),
                       pos="midCenter", fade=True)
    print(message)
    return button


if __name__ == "__main__":
    register()

