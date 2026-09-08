import json, zipfile, sys, collections, pathlib

PATH = sys.argv[1] if len(sys.argv) > 1 else \
    str(pathlib.Path(__file__).resolve().parent.parent / "dist" / "ClubRoyale.sb3")

z = zipfile.ZipFile(PATH)
names = set(z.namelist())
proj = json.loads(z.read("project.json"))
errs, warns = [], []

stage = proj["targets"][0]
assert stage["isStage"]
gvars = {vid for vid in stage["variables"]}
glists = {lid for lid in stage["lists"]}
bcasts = dict(stage["broadcasts"])

SHADOW_OPS = {
    "looks_costume", "looks_backdrops", "control_create_clone_of_menu",
    "sensing_touchingobjectmenu", "sensing_of_object_menu",
    "sound_sounds_menu", "motion_glideto_menu", "motion_goto_menu",
    "pen_menu_colorParam", "procedures_prototype",
    "argument_reporter_string_number",
}

for t in proj["targets"]:
    tn = t["name"]
    blocks = t["blocks"]
    ids = set(blocks)
    local_v = {vid for vid in t["variables"]}
    local_l = {lid for lid in t["lists"]}
    allv, alll = gvars | local_v, glists | local_l

    # costumes present
    for c in t["costumes"]:
        if c["md5ext"] not in names:
            errs.append(f"{tn}: missing asset {c['md5ext']}")
        for k in ("assetId", "name", "bitmapResolution", "dataFormat",
                  "rotationCenterX", "rotationCenterY"):
            if k not in c:
                errs.append(f"{tn}: costume {c.get('name')} missing {k}")
    if not t["costumes"]:
        errs.append(f"{tn}: no costumes")

    procdefs, proccalls = {}, []

    for bid, b in blocks.items():
        op = b["opcode"]
        # next / parent
        for k in ("next", "parent"):
            v = b.get(k)
            if v is not None and v not in ids:
                errs.append(f"{tn}/{bid}({op}): dangling {k} -> {v}")
        if b.get("topLevel"):
            if b.get("parent") is not None:
                errs.append(f"{tn}/{bid}({op}): topLevel but has parent")
            if "x" not in b or "y" not in b:
                errs.append(f"{tn}/{bid}({op}): topLevel without x/y")
        else:
            if b.get("parent") is None:
                errs.append(f"{tn}/{bid}({op}): orphan (no parent, not topLevel)")

        # inputs
        for iname, iv in b["inputs"].items():
            if iv is None:
                errs.append(f"{tn}/{bid}({op}): input {iname} is null")
                continue
            kind = iv[0]
            for slot in iv[1:]:
                if isinstance(slot, str):
                    if slot not in ids:
                        errs.append(
                            f"{tn}/{bid}({op}): input {iname} -> missing block {slot}")
                elif isinstance(slot, list):
                    code = slot[0]
                    if code == 12 and slot[2] not in allv:
                        errs.append(f"{tn}/{bid}: input var {slot[1]} unknown id")
                    if code == 13 and slot[2] not in alll:
                        errs.append(f"{tn}/{bid}: input list {slot[1]} unknown id")
                    if code == 11 and slot[2] not in bcasts:
                        errs.append(f"{tn}/{bid}: broadcast {slot[1]} unknown id")
                elif slot is None:
                    pass
            if kind not in (1, 2, 3):
                errs.append(f"{tn}/{bid}({op}): bad input kind {kind}")

        # fields
        for fname, fv in b["fields"].items():
            if fname == "VARIABLE" and fv[1] not in allv:
                errs.append(f"{tn}/{bid}: field VARIABLE {fv[0]} unknown id")
            if fname == "LIST" and fv[1] not in alll:
                errs.append(f"{tn}/{bid}: field LIST {fv[0]} unknown id")
            if fname == "BROADCAST_OPTION" and fv[1] not in bcasts:
                errs.append(f"{tn}/{bid}: field BROADCAST {fv[0]} unknown id")
            if fname == "COSTUME" and op == "looks_costume":
                if fv[0] not in [c["name"] for c in t["costumes"]]:
                    errs.append(f"{tn}/{bid}: costume '{fv[0]}' not in sprite")

        # shadow flags
        if b.get("shadow") and op not in SHADOW_OPS and not op.startswith(
                ("math_", "text", "colour_", "event_broadcast_menu")):
            warns.append(f"{tn}/{bid}: shadow=true on {op}")
        if op in SHADOW_OPS and op != "procedures_prototype" and not b.get("shadow"):
            warns.append(f"{tn}/{bid}: menu {op} not marked shadow")

        # procedures
        if op == "procedures_prototype":
            m = b["mutation"]
            procdefs[m["proccode"]] = m
            for k in ("argumentids", "argumentnames", "argumentdefaults",
                      "proccode", "warp"):
                if k not in m:
                    errs.append(f"{tn}/{bid}: prototype missing {k}")
            if len(json.loads(m["argumentids"])) != len(
                    json.loads(m["argumentnames"])):
                errs.append(f"{tn}/{bid}: prototype arg count mismatch")
        if op == "procedures_call":
            proccalls.append((bid, b["mutation"]))
        if op == "procedures_definition":
            ci = b["inputs"].get("custom_block")
            if not ci or ci[1] not in ids:
                errs.append(f"{tn}/{bid}: definition without prototype")
            elif blocks[ci[1]]["opcode"] != "procedures_prototype":
                errs.append(f"{tn}/{bid}: custom_block is not a prototype")

    for bid, m in proccalls:
        if m["proccode"] not in procdefs:
            errs.append(f"{tn}/{bid}: call to undefined proc '{m['proccode']}'")
        else:
            d = procdefs[m["proccode"]]
            if json.loads(m["argumentids"]) != json.loads(d["argumentids"]):
                errs.append(f"{tn}/{bid}: call argumentids != definition")
            if m.get("warp") != d.get("warp"):
                errs.append(f"{tn}/{bid}: call warp != definition warp")

# monitors
for mo in proj["monitors"]:
    if mo["opcode"] == "data_variable" and mo["id"] not in gvars:
        errs.append(f"monitor {mo['params']['VARIABLE']} unknown var id")

# duplicate block ids across whole project (must be unique per target only,
# but global uniqueness is safer)
seen = collections.Counter()
for t in proj["targets"]:
    for bid in t["blocks"]:
        seen[bid] += 1
dups = [k for k, v in seen.items() if v > 1]
if dups:
    errs.append(f"duplicate block ids: {dups[:5]}")

# A warp procedure ("run without screen refresh") that contains a time-based
# yield is pathological: scratch-vm re-executes the yielding block instead of
# yielding, so each wait busy-spins for the whole 500ms warp budget and starves
# every other script in the project. "duck hop" shipped this way in v3.2 and
# dropped the stage to a few frames per second for the length of every hop.
# Loops are fine inside warp - that is what warp is for. Clocks are not.
YIELDING = {
    "control_wait", "control_wait_until", "motion_glidesecstoxy",
    "motion_glideto", "event_broadcastandwait", "looks_sayforsecs",
    "looks_thinkforsecs", "looks_switchbackdroptoandwait", "sound_playuntildone",
}
for t in proj["targets"]:
    tn = t["name"]
    blocks = t["blocks"]
    for bid, b in blocks.items():
        if b.get("opcode") != "procedures_prototype":
            continue
        mut = b.get("mutation") or {}
        if str(mut.get("warp", "false")).lower() != "true":
            continue
        proccode = mut.get("proccode", bid)
        # the prototype hangs off a definition; walk that definition's stack
        root = None
        for cid, c in blocks.items():
            if c.get("opcode") == "procedures_definition":
                cust = (c.get("inputs") or {}).get("custom_block")
                if cust and len(cust) > 1 and cust[1] == bid:
                    root = c
                    break
        if root is None:
            continue
        # walk every block reachable from the definition, substacks included
        stack, found = [root.get("next")], set()
        while stack:
            cur = stack.pop()
            while cur:
                blk = blocks.get(cur)
                if not blk:
                    break
                if blk.get("opcode") in YIELDING:
                    found.add(blk["opcode"])
                for key, val in (blk.get("inputs") or {}).items():
                    if key.startswith("SUBSTACK") and len(val) > 1 and isinstance(val[1], str):
                        stack.append(val[1])
                cur = blk.get("next")
        if found:
            errs.append(f"{tn}: warp procedure '{proccode}' contains "
                        f"{sorted(found)} - it will busy-spin and freeze the VM")

# layer order sanity
los = [t["layerOrder"] for t in proj["targets"]]
if sorted(los) != list(range(len(los))):
    warns.append(f"layerOrder not a clean sequence: {los}")

print(f"targets {len(proj['targets'])}  blocks "
      f"{sum(len(t['blocks']) for t in proj['targets'])}  "
      f"assets {len(names)-1}")
print(f"ERRORS {len(errs)}   WARNINGS {len(warns)}")
for e in errs[:40]:
    print("  E", e)
for w in warns[:15]:
    print("  W", w)
sys.exit(1 if errs else 0)
