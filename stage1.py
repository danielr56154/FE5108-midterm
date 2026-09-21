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


if __name__ == "__main__":
    main()
