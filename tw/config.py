"""DEV config for CHG-TW-001. PublicFunds is a read-only pinned upstream."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "chg-tw-001-dev.json"

PUBLICFUNDS_PIN = "de37f666c12d1d6b7a815860894af0372514ba7f"
EXPECTED_OCDS_SHA256 = "a2849a632148ca1eb59c0ceabeb45de16be0698a1804a485cf93417542435225"
EXPECTED_OCDS_SIZE = 11_676_874
DEFAULT_BUYER = "City of Cape Town"
RIGHT_OF_REPLY = "Right of reply: pending"
INDICATOR_WINDOW_LABEL = (
    "The registration year on the CIPC number is the same as, or the year before, "
    "the award year (0–23 months)"
)
OCDS_SOURCE_URL = "https://data.open-contracting.org/en/publication/143/download?name=full.jsonl.gz"
LEARN_MORE_URL = "https://data.etenders.gov.za/Home/LearnMore"


def load_config(path: Path | None = None) -> dict:
    p = path or CONFIG_PATH
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("env") != "DEV":
        raise RuntimeError("CHG-TW-001 config must name env DEV")
    return data


def ocds_input_path(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    for raw in cfg["etenders_ocds"]["paths"]:
        p = Path(raw)
        if p.is_file():
            return p
    raise FileNotFoundError("pinned PublicFunds etenders_ocds file not found (read-only paths in config)")


def data_dir(cfg: dict | None = None) -> Path:
    cfg = cfg or load_config()
    d = ROOT / cfg.get("data_dir", "data/local")
    d.mkdir(parents=True, exist_ok=True)
    return d
