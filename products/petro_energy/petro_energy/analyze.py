"""KPIs, optimisation savings and fault detection over a simulated history."""
from . import optimize as op
from . import physics as ph


def daily(rows, key):
    out = []
    for d in range(len(rows) // 24):
        vals = [key(r) for r in rows[d * 24:(d + 1) * 24]]
        out.append(sum(vals) / len(vals))
    return out


def analyse(plant, rows, truth=None):
    fuel_now = fuel_opt = prod_tot = 0.0
    eff_series, sec_series, o2_series, o2_opt_series, flags = [], [], [], [], []
    per_furn = {f.id: {"eff": [], "o2": [], "o2_opt": [], "save": 0.0, "fuel": 0.0} for f in plant.furnaces}
    for r in rows:
        f_now = f_opt = 0.0
        effs = []
        for f, fr in zip(plant.furnaces, r["furnaces"]):
            loss = op.furnace_loss_pct(fr["o2"], f, fr["t_stack"], r["t_amb"])
            o2o = op.best_o2(f, fr["t_stack"], r["t_amb"])
            loss_o = op.furnace_loss_pct(o2o, f, fr["t_stack"], r["t_amb"])
            a, b = op.furnace_fuel_mw(fr["duty_mw"], loss), op.furnace_fuel_mw(fr["duty_mw"], loss_o)
            f_now += a
            f_opt += b
            effs.append(100 - loss)
            pf = per_furn[f.id]
            pf["eff"].append(100 - loss); pf["o2"].append(fr["o2"]); pf["o2_opt"].append(o2o)
            pf["save"] += a - b; pf["fuel"] += a
        loads_n = op.equal_share(plant.boilers, r["steam_tph"])
        loads_o = op.dispatch(plant.boilers, r["steam_tph"])
        b_now, b_opt = op.boiler_fuel_total(plant.boilers, loads_n), op.boiler_fuel_total(plant.boilers, loads_o)
        fuel_now += f_now + b_now
        fuel_opt += f_opt + b_opt
        prod_tot += r["prod_tph"]
        eff_series.append(sum(effs) / len(effs) if effs else 0.0)
        sec_series.append((f_now + b_now) / r["prod_tph"])
    n = len(rows)
    sec_daily = [sum(sec_series[d * 24:(d + 1) * 24]) / 24 for d in range(n // 24)]
    flags = []
    for fi, f in enumerate(plant.furnaces):
        o2s = [r["furnaces"][fi]["o2"] for r in rows]
        flags += [(h, f.id, z) for h, z in detect_o2_excursions(o2s)]
        per_furn[f.id]["fouling_c_per_day"] = fouling_slope([r["furnaces"][fi]["t_stack"] for r in rows])
    res = {
        "hours": n,
        "sec_mwh_per_t": fuel_now / prod_tot,
        "sec_opt_mwh_per_t": fuel_opt / prod_tot,
        "saving_pct": 100 * (fuel_now - fuel_opt) / fuel_now,
        "avg_furnace_eff": (sum(eff_series) / n) if plant.furnaces else None,
        "eff_series": eff_series, "sec_series": sec_series, "sec_daily": sec_daily,
        "furnaces": per_furn, "flags": flags,
        "last_loads_now": op.equal_share(plant.boilers, rows[-1]["steam_tph"]),
        "last_loads_opt": op.dispatch(plant.boilers, rows[-1]["steam_tph"]),
    }
    res["detected_leak"] = bool(truth) and any(truth["leak_start"] - 2 <= h <= truth["leak_start"] + truth["leak_hours"] and fid == plant.furnaces[0].id for h, fid, _ in flags)
    return res


def detect_o2_excursions(series, window=72, z_alarm=6.0, min_hours=3):
    """Flags hours where a furnace's O2 sits far above its own recent median (air in-leak, damper or burner fault).
    series: list of O2 readings. Returns [(first_hour, peak_z)] per excursion lasting at least min_hours."""
    out, run, peak = [], 0, 0.0
    for i in range(window, len(series)):
        ref = sorted(series[i - window:i])
        med = ref[len(ref) // 2]
        mad = sorted(abs(x - med) for x in ref)[len(ref) // 2] * 1.4826 or 0.15
        z = (series[i] - med) / mad
        if z > z_alarm:
            run += 1
            peak = max(peak, z)
            if run == min_hours:
                out.append((i - min_hours + 1, peak))
        else:
            run, peak = 0, 0.0
    return out


def fouling_slope(series_t_stack):
    """Least-squares slope of the stack temperature in degC per day (a steady rise means fouled convection section)."""
    n = len(series_t_stack)
    xs = [i / 24.0 for i in range(n)]
    mx, my = sum(xs) / n, sum(series_t_stack) / n
    return sum((x - mx) * (y - my) for x, y in zip(xs, series_t_stack)) / sum((x - mx) ** 2 for x in xs)
