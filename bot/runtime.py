"""Fixed module interface. Edit bot/modules/, never this file.

Every turn runs the modules in bot/modules/ in descending PRIORITY (default 0), then by
filename, in three phases:

1. observe(text, memory): remember things (a name, a fact, the topic). It never replies.
2. respond(text, memory): propose a reply (a string) or pass (None). Every module proposes;
   each one works on its own copy of memory, so a reply that is not chosen leaves no trace.
3. choose(text, memory, candidates) in bot/modules/arbiter.py picks one candidate, and the
   chosen module's copy of memory becomes the conversation's memory. A candidate is
   {"module": name, "priority": PRIORITY, "reply": text}; they arrive in the order above.
   Without a working arbiter, the first candidate (the highest PRIORITY) is chosen.

Then after(text, reply, memory) runs in every module that defines it, and the runtime appends
{"user": text, "bot": reply, "module": name} to memory["turns"] (read it, never change it).
A hook that raises is skipped unless strict mode is on.
"""
import copy
import importlib
import pkgutil

from . import modules

ARBITER = "arbiter"
FALLBACK = "Hello!"


def format_error(error):
    name = type(error).__name__
    try:
        msg = str(error)
    except Exception:
        return name
    return f"{name}: {msg}" if msg else name


def load_modules(*, errors=None):
    """[(name, priority, module)], highest PRIORITY first, then by filename."""
    loaded = []
    for entry in pkgutil.iter_modules(modules.__path__):
        try:
            module = importlib.import_module(f"{modules.__name__}.{entry.name}")
        except Exception as error:
            if errors is not None:
                errors.append((entry.name, format_error(error)))
            continue
        priority = getattr(module, "PRIORITY", 0)
        if isinstance(priority, bool) or not isinstance(priority, (int, float)):
            priority = 0
        loaded.append((priority, entry.name, module))
    loaded.sort(key=lambda item: (-item[0], item[1]))
    return [(name, priority, module) for priority, name, module in loaded]


def _hooks(name):
    return [(module_name, priority, getattr(module, name)) for module_name, priority, module in _MODULES
            if callable(getattr(module, name, None))]


_load_errors = []
_MODULES = load_modules(errors=_load_errors)
LOAD_ERRORS = tuple(_load_errors)
del _load_errors
_OBSERVERS = _hooks("observe")
_HANDLERS = _hooks("respond")
_AFTER = _hooks("after")
_ARBITER = next((getattr(module, "choose", None) for name, _, module in _MODULES if name == ARBITER), None)


def _copy(memory):
    """A module's own copy of memory. memory["turns"] is shared: only the runtime writes it."""
    try:
        return {key: value if key == "turns" else copy.deepcopy(value) for key, value in memory.items()}
    except Exception:  # noqa: BLE001 - a value that cannot be copied: share memory instead
        return memory


def _choose(text, memory, candidates, errors=None, strict=False):
    """The arbiter's pick, as an index into candidates; 0 when it fails or returns nonsense."""
    if _ARBITER is None or len(candidates) < 2:
        return 0
    views = [dict(c) for c in candidates]
    try:
        picked = _ARBITER(text, memory, views)
    except Exception as error:
        if strict:
            raise
        if errors is not None:
            errors.append(("choose", ARBITER, format_error(error)))
        return 0
    if isinstance(picked, int) and not isinstance(picked, bool) and 0 <= picked < len(views):
        return picked
    if isinstance(picked, dict):
        for i, view in enumerate(views):
            if view is picked or view["module"] == picked.get("module"):
                return i
    return 0


def turn(text, memory, strict=False, *, errors=None):
    """One turn: {"reply", "module", "candidates"}. Updates memory in place."""
    for name, _, observe in _OBSERVERS:
        try:
            observe(text, memory)
        except Exception as error:
            if strict:
                raise
            if errors is not None:
                errors.append(("observe", name, format_error(error)))
            continue
    candidates, copies = [], []
    for name, priority, respond in _HANDLERS:
        mine = _copy(memory)
        try:
            answer = respond(text, mine)
        except Exception as error:
            if strict:
                raise
            if errors is not None:
                errors.append(("respond", name, format_error(error)))
            continue
        if isinstance(answer, str) and answer.strip():
            candidates.append({"module": name, "priority": priority, "reply": answer})
            copies.append(mine)
    if candidates:
        index = _choose(text, memory, candidates, errors=errors, strict=strict)
        reply, module = candidates[index]["reply"], candidates[index]["module"]
        if copies[index] is not memory:
            memory.clear()
            memory.update(copies[index])
    else:
        reply, module = FALLBACK, None
    for name, _, after in _AFTER:
        try:
            after(text, reply, memory)
        except Exception as error:
            if strict:
                raise
            if errors is not None:
                errors.append(("after", name, format_error(error)))
            continue
    turns = memory.get("turns")
    if not isinstance(turns, list):
        turns = memory["turns"] = []
    turns.append({"user": text, "bot": reply, "module": module})
    return {"reply": reply, "module": module, "candidates": candidates}


def reply(text, memory):
    return turn(text, memory)["reply"]
