"""Combustion and boiler relations used by the KPIs and the optimiser."""
import math

A2_GAS, B_GAS = 0.66, 0.009   # Siegert constants for natural gas (stack-loss method)
RADIATION_LOSS = 1.5          # % of fuel energy lost through the casing, assumed constant
STEAM_MW_PER_TPH = 0.7        # about 2.5 GJ of heat per tonne of steam raised


def excess_air_pct(o2):
    """Excess air (%) from flue-gas oxygen (% dry): lambda = 21 / (21 - O2)."""
    return (21.0 / (21.0 - o2) - 1.0) * 100.0


def stack_loss_pct(o2, t_stack, t_amb):
    """Siegert dry-flue-gas loss, % of fuel energy."""
    return max(0.0, (t_stack - t_amb) * (A2_GAS / (21.0 - o2) + B_GAS))


def furnace_efficiency(o2, t_stack, t_amb):
    return 100.0 - stack_loss_pct(o2, t_stack, t_amb) - RADIATION_LOSS


def co_penalty_pct(o2, o2_min):
    """Incomplete-combustion penalty that rises steeply below the safe O2 level."""
    knee = o2_min + 0.4
    return 0.0 if o2 >= knee else 3.0 * (math.exp((knee - o2) / 0.35) - 1.0) + 0.2


def boiler_eta(x, b):
    """Efficiency (fraction) at steam load x t/h: peaks near 75 % of max load."""
    load = x / b.max_tph
    return max(0.55, b.eta_max - b.curvature * (load - 0.75) ** 2)


def boiler_fuel_mw(x, b):
    return STEAM_MW_PER_TPH * x / boiler_eta(x, b) if x > 0 else 0.0
