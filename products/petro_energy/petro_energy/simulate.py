"""Deterministic synthetic plant history (hourly). Used for the TRL 4 laboratory validation; NOT plant data."""
import math
import random

HOURS = 24 * 30


def simulate(plant, hours=HOURS, seed=7):
    rnd = random.Random(f"{plant.slug}:{seed}")
    leak_start = int(hours * 0.55)            # injected fault: air in-leak raises O2 on furnace 1 for 18 h
    rows = []
    for h in range(hours):
        day = h / 24.0
        t_amb = 25 + 9 * math.sin(2 * math.pi * (h % 24 - 9) / 24) + rnd.gauss(0, 0.8)
        prod = plant.production_tph * (1 + rnd.gauss(0, 0.03)) * (0.93 if 14 < (h % 168) / 24 < 15 else 1)
        steam = plant.steam_demand_tph * (prod / plant.production_tph) * (1 + rnd.gauss(0, 0.02))
        furn = []
        for k, f in enumerate(plant.furnaces):
            o2 = f.o2_setpoint + rnd.gauss(0, 0.25)
            if k == 0 and leak_start <= h < leak_start + 18:
                o2 += 3.0
            t_stack = f.t_stack_c + 0.9 * day + 0.15 * (t_amb - 25) + rnd.gauss(0, 2)    # slow fouling drift
            duty = f.duty_mw * (prod / plant.production_tph) * (1 + rnd.gauss(0, 0.01))
            furn.append({"id": f.id, "o2": max(0.3, o2), "t_stack": t_stack, "duty_mw": duty})
        rows.append({"h": h, "t_amb": t_amb, "prod_tph": prod, "steam_tph": steam, "furnaces": furn})
    return rows, {"leak_start": leak_start, "leak_hours": 18}
