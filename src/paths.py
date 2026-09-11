"""Repo-relative paths. Everything generated lands under build/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
ASSETS = BUILD / "assets"
SFX_DIR = BUILD / "sfx"
DIST = ROOT / "dist"

for _d in (BUILD, ASSETS, SFX_DIR, DIST):
    _d.mkdir(parents=True, exist_ok=True)


def ensure_tables():
    """Solve the payout tables if they are not cached yet."""
    if not (BUILD / "tables.json").exists():
        import tables  # noqa: F401  (writes on import)
    if not (BUILD / "tables2.json").exists():
        import tables2  # noqa: F401
    if not (BUILD / "tables3.json").exists():
        import tables3  # noqa: F401
    if not (BUILD / "tables4.json").exists():
        import tables4  # noqa: F401
    if not (BUILD / "tables5.json").exists():
        import tables5  # noqa: F401
    if not (BUILD / "tables6.json").exists():
        import tables6  # noqa: F401
