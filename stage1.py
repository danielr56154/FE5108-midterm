"""Stage 1: download (cached), 1a table, 1b/1c figures.

    python stage1.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

import config as C

plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight"})

QUADS = {
    "ll": ("Long both halves", "#4C78A8"),
    "sl": ("Short then long", "#54A24B"),
    "ls": ("Long then short", "#F58518"),
    "ss": ("Short both halves", "#9D755D"),
}


def panel():
    C.DATA.mkdir(exist_ok=True)

    path = C.DATA / "prices.csv"
    if path.exists():
        px = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        px = yf.download(C.TICKERS, start=C.START, interval="1mo",
                         auto_adjust=True, progress=False)["Close"]
        px = px.sort_index()
        px.columns = [str(c) for c in px.columns]
        px = px[C.TICKERS]
        thin = [c for c in px.columns if px[c].notna().sum() < C.MIN_OBS]
        if thin:
            raise RuntimeError(f"under 96 months: {thin}")
        px.to_csv(path)

    path = C.DATA / "rf.csv"
    if path.exists():
        rf = pd.read_csv(path, index_col=0, parse_dates=True).squeeze()
        rf.name = "rf"
    else:
        raw = pd.read_csv(C.RF_URL)
        raw.columns = ["date", "pa"]
        rf = pd.to_numeric(raw.set_index(pd.to_datetime(raw["date"]))["pa"],
                           errors="coerce") / 100.0 / 12.0
        rf.name = "rf"
        rf.to_csv(path)

    path = C.DATA / "caps.csv"
    if path.exists():
        caps = pd.read_csv(path, index_col=0).squeeze()
    else:
        rows = {}
        for t in px.columns:
            info = yf.Ticker(t).fast_info
            cap = getattr(info, "market_cap", None)
            if cap is None:
                cap = yf.Ticker(t).info.get("marketCap")
            rows[t] = cap
        caps = pd.Series(rows, dtype="float64", name="cap")
        caps.to_csv(path)

    rets = px.pct_change().dropna(how="any")
    rf.index = rf.index.to_period("M")
    rf = rf.reindex(rets.index.to_period("M"))
    rf.index = rets.index
    if rf.isna().any():
        rf = rf.interpolate(limit_direction="both")
    caps = caps.reindex(rets.columns).astype(float)
    if caps.isna().any():
        caps = caps.fillna(caps.median())
    return rets, rf.astype(float), caps


def tangency(rets, rf) -> pd.Series:
    mu_e = rets.sub(rf, axis=0).mean().values
    w = np.linalg.solve(rets.cov().values, mu_e)
    return pd.Series(w / w.sum(), index=rets.columns, name="tangency")


def long_only(rets, rf) -> pd.Series:
    """Max-Sharpe with w >= 0: min y'Σy s.t. μe'y = 1, y >= 0, then w = y / Σy."""
    mu_e = rets.sub(rf, axis=0).mean().values * 12
    S = rets.cov().values * 12
    n = len(mu_e)
    y0 = np.where(mu_e > 0, 1.0, 0.0)
    y0 /= mu_e @ y0
    res = minimize(lambda y: y @ S @ y, y0, jac=lambda y: 2 * S @ y,
                   bounds=[(0, None)] * n, method="SLSQP",
                   constraints=[{"type": "eq", "fun": lambda y: mu_e @ y - 1,
                                 "jac": lambda y: mu_e}],
                   options={"ftol": 1e-12, "maxiter": 1000})
    if not res.success:
        raise RuntimeError(f"long-only tangency: {res.message}")
    w = np.clip(res.x, 0, None)
    return pd.Series(w / w.sum(), index=rets.columns, name="long_only")


def shrunk(rets, rf):
    """Tangency on Bayes-Stein μ (Jorion 1986) and Ledoit-Wolf (2004) Σ.

    Returns weights, LW intensity δ (weight on the scaled-identity target)
    and Bayes-Stein intensity φ (weight on the minimum-variance mean).
    """
    X = rets.sub(rf, axis=0).values
    T, N = X.shape
    mu = X.mean(axis=0)
    Xc = X - mu

    S_ml = Xc.T @ Xc / T
    F = np.trace(S_ml) / N * np.eye(N)
    d2 = np.sum((S_ml - F) ** 2) / N
    b2 = sum(np.sum((np.outer(x, x) - S_ml) ** 2) for x in Xc) / N / T**2
    delta = min(b2, d2) / d2
    sigma = delta * F + (1 - delta) * S_ml

    S_j = Xc.T @ Xc / (T - N - 2)
    Si = np.linalg.inv(S_j)
    one = np.ones(N)
    mu0 = one @ Si @ mu / (one @ Si @ one)
    d = mu - mu0
    phi = (N + 2) / ((N + 2) + T * d @ Si @ d)
    mu_bs = (1 - phi) * mu + phi * mu0

    w = np.linalg.solve(sigma, mu_bs)
    return pd.Series(w / w.sum(), index=rets.columns, name="shrunk"), delta, phi


def oos(rets, rf, w_val, window=60) -> pd.DataFrame:
    """Rolling out-of-sample test: estimate on the trailing window, hold one month."""
    rules = {
        "Value (today's caps)": lambda r, f: w_val,
        "Equal 1/N": lambda r, f: pd.Series(1 / r.shape[1], index=r.columns),
        "Tangency": tangency,
        "Long-only tangency": long_only,
        "Shrunk tangency": lambda r, f: shrunk(r, f)[0],
    }
    rows = {}
    for name, rule in rules.items():
        port, gross, turn, prev = [], [], [], None
        for t in range(window, len(rets)):
            w = rule(rets.iloc[t - window:t], rf.iloc[t - window:t])
            w = w.reindex(rets.columns).values
            port.append(rets.iloc[t].values @ w - rf.iloc[t])
            gross.append(np.abs(w).sum())
            if prev is not None:
                turn.append(np.abs(w - prev).sum())
            prev = w
        p = np.array(port)
        rows[name] = {
            "mean_ex": p.mean() * 12,
            "vol": p.std(ddof=1) * np.sqrt(12),
            "sharpe": p.mean() / p.std(ddof=1) * np.sqrt(12),
            "worst_month": p.min(),
            "avg_gross": np.mean(gross),
            "max_gross": np.max(gross),
            "avg_turnover": np.mean(turn),
        }
    return pd.DataFrame(rows).T


def book_stats(books, rets, rf) -> pd.DataFrame:
    """In-sample Sharpe, concentration and half-sample stability of each book."""
    excess = rets.sub(rf, axis=0)
    half = len(rets) // 2
    rows = {}
    for name, (w, rule) in books.items():
        p = excess.values @ w.reindex(rets.columns).values
        if rule is None:
            corr = np.nan
        else:
            a = rule(rets.iloc[:half], rf.iloc[:half])
            b = rule(rets.iloc[half:], rf.iloc[half:])
            corr = float(a.corr(b))
        rows[name] = {
            "sharpe_in": p.mean() / p.std(ddof=1) * np.sqrt(12),
            "gross": w.abs().sum(),
            "max_w": w.max(),
            "min_w": w.min(),
            "n_short": int((w < -1e-6).sum()),
            "n_held": int((w.abs() > 1e-3).sum()),
            "half_corr": corr,
        }
    return pd.DataFrame(rows).T


def plot_1d(books, path):
    w_val = books["Value"]
    order = w_val.sort_values(ascending=True).index
    labels = [f"{C.NAMES[t]}  ({t.replace('.T', '')})" for t in order]
    names = ["Tangency", "Shrunk tangency", "Long-only tangency", "Value"]
    colors = ["#BBBBBB", "#4C78A8", "#54A24B", "#F58518"]

    fig, ax = plt.subplots(figsize=(9.5, 12.5))
    y = np.arange(len(order))
    h = 0.2
    for k, (n, c) in enumerate(zip(names, colors)):
        ax.barh(y + (k - 1.5) * h, books[n].reindex(order).values, h, label=n, color=c)
    ax.set_yticks(y, labels, fontsize=9)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_xlabel("Weight")
    ax.legend(loc="lower right")
    ax.set_title("1d  Taming the tangency portfolio")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    _save(fig, path)


def summary(rets, rf) -> pd.DataFrame:
    excess = rets.sub(rf, axis=0)
    out = pd.DataFrame({
        "name": [C.NAMES[t] for t in rets.columns],
        "mean": rets.mean() * 12,
        "vol": rets.std() * np.sqrt(12),
        "sharpe": excess.mean() / rets.std() * np.sqrt(12),
    })
    out.index.name = "ticker"
    return out


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_1b(w_tan, w_val, path):
    w_val = w_val.reindex(w_tan.index)
    order = w_val.sort_values(ascending=True).index
    w_tan, w_val = w_tan.reindex(order), w_val.reindex(order)
    labels = [f"{C.NAMES[t]}  ({t.replace('.T', '')})" for t in order]

    fig, ax = plt.subplots(figsize=(9.5, 11.5))
    y = np.arange(len(order))
    ax.barh(y - 0.18, w_tan.values, 0.36, label="Tangency")
    ax.barh(y + 0.18, w_val.values, 0.36, label="Value")
    ax.set_yticks(y, labels, fontsize=9)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_xlabel("Weight")
    ax.legend(loc="lower right")
    ax.set_title("1b  Tangency vs value weights")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    _save(fig, path)


def plot_1c(rets, rf, path) -> float:
    half = len(rets) // 2
    a = tangency(rets.iloc[:half], rf.reindex(rets.index[:half]))
    b = tangency(rets.iloc[half:], rf.reindex(rets.index[half:]))
    corr = float(a.corr(b))
    cat = pd.Series(
        np.where(a >= 0, np.where(b >= 0, "ll", "ls"),
                 np.where(b >= 0, "sl", "ss")),
        index=a.index,
    )
    colors = cat.map({q: c for q, (_, c) in QUADS.items()})

    fig, (ax, key) = plt.subplots(
        1, 2, figsize=(12.6, 7.4), gridspec_kw={"width_ratios": [3.05, 1.15]}
    )
    ax.axhline(0, color="k", lw=0.6)
    ax.axvline(0, color="k", lw=0.6)
    ax.axline((0, 0), slope=1, color="0.35", lw=0.8, zorder=1)
    ax.scatter(a, b, s=54, c=colors, zorder=3, edgecolors="white", linewidths=0.7)
    ax.set_xlim(a.min() - 0.22, a.max() + 0.18)
    ax.set_ylim(b.min() - 0.06, b.max() + 0.055)

    halo = [pe.withStroke(linewidth=2.8, foreground="white")]
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    xspan, yspan = xlim[1] - xlim[0], ylim[1] - ylim[0]
    dx, dy = _spread_tickers(a.values, b.values, xlim, ylim)
    for t, ox, oy in zip(a.index, dx, dy):
        moved = np.hypot(ox / xspan, oy / yspan)
        ax.annotate(
            t.replace(".T", ""), (a[t], b[t]),
            xytext=(a[t] + ox, b[t] + oy), textcoords="data",
            fontsize=8, ha="center", va="center", color="#222", zorder=4,
            path_effects=halo,
            arrowprops=(
                dict(arrowstyle="-", color="0.7", lw=0.45, shrinkA=0, shrinkB=3)
                if moved > 0.035 else None
            ),
        )
    ax.set_xlabel("First-half tangency  (2016–21)")
    ax.set_ylabel("Second-half tangency  (2021–26)")
    ax.set_title(f"1c  Half-sample weights  (corr = {corr:.2f})")
    ax.grid(linestyle=":", alpha=0.35)

    key.set_xlim(0, 1)
    key.axis("off")
    key.set_title("Ticker  ·  name", fontsize=10, pad=8)
    rows = []
    for q, (title, color) in QUADS.items():
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
    _save(fig, path)
    return corr


def _spread_tickers(xs, ys, xlim, ylim, steps=150):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    xspan, yspan = xlim[1] - xlim[0], ylim[1] - ylim[0]
    px = (xs - xlim[0]) / xspan
    py = (ys - ylim[0]) / yspan
    posx = px + np.where(px >= 0.5, 0.028, -0.028)
    posy = py + np.where(py >= 0.5, 0.022, -0.022)
    for _ in range(steps):
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                dx, dy = posx[i] - posx[j], posy[i] - posy[j]
                if abs(dx) < 0.062 and abs(dy) < 0.044:
                    sx = 1.0 if dx == 0 else np.sign(dx)
                    sy = 1.0 if dy == 0 else np.sign(dy)
                    posx[i] += 0.0035 * sx
                    posx[j] -= 0.0035 * sx
                    posy[i] += 0.0028 * sy
                    posy[j] -= 0.0028 * sy
    return (posx - px) * xspan, (posy - py) * yspan


def main() -> None:
    rets, rf, caps = panel()
    C.EXHIBITS.mkdir(exist_ok=True)
    print(f"{rets.shape[1]} names, {rets.shape[0]} months  "
          f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}")
    print(f"rf monthly  mean {rf.mean():.4%}  min {rf.min():.4%}")

    table = summary(rets, rf).sort_values("sharpe", ascending=False).round(3)
    p1a = C.EXHIBITS / "1a_summary.txt"
    p1a.write_text(
        "Exhibit 1a — annualized mean, vol, Sharpe (yen call money)\n"
        f"{rets.shape[1]} names, {rets.shape[0]} months  "
        f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}\n\n"
        + table.to_string()
        + "\n"
    )
    print(f"=== 1a  {p1a}")

    w_tan = tangency(rets, rf)
    p1b = C.EXHIBITS / "1b_weights.png"
    plot_1b(w_tan, caps / caps.sum(), p1b)
    extreme = w_tan.abs().idxmax()
    print(f"=== 1b  {p1b}")
    print(f"largest |tangency|: {extreme} {w_tan[extreme]:+.0%}")

    p1c = C.EXHIBITS / "1c_subsample.png"
    corr = plot_1c(rets, rf, p1c)
    print(f"=== 1c  {p1c}")
    print(f"corr(first half, second half) = {corr:.2f}")

    w_val = caps / caps.sum()
    w_val.name = "value"
    w_sh, delta, phi = shrunk(rets, rf)
    books = {
        "Value": (w_val, None),
        "Equal 1/N": (pd.Series(1 / len(w_val), index=w_val.index), None),
        "Tangency": (w_tan, tangency),
        "Long-only tangency": (long_only(rets, rf), long_only),
        "Shrunk tangency": (w_sh, lambda r, f: shrunk(r, f)[0]),
    }
    p1d = C.EXHIBITS / "1d_tamed.png"
    plot_1d({k: w for k, (w, _) in books.items()}, p1d)
    stats = book_stats(books, rets, rf)
    weights = pd.DataFrame({k: w for k, (w, _) in books.items()})
    weights.insert(0, "name", [C.NAMES[t] for t in weights.index])
    weights = weights.sort_values("Value", ascending=False)
    p1d_txt = C.EXHIBITS / "1d_tamed.txt"
    p1d_txt.write_text(
        "Exhibit 1d — taming the tangency portfolio (full sample)\n"
        f"{rets.shape[1]} names, {rets.shape[0]} months  "
        f"{rets.index[0]:%Y-%m} … {rets.index[-1]:%Y-%m}\n"
        "Long-only: max Sharpe with w >= 0.  Shrunk: Bayes-Stein mean (Jorion 1986) "
        "and Ledoit-Wolf (2004) covariance, shorts allowed.\n"
        f"Ledoit-Wolf weight on identity target δ = {delta:.2f};  "
        f"Bayes-Stein weight on min-variance mean φ = {phi:.2f}\n"
        "sharpe_in is in-sample (flatters the optimized books).  "
        "half_corr = corr of weights re-estimated on each 60-month half.\n\n"
        + stats.round(3).to_string()
        + "\n\nWeights\n\n"
        + weights.round(3).to_string()
        + "\n"
    )
    print(f"=== 1d  {p1d}")
    print(f"=== 1d  {p1d_txt}")
    print(f"δ = {delta:.2f}  φ = {phi:.2f}")
    print(stats.round(3).to_string())

    table_oos = oos(rets, rf, w_val)
    p1e = C.EXHIBITS / "1e_oos.txt"
    p1e.write_text(
        "Exhibit 1e — out-of-sample test of the books\n"
        "Each month, estimate on the trailing 60 months, hold the next month.\n"
        f"{len(rets) - 60} out-of-sample months  "
        f"{rets.index[60]:%Y-%m} … {rets.index[-1]:%Y-%m}\n"
        "Excess returns over call money, annualized.  Value uses today's caps "
        "throughout (look-ahead).\n"
        "gross = sum |w|;  turnover = sum |w_t − w_{t−1}| per month "
        "(ignores drift, so value and 1/N show 0).\n\n"
        + table_oos.round(3).to_string()
        + "\n"
    )
    print(f"=== 1e  {p1e}")
    print(table_oos.round(3).to_string())


if __name__ == "__main__":
    main()
