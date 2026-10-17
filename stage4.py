"""Stage 4: Roll — TOPIX vs MSCI World in yen.

    python stage4.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

import config as C
import stage1
import stage2

plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight"})


def _monthly(s: pd.Series) -> pd.Series:
    s = s.astype(float).copy()
    s.index = pd.to_datetime(s.index).to_period("M")
    return s.groupby(level=0).last()


def _px(ticker, path, name):
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True).squeeze()
    px = yf.download(ticker, start=C.START, end=C.END, interval="1mo",
                     auto_adjust=True, progress=False)["Close"]
    px = px.squeeze().sort_index()
    px.name = name
    px.to_csv(path)
    return px


def world(idx) -> pd.Series:
    urth = _px(C.WORLD, C.DATA / "urth.csv", "urth")
    fx = _px(C.FX, C.DATA / "fx.csv", "fx")
    u, f = _monthly(urth), _monthly(fx)
    if float(f.median()) < 1:
        f = 1.0 / f
    r = (1 + u.pct_change()) * (1 + f.pct_change()) - 1
    out = r.reindex(idx.to_period("M"))
    out.index = idx
    if out.isna().any():
        raise RuntimeError(f"world missing {list(out.index[out.isna()])}")
    if (out.abs() > 0.4).any():
        raise RuntimeError(f"implausible world return: {out[out.abs() > 0.4]}")
    out.name = "world"
    return out.astype(float)


def plot_4b(a0, a1, path):
    order = a0.sort_values().index
    a0, a1 = a0.reindex(order), a1.reindex(order)
    labels = [f"{C.NAMES[t]}  ({t.replace('.T', '')})" for t in order]
    fig, ax = plt.subplots(figsize=(9.5, 11.5))
    y = np.arange(len(order))
    ax.barh(y - 0.18, a0.values, 0.36, label="TOPIX")
    ax.barh(y + 0.18, a1.values, 0.36, label="MSCI World (yen)")
    ax.set_yticks(y, labels, fontsize=9)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_xlabel("Annualized α")
    ax.legend(loc="lower right")
    ax.set_title("4b  Alphas: TOPIX vs world")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    stage1._save(fig, path)


def shift_summary(t_tab, w_tab, prem_t, prem_w) -> str:
    """How far betas, R² and alphas move when the proxy changes."""
    bt, bw = t_tab["beta"], w_tab["beta"]
    da = (w_tab["alpha"] - t_tab["alpha"]).abs()
    db = bw - bt
    big = da.idxmax()
    n = len(bt)
    lines = [
        "How much moves (TOPIX → world)",
        f"mean β            {bt.mean():.3f} → {bw.mean():.3f}   "
        f"lower under world: {int((bw < bt).sum())} of {n}",
        f"corr(β_topix, β_world) = {bt.corr(bw):.2f}   "
        f"rank corr = {bt.rank().corr(bw.rank()):.2f}",
        f"mean R²           {t_tab['r2'].mean():.3f} → {w_tab['r2'].mean():.3f}   "
        f"lower under world: {int((w_tab['r2'] < t_tab['r2']).sum())} of {n}",
        f"mean |Δα|         {da.mean():.3f}   max {da.max():.3f}  "
        f"{C.NAMES[big]} ({big.replace('.T', '')})",
        f"mean β × premium  {bt.mean():.3f} × {prem_t:.3f} = {bt.mean() * prem_t:.3f}   vs   "
        f"{bw.mean():.3f} × {prem_w:.3f} = {bw.mean() * prem_w:.3f}",
        "largest β falls:  " + ", ".join(
            f"{C.NAMES[t]} {bt[t]:.2f}→{bw[t]:.2f}" for t in db.nsmallest(3).index),
        "largest β rises:  " + (
            ", ".join(
                f"{C.NAMES[t]} {bt[t]:.2f}→{bw[t]:.2f}"
                for t in db[db > 0].nlargest(3).index
            ) or "none"
        ),
    ]
    return "\n".join(lines) + "\n"


def _loud(t):
    return [f"{C.NAMES[i]} ({i.replace('.T', '')})"
            for i in t.index[t.abs() > 2]]


def _join(names):
    return ", ".join(names) if names else "none"


def main() -> None:
    rets, rf, _ = stage1.panel()
    topix = stage2.market(rets.index)
    wld = world(rets.index)
    C.EXHIBITS.mkdir(exist_ok=True)

    ok = topix.notna() & wld.notna()
    rets, rf, topix, wld = rets.loc[ok], rf.loc[ok], topix.loc[ok], wld.loc[ok]
    excess = rets.sub(rf, axis=0)
    topix_e, world_e = topix - rf, wld - rf
    span = (
        f"{excess.shape[1]} names, {len(excess)} months  "
        f"{excess.index[0]:%Y-%m} … {excess.index[-1]:%Y-%m}"
    )

    t_tab, t_res, t_a = stage2.capm(excess, topix_e)
    w_tab, w_res, w_a = stage2.capm(excess, world_e)
    t_grs = stage2.grs(t_a, t_res, topix_e.values)
    w_grs = stage2.grs(w_a, w_res, world_e.values)

    cmp = pd.DataFrame({"name": [C.NAMES[t] for t in excess.columns]},
                       index=excess.columns)
    cmp.index.name = "ticker"
    for key, tab in (("topix", t_tab), ("world", w_tab)):
        cmp[f"b_{key}"] = tab["beta"]
        cmp[f"a_{key}"] = tab["alpha"]
        cmp[f"t_{key}"] = tab["t_alpha"]
        cmp[f"r2_{key}"] = tab["r2"]
    cmp = cmp.sort_values("t_topix", key=np.abs, ascending=False)

    def line(lab, tab, grs):
        F, p, d1, d2 = grs
        n_big = int((tab["t_alpha"].abs() > 2).sum())
        return (f"{lab:18} |t(α)| > 2: {n_big} of {len(tab)}   "
                f"GRS F({d1}, {d2}) = {F:.2f}   p ≈ {p:.3f}")

    t_l, w_l = set(_loud(t_tab["t_alpha"])), set(_loud(w_tab["t_alpha"]))
    corr = float(topix_e.corr(world_e))
    move = shift_summary(t_tab, w_tab, topix_e.mean() * 12, world_e.mean() * 12)
    p4a = C.EXHIBITS / "4a_roll.txt"
    p4a.write_text(
        "Exhibit 4a — CAPM under two market proxies\n"
        f"{span}\n"
        f"TOPIX {C.MARKET}   world {C.WORLD} unhedged with {C.FX}\n"
        f"corr(TOPIX, world) = {corr:.2f}   "
        f"mean excess TOPIX {topix_e.mean()*12:.3f}  "
        f"world {world_e.mean()*12:.3f} (ann.)\n"
        "α annualized; t(α) and R² from the monthly regression\n\n"
        + cmp.round(3).to_string()
        + "\n\n"
        + line("TOPIX", t_tab, t_grs) + "\n"
        + line("MSCI World", w_tab, w_grs) + "\n\n"
        f"Loud both:        {_join(sorted(t_l & w_l))}\n"
        f"Loud only TOPIX:  {_join(sorted(t_l - w_l))}\n"
        f"Loud only world:  {_join(sorted(w_l - t_l))}\n\n"
        + move
    )
    print(f"=== 4a  {p4a}")
    print("   ", line("TOPIX", t_tab, t_grs))
    print("   ", line("MSCI World", w_tab, w_grs))
    print(move)

    png = C.EXHIBITS / "4b_roll.png"
    plot_4b(t_tab["alpha"], w_tab["alpha"], png)
    print(f"=== 4b  {png}")


if __name__ == "__main__":
    main()
