"""Repo-relative paths. Everything generated lands under build/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
ASSETS = BUILD / "assets"
SFX_DIR = BUILD / "sfx"
DIST = ROOT / "dist"

for _d in (BUILD, ASSETS, SFX_DIR, DIST):
    _d.mkdir(parents=True, exist_ok=True)


def _stale(name):
    """Does this solver still need to run?

    Missing output is the obvious case. The other one is a solver that has
    been edited since it last wrote: the JSON is then a table nobody solved
    for the code that is about to ship, and because the JS harnesses read the
    same file, the build and the test agree with each other while both
    disagree with the source. A solver opts out of that by dumping a `digest`
    of its own source; one that does not is only checked for existence, as
    before.
    """
    out = BUILD / f"{name}.json"
    if not out.exists():
        return True
    try:
        import hashlib
        import json
        cached = json.load(open(out)).get("digest")
        if cached is None:
            return False
        src = (Path(__file__).resolve().parent / f"{name}.py").read_bytes()
        return cached != hashlib.sha256(src).hexdigest()
    except (ValueError, OSError):
        return True


def ensure_tables():
    """Solve the payout tables if they are not cached yet."""
    if _stale("tables"):
        import tables  # noqa: F401  (writes on import)
    if _stale("tables2"):
        import tables2  # noqa: F401
    if _stale("tables3"):
        import tables3  # noqa: F401
    if _stale("tables4"):
        import tables4  # noqa: F401
    if _stale("tables5"):
        import tables5  # noqa: F401
    if _stale("tables6"):
        import tables6  # noqa: F401
    if _stale("tables7"):
        import tables7  # noqa: F401
