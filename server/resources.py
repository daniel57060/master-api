from dataclasses import dataclass
from pathlib import Path


@dataclass
class Resources:
    ROOT = Path(__file__).parent.parent
    FILES = ROOT / "files"

    RESOURCES = ROOT / "resources"

    DATABASE = RESOURCES / "database.db"


dirs = [
    Resources.FILES,
    Resources.RESOURCES,
]

for it in dirs:
    it.mkdir(exist_ok=True, parents=True)
