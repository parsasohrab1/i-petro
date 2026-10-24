import numpy as np
import pandapower as pp
import pandapower.networks as pn


def load(name):
    net = getattr(pn, name)(); pp.runpp(net)
    edges = []
    for _, r in net.res_line.join(net.line[["from_bus", "to_bus"]]).iterrows():
        edges.append((int(r.from_bus), int(r.to_bus), abs(float(r.p_from_mw))))
    for _, r in net.res_trafo.join(net.trafo[["hv_bus", "lv_bus"]]).iterrows():
        edges.append((int(r.hv_bus), int(r.lv_bus), abs(float(r.p_hv_mw))))
    n = len(net.bus); idx = {b: i for i, b in enumerate(net.bus.index)}
    inj = np.zeros(n)
    for _, g in net.res_gen.join(net.gen.bus).iterrows(): inj[idx[int(g.bus)]] += g.p_mw
    for _, g in net.res_sgen.join(net.sgen.bus).iterrows(): inj[idx[int(g.bus)]] += g.p_mw
    for _, l in net.res_ext_grid.join(net.ext_grid.bus).iterrows(): inj[idx[int(l.bus)]] += l.p_mw
    for _, l in net.res_load.join(net.load.bus).iterrows(): inj[idx[int(l.bus)]] -= l.p_mw
    edges = [(idx[i], idx[j], w) for i, j, w in edges]
    return n, edges, inj
