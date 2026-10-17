"""Stage 2: CAPM time-series, SML, GRS.

    python stage2.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import f as f_dist

import config as C
import stage1

plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight"})


def market(idx) -> pd.Series:
    path = C.DATA / "mkt.csv"
    if path.exists():
        px = pd.read_csv(path, index_col=0, parse_dates=True).squeeze()
    else:
        px = yf.download(C.MARKET, start=C.START, end=C.END, interval="1mo",
                         auto_adjust=True, progress=False)["Close"]
        px = px.squeeze().sort_index()
        px.name = "mkt"
        px.to_csv(path)
    r = px.pct_change().reindex(idx)
    if r.isna().any():
        raise RuntimeError(f"market missing {list(r.index[r.isna()])}")
    if (r.abs() > 0.4).any():
        raise RuntimeError(f"implausible market return: {r[r.abs() > 0.4]}")
    r.name = "mkt"
    return r.astype(float)


def capm(excess, mkt_e):
    T = len(excess)
    X = np.column_stack([np.ones(T), mkt_e.values])
    y = excess.values
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    s2 = (e ** 2).sum(axis=0) / (T - 2)
    se_a = np.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0])
    sst = ((y - y.mean(axis=0)) ** 2).sum(axis=0)
    out = pd.DataFrame({
        "name": [C.NAMES[t] for t in excess.columns],
        "beta": b[1],
        "alpha": b[0] * 12,
        "t_alpha": b[0] / se_a,
        "r2": 1 - (e ** 2).sum(axis=0) / sst,
    }, index=excess.columns)
    out.index.name = "ticker"
    return out, e, b[0]


def grs(alpha_m, resid, f):
    """GRS (1989): MLE residual covariance (÷ T) and exact F tail."""
    T, N = resid.shape
    K = 1
    Sigma = resid.T @ resid / T
    fbar = float(np.mean(f))
    omega = float(np.mean((f - fbar) ** 2))
    q = float(alpha_m @ np.linalg.solve(Sigma, alpha_m))
    stat = ((T - N - K) / N) * q / (1 + fbar ** 2 / omega)
    p = float(f_dist.sf(stat, N, T - N - K))
    return stat, p, N, T - N - K


def sml_fit(beta, mu_e):
    slope, intercept = np.polyfit(beta, mu_e, 1)
    return float(intercept), float(slope)


GROUPS = (
    ("gt", "|t(α)| > 2", "#F58518"),
    ("le", "|t(α)| ≤ 2", "#4C78A8"),
)


def plot_2b(table, mu_e, mkt_ann, path, fit):
    beta = table["beta"]
    sig = table["t_alpha"].abs() > 2
    intercept, slope = fit
    cat = pd.Series(np.where(sig, "gt", "le"), index=beta.index)

    fig, (ax, key) = plt.subplots(
        1, 2, figsize=(12.6, 7.4), gridspec_kw={"width_ratios": [3.05, 1.15]}
    )
    x_lo, x_hi = 0.0, max(float(beta.max()), 1.05) + 0.18
    xs = np.array([x_lo, x_hi])
    ax.plot(xs, intercept + slope * xs, color="#4C78A8", lw=1.4,
            label=f"Fitted    intercept {intercept:.3f}  slope {slope:.3f}")
    ax.plot(xs, mkt_ann * xs, color="0.25", lw=1.4, ls="--",
            label=f"Theory   intercept 0      slope {mkt_ann:.3f}")
    ax.scatter(beta[~sig], mu_e[~sig], s=54, c="#4C78A8", zorder=3,
               edgecolors="white", linewidths=0.7)
    ax.scatter(beta[sig], mu_e[sig], s=54, c="#F58518", zorder=3,
               edgecolors="white", linewidths=0.7)
    ax.scatter([1], [mkt_ann], s=70, marker="D", c="#54A24B", zorder=4,
               edgecolors="white", linewidths=0.7, label="TOPIX")

    halo = [pe.withStroke(linewidth=2.8, foreground="white")]
    xlim = (x_lo, x_hi)
    ypad = 0.04
    ylim = (min(0.0, float(mu_e.min())) - ypad, float(mu_e.max()) + ypad)
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    dx, dy = stage1._spread_tickers(beta.values, mu_e.values, xlim, ylim)
    xspan, yspan = xlim[1] - xlim[0], ylim[1] - ylim[0]
    for t, ox, oy in zip(beta.index, dx, dy):
        moved = np.hypot(ox / xspan, oy / yspan)
        ax.annotate(
            t.replace(".T", ""), (beta[t], mu_e[t]),
            xytext=(beta[t] + ox, mu_e[t] + oy), textcoords="data",
            fontsize=8, ha="center", va="center", color="#222", zorder=4,
            path_effects=halo,
            arrowprops=(
                dict(arrowstyle="-", color="0.7", lw=0.45, shrinkA=0, shrinkB=3)
                if moved > 0.035 else None
            ),
        )
    ax.set_xlabel(r"$\hat\beta_i$  vs TOPIX")
    ax.set_ylabel("Average excess return  (annualized)")
    ax.set_title("2b  Empirical SML")
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.92)
    ax.grid(linestyle=":", alpha=0.35)

    key.set_xlim(0, 1)
    key.axis("off")
    key.set_title("Ticker  ·  name", fontsize=10, pad=8)
    rows = []
    for q, title, color in GROUPS:
        members = sorted(cat[cat == q].index.tolist())
        rows.append((f"{title}  ({len(members)})", "", color, True))
        rows.extend((t.replace(".T", ""), C.NAMES[t], color, False) for t in members)
    key.set_ylim(-len(rows) + 0.4, 0.8)
    for i, (code, name, color, header) in enumerate(rows):
        y = -i
        if header:
            key.text(0.02, y, code, fontsize=8.5, fontweight="bold",
                     color=color, va="center")
        else:
            key.scatter([0.06], [y], s=26, c=color, edgecolors="white",
                        linewidths=0.5, zorder=3, clip_on=False)
            key.text(0.13, y, code, fontsize=8.5, color="#222", va="center",
                     fontfamily="monospace")
            key.text(0.38, y, name, fontsize=8.5, color="#222", va="center")
    stage1._save(fig, path)


def main() -> None:
    rets, rf, _ = stage1.panel()
    mkt = market(rets.index)
    C.EXHIBITS.mkdir(exist_ok=True)
    excess = rets.sub(rf, axis=0)
    mkt_e = mkt - rf

    table, resid, alpha_m = capm(excess, mkt_e)
    table = table.sort_values("t_alpha", key=np.abs, ascending=False)
    n_big = int((table["t_alpha"].abs() > 2).sum())
    F, p, d1, d2 = grs(alpha_m, resid, mkt_e.values)
    mu_e = excess.mean() * 12
    mkt_ann = float(mkt_e.mean() * 12)
    fit = sml_fit(table["beta"].reindex(mu_e.index).values, mu_e.values)

    p2a = C.EXHIBITS / "2a_capm.txt"
    p2a.write_text(
        "Exhibit 2a — CAPM  Ri−Rf = α + β (RM−Rf) + ε\n"
        f"market {C.MARKET}  (Daiwa full-TOPIX ETF)\n"
        f"{rets.shape[1]} names, {rets.shape[0]} months  "
        f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}\n"
        f"α annualized; t(α) and R² from the monthly regression\n\n"
        + table.round(3).to_string()
        + "\n"
    )
    print(f"=== 2a  {p2a}")

    p2c = C.EXHIBITS / "2c_grs.txt"
    p2c.write_text(
        "Exhibit 2c — all α = 0?\n"
        f"{rets.shape[1]} names, {rets.shape[0]} months  "
        f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}\n\n"
        f"|t(α)| > 2: {n_big} of {len(table)}   "
        f"(≈{0.05 * len(table):.1f} expected by chance if independent)\n"
        f"GRS F({d1}, {d2}) = {F:.2f}   p ≈ {p:.3f}\n"
    )
    print(f"=== 2c  {p2c}")
    print(f"|t(α)| > 2: {n_big}/{len(table)}   GRS F({d1},{d2})={F:.2f} p≈{p:.3f}")

    p2d = C.EXHIBITS / "2d_sml.txt"
    p2d.write_text(
        "Exhibit 2d — fitted SML vs theory (annualized)\n"
        f"market {C.MARKET}  (Daiwa full-TOPIX ETF)\n"
        f"{rets.shape[1]} names, {rets.shape[0]} months  "
        f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}\n\n"
        f"theory     intercept 0.000   slope {mkt_ann:.3f}\n"
        f"fitted     intercept {fit[0]:.3f}   slope {fit[1]:.3f}\n"
    )
    print(f"=== 2d  {p2d}")
    print(f"SML fitted intercept {fit[0]:.3f}  slope {fit[1]:.3f}  "
          f"theory slope {mkt_ann:.3f}")

    p2b = C.EXHIBITS / "2b_sml.png"
    plot_2b(table, mu_e.reindex(table.index), mkt_ann, p2b, fit)
    print(f"=== 2b  {p2b}")


if __name__ == "__main__":
    main()
