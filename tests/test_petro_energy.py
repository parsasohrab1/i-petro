import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "products" / "petro_energy"))

from petro_energy import optimize as op, physics as ph          # noqa: E402
from petro_energy.analyze import analyse, detect_o2_excursions, fouling_slope   # noqa: E402
from petro_energy.cli import build_one                          # noqa: E402
from petro_energy.model import all_slugs, load_plant            # noqa: E402
from petro_energy.simulate import simulate                      # noqa: E402


def test_excess_air_and_efficiency_fall_as_oxygen_rises():
    assert round(ph.excess_air_pct(3.0)) == 17
    effs = [ph.furnace_efficiency(o, 190, 25) for o in (1, 2, 3, 4, 6)]
    assert effs == sorted(effs, reverse=True)


def test_best_o2_respects_co_limit_and_beats_current_setpoint():
    f = load_plant("arvand").furnaces[0]
    o2 = op.best_o2(f, f.t_stack_c, 25)
    assert o2 >= f.co_o2_min + 0.3 - 1e-9
    assert op.furnace_loss_pct(o2, f, f.t_stack_c, 25) < op.furnace_loss_pct(f.o2_setpoint, f, f.t_stack_c, 25)
    assert ph.co_penalty_pct(f.co_o2_min - 0.5, f.co_o2_min) > 1.0     # starving the burner is expensive


def test_dispatch_meets_demand_within_bounds_and_uses_less_fuel_than_equal_share():
    p = load_plant("bandar_imam")
    for demand in (0.5, 0.62, 0.8):
        d = demand * sum(b.max_tph for b in p.boilers)
        loads = op.dispatch(p.boilers, d)
        assert abs(sum(loads) - d) < 1e-6
        assert all(b.min_tph - 1e-9 <= x <= b.max_tph + 1e-9 for x, b in zip(loads, p.boilers))
        assert op.boiler_fuel_total(p.boilers, loads) <= op.boiler_fuel_total(p.boilers, op.equal_share(p.boilers, d)) + 1e-9


def test_simulation_is_deterministic():
    p = load_plant("karoun")
    assert simulate(p)[0][100] == simulate(p)[0][100]


def test_injected_air_leak_is_found_on_the_right_furnace_and_no_false_alarms():
    p = load_plant("arvand")
    rows, truth = simulate(p)
    res = analyse(p, rows, truth)
    assert res["detected_leak"]
    assert all(fid == p.furnaces[0].id for _, fid, _ in res["flags"])
    quiet = [r["furnaces"][1]["o2"] for r in rows]                      # furnace without the fault
    assert detect_o2_excursions(quiet) == []


def test_fouling_slope_matches_the_simulated_drift():
    p = load_plant("karoun")
    rows, _ = simulate(p)
    slope = fouling_slope([r["furnaces"][0]["t_stack"] for r in rows])
    assert 0.6 < slope < 1.3                                           # simulated drift is about 0.9 degC/day


def test_every_plant_builds_a_labelled_dashboard(tmp_path):
    slugs = all_slugs()
    assert len(slugs) >= 16 and {"arvand", "bandar_imam", "mobin"} <= set(slugs)
    for s in slugs:
        plant, res, path = build_one(s, tmp_path)
        html = path.read_text(encoding="utf-8")
        assert plant.name_fa in html and "داده‌ی ساختگی" in html and "TRL 4" in html
        assert res["sec_opt_mwh_per_t"] <= res["sec_mwh_per_t"] + 1e-9
        assert plant.illustrative


def test_utility_plants_have_no_furnaces_but_still_dispatch_boilers():
    p = load_plant("mobin")
    assert p.kind == "utility" and not p.furnaces
    rows, _ = simulate(p)
    assert analyse(p, rows)["avg_furnace_eff"] is None
