"""Small, defensive Maya helpers."""

from contextlib import contextmanager
from typing import Any, Iterable, List


class SceneError(RuntimeError):
    pass


def resolve(cmds: Any, name: str, context: str = "") -> str:
    matches = cmds.ls(name, long=True) or []
    if not matches:
        # Maya references normally add ``namespace:`` while importing with
        # "Use selected namespace as prefix" can produce ``prefix_Node``.
        # Accept both without hard-coding a particular shot namespace.
        candidates = []
        for pattern in ("*:" + name, "*_" + name):
            candidates.extend(cmds.ls(pattern, long=True) or [])
        matches = list(dict.fromkeys(candidates))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SceneError("ノードが見つかりません: {}".format(name))
    if context:
        contexts = cmds.ls(context, long=True) or []
        if len(contexts) == 1:
            prefix = contexts[0].rsplit("|", 1)[0]
            local = [item for item in matches if item.startswith(prefix + "|")]
            if len(local) == 1:
                return local[0]
    raise SceneError("ノード名が曖昧です: {}".format(name))


def resolve_plug(cmds: Any, plug: str, context: str = "") -> str:
    """Resolve only the node portion of ``node.attribute``."""
    if "." not in plug:
        raise SceneError("属性名が不正です: {}".format(plug))
    node, attribute = plug.split(".", 1)
    resolved = resolve(cmds, node, context=context)
    result = "{}.{}".format(resolved, attribute)
    if not cmds.objExists(result):
        raise SceneError("属性が見つかりません: {}".format(plug))
    return result


def incoming(cmds: Any, node: str, attrs: Iterable[str]) -> List[str]:
    result = []
    for attr in attrs:
        result.extend(cmds.listConnections(
            "{}.{}".format(node, attr), source=True, destination=False,
            plugs=True, skipConversionNodes=False) or [])
    return result


@contextmanager
def undo_chunk(cmds: Any, name: str):
    cmds.undoInfo(openChunk=True, chunkName=name)
    try:
        yield
    finally:
        cmds.undoInfo(closeChunk=True)

