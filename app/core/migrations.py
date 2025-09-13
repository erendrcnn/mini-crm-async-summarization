from pathlib import Path
from alembic.config import Config
from alembic import command


def upgrade_head() -> None:
    root = Path(__file__).resolve().parents[2]
    ini_path = root / "alembic.ini"
    cfg = Config(str(ini_path))
    # Ensure script location resolves even if cwd differs
    cfg.set_main_option("script_location", str(root / "alembic"))
    command.upgrade(cfg, "head")
