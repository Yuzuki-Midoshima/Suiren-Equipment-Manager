"""Application composition root."""


_WINDOW = None


def show():
    global _WINDOW
    import importlib
    from maya import cmds
    from . import constants
    importlib.reload(constants)
    from . import maya_utils
    importlib.reload(maya_utils)
    from . import rig_adapter
    importlib.reload(rig_adapter)
    from . import services
    importlib.reload(services)
    from . import controller
    importlib.reload(controller)
    from . import ui
    importlib.reload(ui)
    if _WINDOW is not None:
        try: _WINDOW.window.close()
        except RuntimeError: pass
    app_controller = controller.EquipmentController(
        cmds, services.EquipmentService(cmds))
    _WINDOW = ui.EquipmentManagerUI(app_controller)
    _WINDOW.show(); app_controller.refresh()
    return _WINDOW

