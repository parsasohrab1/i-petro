"""Optimisers: furnace excess-oxygen set-point and least-fuel boiler dispatch."""
from . import physics as ph


def furnace_loss_pct(o2, f, t_stack, t_amb):
    return ph.stack_loss_pct(o2, t_stack, t_amb) + ph.RADIATION_LOSS + ph.co_penalty_pct(o2, f.co_o2_min)


def best_o2(f, t_stack, t_amb, safety=0.3):
    """Set-point that minimises total loss; never below the CO knee plus a safety margin."""
    lo = f.co_o2_min + safety
    grid = [lo + 0.05 * i for i in range(int((6.0 - lo) / 0.05) + 1)]
    return min(grid, key=lambda o2: furnace_loss_pct(o2, f, t_stack, t_amb))


def furnace_fuel_mw(duty_mw, loss_pct):
    return duty_mw / (1 - loss_pct / 100.0)


_cache = {}


def dispatch(boilers, demand_tph, step=0.5):
    """Least-fuel split of the steam demand: start every boiler at its minimum and hand out the rest in small
    steps to the boiler whose fuel rises least (exact for convex fuel curves, always meets the demand)."""
    cap_lo, cap_hi = sum(b.min_tph for b in boilers), sum(b.max_tph for b in boilers)
    demand = min(max(demand_tph, cap_lo), cap_hi)
    key = (tuple((b.id, b.min_tph, b.max_tph, b.eta_max, b.curvature) for b in boilers), round(demand / step))
    if key in _cache:
        return list(_cache[key])
    loads = [b.min_tph for b in boilers]
    left = demand - cap_lo
    while left > 1e-9:
        d = min(step, left)
        best, cost = None, None
        for i, b in enumerate(boilers):
            if loads[i] + d > b.max_tph + 1e-9:
                continue
            c = ph.boiler_fuel_mw(loads[i] + d, b) - ph.boiler_fuel_mw(loads[i], b)
            if cost is None or c < cost:
                best, cost = i, c
        if best is None:
            break
        loads[best] += d
        left -= d
    _cache[key] = tuple(loads)
    return loads


def equal_share(boilers, demand_tph):
    """What operators typically do without optimisation: split in proportion to capacity."""
    tot = sum(b.max_tph for b in boilers)
    return [min(max(demand_tph * b.max_tph / tot, b.min_tph), b.max_tph) for b in boilers]


def boiler_fuel_total(boilers, loads):
    return sum(ph.boiler_fuel_mw(x, b) for x, b in zip(loads, boilers))
