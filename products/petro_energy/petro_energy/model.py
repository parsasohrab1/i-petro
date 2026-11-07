import json
from dataclasses import dataclass, field
from pathlib import Path

PLANTS_DIR = Path(__file__).resolve().parent.parent / "plants"


@dataclass
class Furnace:
    id: str
    duty_mw: float            # absorbed heat duty
    o2_setpoint: float        # % O2 in flue gas the operators run today
    t_stack_c: float          # flue-gas temperature at design
    co_o2_min: float = 1.5    # below this O2 the CO breakthrough risk rises sharply


@dataclass
class Boiler:
    id: str
    min_tph: float
    max_tph: float
    eta_max: float            # best efficiency (fraction) at ~75 % load
    curvature: float = 0.12   # efficiency loss away from the sweet spot


@dataclass
class Plant:
    slug: str
    name_fa: str
    name_en: str
    production_tph: float
    steam_demand_tph: float
    furnaces: list = field(default_factory=list)
    boilers: list = field(default_factory=list)
    fuel_price: float = 1.0
    existing_product: dict = None
    illustrative: bool = True
    notes: str = ""
    kind: str = "process"        # "process" (has fired heaters) or "utility" (steam and power only)

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        fu = [Furnace(**x) for x in d.pop("furnaces")]
        bo = [Boiler(**x) for x in d.pop("boilers")]
        return cls(furnaces=fu, boilers=bo, **d)


def load_plant(slug):
    return Plant.from_dict(json.loads((PLANTS_DIR / f"{slug}.json").read_text(encoding="utf-8")))


def all_slugs():
    return sorted(p.stem for p in PLANTS_DIR.glob("*.json"))
