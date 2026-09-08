"""Block constructors for the sb3 builder.

Stack blocks are 4-tuples (opcode, inputs, fields, mutation).
Reporters/booleans are Ref objects.
"""
from sb3 import (Ref, Substack, Shadow, Cover, CoverMenu, Raw,
                 VarRef, ListRef, ArgRef, nid)
import json as _json

S = Substack


def _b(op, inputs=None, fields=None, mutation=None):
    return (op, inputs or {}, fields or {}, mutation)


# ------------------------------------------------------------- events
def when_flag():
    return _b("event_whenflagclicked")


def when_bc(proj, name):
    return _b(
        "event_whenbroadcastreceived", {}, {"BROADCAST_OPTION": [name, proj.bc(name)]}
    )


def broadcast(proj, name):
    return _b("event_broadcast", {"BROADCAST_INPUT": Raw([1, [11, name, proj.bc(name)]])})


def broadcast_wait(proj, name):
    return _b(
        "event_broadcastandwait", {"BROADCAST_INPUT": Raw([1, [11, name, proj.bc(name)]])}
    )


def when_clicked():
    return _b("event_whenthisspriteclicked")


def when_key(key):
    return _b("event_whenkeypressed", {}, {"KEY_OPTION": [key, None]})


# ------------------------------------------------------------ control
def wait(secs):
    return _b("control_wait", {"DURATION": secs})


def repeat(n, *body):
    return _b("control_repeat", {"TIMES": n, "SUBSTACK": S(body)})


def forever(*body):
    return _b("control_forever", {"SUBSTACK": S(body)})


def if_(cond, *body):
    return _b("control_if", {"CONDITION": cond, "SUBSTACK": S(body)})


def if_else(cond, then, other):
    return _b(
        "control_if_else",
        {"CONDITION": cond, "SUBSTACK": S(then), "SUBSTACK2": S(other)},
    )


def wait_until(cond):
    return _b("control_wait_until", {"CONDITION": cond})


def repeat_until(cond, *body):
    return _b("control_repeat_until", {"CONDITION": cond, "SUBSTACK": S(body)})


def stop(option="this script"):
    mut = {"tagName": "mutation", "children": [], "hasnext": "false"}
    if option == "other scripts in sprite":
        mut["hasnext"] = "true"
    return _b("control_stop", {}, {"STOP_OPTION": [option, None]}, mut)


def clone(target="_myself_"):
    return _b(
        "control_create_clone_of",
        {
            "CLONE_OPTION": Shadow(
                _b("control_create_clone_of_menu", {}, {"CLONE_OPTION": [target, None]})
            )
        },
    )


def when_clone():
    return _b("control_start_as_clone")


def delete_clone():
    return _b("control_delete_this_clone")


# -------------------------------------------------------------- looks
def switch_costume(name):
    return _b(
        "looks_switchcostumeto",
        {"COSTUME": Shadow(_b("looks_costume", {}, {"COSTUME": [name, None]}))},
    )


def switch_costume_r(reporter, default="c1"):
    """Switch costume using a reporter dropped onto the costume menu."""
    return _b(
        "looks_switchcostumeto",
        {"COSTUME": CoverMenu(reporter,
                              ("looks_costume", {}, {"COSTUME": [default, None]}, None))},
    )


def switch_backdrop_r(reporter, default="bg"):
    return _b(
        "looks_switchbackdropto",
        {"BACKDROP": CoverMenu(reporter,
                               ("looks_backdrops", {}, {"BACKDROP": [default, None]}, None))},
    )


def switch_backdrop(name):
    return _b(
        "looks_switchbackdropto",
        {"BACKDROP": Shadow(_b("looks_backdrops", {}, {"BACKDROP": [name, None]}))},
    )


def next_costume():
    return _b("looks_nextcostume")


def show():
    return _b("looks_show")


def hide():
    return _b("looks_hide")


def say(msg):
    return _b("looks_say", {"MESSAGE": msg})


def say_for(msg, secs):
    return _b("looks_sayforsecs", {"MESSAGE": msg, "SECS": secs})


def set_size(n):
    return _b("looks_setsizeto", {"SIZE": n})


def change_size(n):
    return _b("looks_changesizeby", {"CHANGE": n})


def set_effect(effect, val):
    return _b("looks_seteffectto", {"VALUE": val}, {"EFFECT": [effect, None]})


def change_effect(effect, val):
    return _b("looks_changeeffectby", {"CHANGE": val}, {"EFFECT": [effect, None]})


def clear_effects():
    return _b("looks_cleargraphiceffects")


def go_layer(where="front"):
    return _b("looks_goto_front_back", {}, {"FRONT_BACK": [where, None]})


def costume_number():
    return Ref("looks_costumenumbername", {}, {"NUMBER_NAME": ["number", None]})


# ------------------------------------------------------------- motion
def goto(x, y):
    return _b("motion_gotoxy", {"X": x, "Y": y})


def glide(secs, x, y):
    return _b("motion_glidesecstoxy", {"SECS": secs, "X": x, "Y": y})


def change_x(n):
    return _b("motion_changexby", {"DX": n})


def change_y(n):
    return _b("motion_changeyby", {"DY": n})


def set_x(n):
    return _b("motion_setx", {"X": n})


def set_y(n):
    return _b("motion_sety", {"Y": n})


def xpos():
    return Ref("motion_xposition")


def ypos():
    return Ref("motion_yposition")


# ------------------------------------------------------------ sensing
def mouse_down():
    return Ref("sensing_mousedown")


def touching_mouse():
    return Ref(
        "sensing_touchingobject",
        {
            "TOUCHINGOBJECTMENU": Shadow(
                _b(
                    "sensing_touchingobjectmenu",
                    {},
                    {"TOUCHINGOBJECTMENU": ["_mouse_", None]},
                )
            )
        },
    )


def timer():
    return Ref("sensing_timer")


def reset_timer():
    return _b("sensing_resettimer")


# ---------------------------------------------------------- operators
def add(a, b):
    return Ref("operator_add", {"NUM1": a, "NUM2": b})


def sub(a, b):
    return Ref("operator_subtract", {"NUM1": a, "NUM2": b})


def mul(a, b):
    return Ref("operator_multiply", {"NUM1": a, "NUM2": b})


def div(a, b):
    return Ref("operator_divide", {"NUM1": a, "NUM2": b})


def rand(a, b):
    return Ref("operator_random", {"FROM": a, "TO": b})


def gt(a, b):
    return Ref("operator_gt", {"OPERAND1": a, "OPERAND2": b})


def lt(a, b):
    return Ref("operator_lt", {"OPERAND1": a, "OPERAND2": b})


def eq(a, b):
    return Ref("operator_equals", {"OPERAND1": a, "OPERAND2": b})


def and_(a, b):
    return Ref("operator_and", {"OPERAND1": a, "OPERAND2": b})


def or_(a, b):
    return Ref("operator_or", {"OPERAND1": a, "OPERAND2": b})


def not_(a):
    return Ref("operator_not", {"OPERAND": a})


def join(a, b):
    return Ref("operator_join", {"STRING1": a, "STRING2": b})


def letter_of(i, s):
    return Ref("operator_letter_of", {"LETTER": i, "STRING": s})


def length_of(s):
    return Ref("operator_length", {"STRING": s})


def contains(a, b):
    return Ref("operator_contains", {"STRING1": a, "STRING2": b})


def mod(a, b):
    return Ref("operator_mod", {"NUM1": a, "NUM2": b})


def round_(a):
    return Ref("operator_round", {"NUM": a})


def mathop(op, a):
    return Ref("operator_mathop", {"NUM": a}, {"OPERATOR": [op, None]})


# --------------------------------------------------------------- data
def set_var(v, val):
    return _b("data_setvariableto", {"VALUE": val}, {"VARIABLE": [v.name, v.id]})


def change_var(v, val):
    return _b("data_changevariableby", {"VALUE": val}, {"VARIABLE": [v.name, v.id]})


def add_to(l, item):
    return _b("data_addtolist", {"ITEM": item}, {"LIST": [l.name, l.id]})


def delete_of(l, idx):
    return _b("data_deleteoflist", {"INDEX": idx}, {"LIST": [l.name, l.id]})


def delete_all(l):
    return _b("data_deletealloflist", {}, {"LIST": [l.name, l.id]})


def replace_item(l, idx, item):
    return _b(
        "data_replaceitemoflist",
        {"INDEX": idx, "ITEM": item},
        {"LIST": [l.name, l.id]},
    )


def item_of(l, idx):
    return Ref("data_itemoflist", {"INDEX": idx}, {"LIST": [l.name, l.id]})


def item_num_of(l, item):
    return Ref("data_itemnumoflist", {"ITEM": item}, {"LIST": [l.name, l.id]})


def len_of(l):
    return Ref("data_lengthoflist", {}, {"LIST": [l.name, l.id]})


def list_contains(l, item):
    return Ref("data_listcontainsitem", {"ITEM": item}, {"LIST": [l.name, l.id]})


# --------------------------------------------------------- procedures
class Proc:
    """A custom block definition + call factory."""

    def __init__(self, target, proccode, argnames, warp=True):
        self.target = target
        self.proccode = proccode
        self.argnames = argnames
        self.argids = [nid("arg") for _ in argnames]
        self.warp = warp

    def mutation(self, prototype):
        m = {
            "tagName": "mutation",
            "children": [],
            "proccode": self.proccode,
            "argumentids": _json.dumps(self.argids),
            "warp": "true" if self.warp else "false",
        }
        if prototype:
            m["argumentnames"] = _json.dumps(self.argnames)
            m["argumentdefaults"] = _json.dumps(["" for _ in self.argnames])
        return m

    def call(self, *args):
        inputs = {aid: a for aid, a in zip(self.argids, args)}
        return _b("procedures_call", inputs, {}, self.mutation(False))

    def arg(self, name):
        return ArgRef(name)


def define(target, proc, *body, x=40, y=40):
    """Emit a procedures_definition script for proc."""
    t = target
    proto_id = nid()
    def_id = nid()
    proto = {
        "opcode": "procedures_prototype",
        "next": None,
        "parent": def_id,
        "inputs": {},
        "fields": {},
        "shadow": True,
        "topLevel": False,
        "mutation": proc.mutation(True),
    }
    for aid, aname in zip(proc.argids, proc.argnames):
        rid = nid()
        t.blocks[rid] = {
            "opcode": "argument_reporter_string_number",
            "next": None,
            "parent": proto_id,
            "inputs": {},
            "fields": {"VALUE": [aname, None]},
            "shadow": True,
            "topLevel": False,
        }
        proto["inputs"][aid] = [1, rid]
    t.blocks[proto_id] = proto
    t.blocks[def_id] = {
        "opcode": "procedures_definition",
        "next": None,
        "parent": None,
        "inputs": {"custom_block": [1, proto_id]},
        "fields": {},
        "shadow": False,
        "topLevel": True,
        "x": x,
        "y": y,
    }
    from sb3 import _flatten

    flat = _flatten(body)
    if flat:
        ids = [t._emit(b) for b in flat]
        for i, bid in enumerate(ids):
            t.blocks[bid]["next"] = ids[i + 1] if i + 1 < len(ids) else None
            t.blocks[bid]["parent"] = ids[i - 1] if i else def_id
        t.blocks[def_id]["next"] = ids[0]
    return def_id


def show_var(v):
    return _b("data_showvariable", {}, {"VARIABLE": [v.name, v.id]})


def hide_var(v):
    return _b("data_hidevariable", {}, {"VARIABLE": [v.name, v.id]})


def point_dir(d):
    return _b("motion_pointindirection", {"DIRECTION": d})


def play_sound(name):
    return _b("sound_play", {"SOUND_MENU": Shadow(
        _b("sound_sounds_menu", {}, {"SOUND_MENU": [name, None]}))})


def play_sound_wait(name):
    return _b("sound_playuntildone", {"SOUND_MENU": Shadow(
        _b("sound_sounds_menu", {}, {"SOUND_MENU": [name, None]}))})


def play_sound_r(reporter, default="s1"):
    return _b("sound_play", {"SOUND_MENU": CoverMenu(
        reporter, ("sound_sounds_menu", {}, {"SOUND_MENU": [default, None]}, None))})


def set_volume(v):
    return _b("sound_setvolumeto", {"VOLUME": v})


def any_of(*conds):
    out = conds[0]
    for c in conds[1:]:
        out = or_(out, c)
    return out


def all_of(*conds):
    out = conds[0]
    for c in conds[1:]:
        out = and_(out, c)
    return out


def set_sound_effect(effect, value):
    return _b("sound_seteffectto", {"VALUE": value}, {"EFFECT": [effect, None]})


def clear_sound_effects():
    return _b("sound_cleareffects")
