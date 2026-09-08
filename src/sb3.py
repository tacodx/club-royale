"""Minimal Scratch 3 project builder.

Compiles a Python DSL into a valid project.json / .sb3 archive.
Handles block id allocation, next/parent wiring, variables, lists,
broadcasts, custom blocks (procedures) and monitors.
"""
import json, os, hashlib, zipfile, itertools

# ---------------------------------------------------------------- ids
_counter = itertools.count(1)


def nid(prefix="b"):
    return f"{prefix}{next(_counter):05d}"


# ------------------------------------------------------------- inputs
# Scratch input shadow type codes
NUM, POSNUM, WHOLE, INT, ANGLE, COLOR, TEXT = 4, 5, 6, 7, 8, 9, 10


class Ref:
    """A reporter block that has not been materialised yet."""

    def __init__(self, opcode, inputs=None, fields=None, mutation=None):
        self.opcode = opcode
        self.inputs = inputs or {}
        self.fields = fields or {}
        self.mutation = mutation


class VarRef:
    def __init__(self, name, vid):
        self.name, self.id = name, vid


class ListRef:
    def __init__(self, name, lid):
        self.name, self.id = name, lid


class ArgRef:
    """Reporter for a custom-block argument."""

    def __init__(self, name):
        self.name = name


# ------------------------------------------------------------- target
class Target:
    def __init__(self, project, name, is_stage=False):
        self.project = project
        self.name = name
        self.is_stage = is_stage
        self.blocks = {}
        self.costumes = []
        self.sounds = []
        self.variables = {}
        self.lists = {}
        self.local_vars = {}
        self.x, self.y = 0, 0
        self.visible = True
        self.size = 100
        self.current_costume = 0
        self.layer_order = 0
        self._script_x = 40
        self._script_y = 40
        self.procs = {}  # proccode -> (argids, argnames, warp)

    # --- assets -------------------------------------------------
    def add_costume(self, name, path, cx=None, cy=None, res=2):
        data = open(path, "rb").read()
        md5 = hashlib.md5(data).hexdigest()
        ext = os.path.splitext(path)[1][1:].lower()
        self.project.assets[md5 + "." + ext] = data
        from PIL import Image

        if cx is None or cy is None:
            with Image.open(path) as im:
                w, h = im.size
            cx, cy = w // 2, h // 2
        self.costumes.append(
            {
                "assetId": md5,
                "name": name,
                "bitmapResolution": res,
                "md5ext": f"{md5}.{ext}",
                "dataFormat": ext,
                "rotationCenterX": cx,
                "rotationCenterY": cy,
            }
        )
        return name

    def add_sound(self, name, path):
        import wave
        data = open(path, "rb").read()
        md5 = hashlib.md5(data).hexdigest()
        self.project.assets[md5 + ".wav"] = data
        with wave.open(path, "rb") as w:
            rate, frames = w.getframerate(), w.getnframes()
        self.sounds.append({
            "assetId": md5, "name": name, "dataFormat": "wav",
            "format": "", "rate": rate, "sampleCount": frames,
            "md5ext": f"{md5}.wav",
        })
        return name

    # --- local variables ---------------------------------------
    def local_var(self, name, value=0):
        vid = nid("lv")
        self.variables[vid] = [name, value]
        r = VarRef(name, vid)
        self.local_vars[name] = r
        return r

    # --- scripts ------------------------------------------------
    def script(self, *blocks, x=None, y=None):
        """Attach a stack of blocks as a top-level script."""
        flat = _flatten(blocks)
        if not flat:
            return
        ids = [self._emit(b) for b in flat]
        for i, bid in enumerate(ids):
            self.blocks[bid]["next"] = ids[i + 1] if i + 1 < len(ids) else None
            self.blocks[bid]["parent"] = ids[i - 1] if i else None
        head = self.blocks[ids[0]]
        head["topLevel"] = True
        head["x"] = x if x is not None else self._script_x
        head["y"] = y if y is not None else self._script_y
        self._script_y += 0
        if x is None:
            self._script_x += 420
            if self._script_x > 2000:
                self._script_x = 40
                self._script_y += 700
        return ids[0]

    # --- emit ---------------------------------------------------
    def _emit(self, spec, parent=None, shadow=False):
        """spec is (opcode, inputs, fields, mutation)."""
        opcode, inputs, fields, mutation = spec
        bid = nid()
        blk = {
            "opcode": opcode,
            "next": None,
            "parent": parent,
            "inputs": {},
            "fields": {},
            "shadow": shadow,
            "topLevel": False,
        }
        if mutation:
            blk["mutation"] = mutation
        self.blocks[bid] = blk
        for k, v in (fields or {}).items():
            blk["fields"][k] = v
        for k, v in (inputs or {}).items():
            blk["inputs"][k] = self._input(v, bid)
        return bid

    def _input(self, v, parent):
        # substack: list of stack blocks
        if isinstance(v, Substack):
            flat = _flatten(v.blocks)
            if not flat:
                return None
            ids = [self._emit(b) for b in flat]
            for i, bid in enumerate(ids):
                self.blocks[bid]["next"] = ids[i + 1] if i + 1 < len(ids) else None
                self.blocks[bid]["parent"] = ids[i - 1] if i else parent
            return [2, ids[0]]
        if isinstance(v, Shadow):
            sid = self._emit(v.spec, parent, shadow=True)
            return [1, sid]
        if isinstance(v, Cover):
            bid = self._emit(v.spec, parent)
            return [3, bid, v.shadow_val]
        if isinstance(v, CoverMenu):
            r = v.reporter
            rspec = ((r.opcode, r.inputs, r.fields, r.mutation)
                     if isinstance(r, Ref) else None)
            if rspec is not None:
                bid = self._emit(rspec, parent)
            elif isinstance(r, VarRef):
                sid = self._emit(v.menu_spec, parent, shadow=True)
                return [3, [12, r.name, r.id], sid]
            elif isinstance(r, ArgRef):
                bid = self._emit(("argument_reporter_string_number", {},
                                  {"VALUE": [r.name, None]}, None), parent)
            else:
                raise TypeError("CoverMenu needs a reporter")
            sid = self._emit(v.menu_spec, parent, shadow=True)
            return [3, bid, sid]
        if isinstance(v, VarRef):
            return [3, [12, v.name, v.id], [TEXT, ""]]
        if isinstance(v, ListRef):
            return [3, [13, v.name, v.id], [TEXT, ""]]
        if isinstance(v, ArgRef):
            bid = self._emit(
                ("argument_reporter_string_number", {}, {"VALUE": [v.name, None]}, None),
                parent,
            )
            return [3, bid, [TEXT, ""]]
        if isinstance(v, Ref):
            bid = self._emit((v.opcode, v.inputs, v.fields, v.mutation), parent)
            return [3, bid, [TEXT, ""]]
        if isinstance(v, Raw):
            return v.value
        if isinstance(v, bool):
            return None
        # plain literal
        if isinstance(v, (int, float)):
            return [1, [NUM, str(v)]]
        return [1, [TEXT, str(v)]]


class Substack:
    def __init__(self, blocks):
        self.blocks = blocks


class Shadow:
    def __init__(self, spec):
        self.spec = spec


class Cover:
    """A block placed over a typed shadow (used for menus with blocks)."""

    def __init__(self, spec, shadow_val):
        self.spec, self.shadow_val = spec, shadow_val


class CoverMenu:
    """A reporter dropped onto a dropdown-menu shadow block."""

    def __init__(self, reporter, menu_spec):
        self.reporter, self.menu_spec = reporter, menu_spec


class Raw:
    def __init__(self, value):
        self.value = value


def _flatten(items):
    out = []
    for it in items:
        if it is None:
            continue
        if isinstance(it, (list, tuple)) and not (
            len(it) == 4 and isinstance(it[0], str)
        ):
            out.extend(_flatten(it))
        else:
            out.append(it)
    return out


# ------------------------------------------------------------ project
class Project:
    def __init__(self):
        self.assets = {}
        self.stage = Target(self, "Stage", is_stage=True)
        self.targets = [self.stage]
        self.broadcasts = {}
        self.monitors = []

    def sprite(self, name):
        t = Target(self, name)
        t.layer_order = len(self.targets)
        self.targets.append(t)
        return t

    def var(self, name, value=0):
        vid = nid("gv")
        self.stage.variables[vid] = [name, value]
        return VarRef(name, vid)

    def lst(self, name, items=None):
        lid = nid("gl")
        self.stage.lists[lid] = [name, items or []]
        return ListRef(name, lid)

    def bc(self, name):
        if name not in self.broadcasts:
            self.broadcasts[name] = nid("bc")
        return self.broadcasts[name]

    def monitor(self, ref, x, y, mode="large", visible=True):
        self.monitors.append(
            {
                "id": ref.id,
                "mode": mode,
                "opcode": "data_variable",
                "params": {"VARIABLE": ref.name},
                "spriteName": None,
                "value": 0,
                "width": 0,
                "height": 0,
                "x": x,
                "y": y,
                "visible": visible,
                "sliderMin": 0,
                "sliderMax": 100,
                "isDiscrete": True,
            }
        )

    # --- serialise ---------------------------------------------
    def to_json(self):
        targets = []
        for t in self.targets:
            d = {
                "isStage": t.is_stage,
                "name": t.name,
                "variables": t.variables,
                "lists": t.lists,
                "broadcasts": ({v: k for k, v in self.broadcasts.items()}
                               if t.is_stage else {}),
                "blocks": t.blocks,
                "comments": {},
                "currentCostume": t.current_costume,
                "costumes": t.costumes,
                "sounds": t.sounds,
                "volume": 100,
                "layerOrder": t.layer_order,
            }
            if t.is_stage:
                d.update(
                    {
                        "tempo": 60,
                        "videoTransparency": 50,
                        "videoState": "off",
                        "textToSpeechLanguage": None,
                    }
                )
            else:
                d.update(
                    {
                        "visible": t.visible,
                        "x": t.x,
                        "y": t.y,
                        "size": t.size,
                        "direction": 90,
                        "draggable": False,
                        "rotationStyle": "all around",
                    }
                )
            targets.append(d)
        return {
            "targets": targets,
            "monitors": self.monitors,
            "extensions": [],
            "meta": {"semver": "3.0.0", "vm": "2.3.0", "agent": ""},
        }

    def save(self, path):
        pj = json.dumps(self.to_json())
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("project.json", pj)
            for name, data in self.assets.items():
                z.writestr(name, data)
        return path
