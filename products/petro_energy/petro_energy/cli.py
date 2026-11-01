import argparse
from pathlib import Path

from .analyze import analyse
from .dashboard import build
from .model import all_slugs, load_plant
from .simulate import simulate


def build_one(slug, out):
    plant = load_plant(slug)
    rows, truth = simulate(plant)
    res = analyse(plant, rows, truth if plant.furnaces else None)
    path = Path(out) / f"{slug}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build(plant, rows, res, truth), encoding="utf-8")
    return plant, res, path


def main(argv=None):
    ap = argparse.ArgumentParser(prog="petro_energy", description="Fuel and energy optimisation dashboards (TRL 4, synthetic data)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    b = sub.add_parser("build")
    b.add_argument("--plant"); b.add_argument("--all", action="store_true"); b.add_argument("--out", default="reports")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        for s in all_slugs():
            print(s, load_plant(s).name_fa)
        return
    for s in (all_slugs() if a.all or not a.plant else [a.plant]):
        plant, res, path = build_one(s, a.out)
        print(f"{plant.name_fa}: SEC {res['sec_mwh_per_t']:.2f} -> {res['sec_opt_mwh_per_t']:.2f} MWh/t ({res['saving_pct']:.2f}%), alerts {len(res['flags'])} -> {path}")


if __name__ == "__main__":
    main()
