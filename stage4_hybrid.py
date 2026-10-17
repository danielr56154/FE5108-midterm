"""stage4_hybrid.py — Stage 4.1: Hybrid portfolio backtest
Rolling 60-month estimation, OOS Oct 2021 – Sep 2026.

Strategies
----------
EW          equal-weighted benchmark (primary clean benchmark)
VW*         value-weighted, current Yahoo caps (LOOK-AHEAD BIASED — illustrative)
LO          100 % long-only tangency
EW+10%LO    90 % EW + 10 % LO
EW+20%LO    80 % EW + 20 % LO
EW+30%LO    70 % EW + 30 % LO
VW*+10%LO   90 % VW* + 10 % LO
VW*+20%LO   80 % VW* + 20 % LO
VW*+30%LO   70 % VW* + 30 % LO

    uv run python stage4_hybrid.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import config as C
import stage1

plt.rcParams.update({"figure.dpi": 120, "savefig.bbox": "tight"})

# ── Constants ─────────────────────────────────────────────────────────────────
WINDOW   = 60
LAMBDAS  = [0.10, 0.20, 0.30]
TC_LIST  = [0, 5, 10, 20]         # bps charged on two-way turnover Σ|Δw|

STRATS = (
    ["EW", "VW*", "LO"]
    + [f"EW+{int(l*100)}%LO" for l in LAMBDAS]
    + [f"VW*+{int(l*100)}%LO" for l in LAMBDAS]
)

PAL = {
    "EW":         "#4C78A8",
    "EW+10%LO":   "#6B99C4",
    "EW+20%LO":   "#92B9DF",
    "EW+30%LO":   "#BAD6F0",
    "VW*":        "#E45756",
    "VW*+10%LO":  "#EB7B7A",
    "VW*+20%LO":  "#F3A9A9",
    "VW*+30%LO":  "#F9D2D2",
    "LO":         "#54A24B",
}


# ── Portfolio weight helpers ──────────────────────────────────────────────────

def _w_ew(cols):
    n = len(cols)
    return pd.Series(1.0 / n, index=cols)


def _w_vw(caps, cols):
    """Current-cap weights.  LOOK-AHEAD BIASED — historical caps unavailable."""
    v = caps.reindex(cols).fillna(caps.median())
    return (v / v.sum()).astype(float)


def _w_lo(rets_win, rf_win):
    """Long-only tangency: maximise Sharpe, w ≥ 0, Σw = 1. Falls back to EW."""
    excess = rets_win.sub(rf_win, axis=0)
    mu_e   = excess.mean().values
    Sigma  = rets_win.cov().values
    n      = len(mu_e)

    def neg_sharpe(w):
        r = w @ mu_e
        v = np.sqrt(w @ Sigma @ w)
        return -r / v if v > 1e-10 else 1e10

    res = minimize(
        neg_sharpe,
        x0=np.ones(n) / n,
        method="SLSQP",
        bounds=[(0.0, None)] * n,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1.0},
        options={"ftol": 1e-12, "maxiter": 2000},
    )
    if not res.success:
        return pd.Series(np.ones(n) / n, index=rets_win.columns)   # EW fallback
    w = np.maximum(res.x, 0.0)
    return pd.Series(w / w.sum(), index=rets_win.columns)


# ── Rolling backtest ──────────────────────────────────────────────────────────

def rolling_backtest(rets, rf, caps):
    """
    Returns
    -------
    w_rec   : dict[str → DataFrame(T_test × N)]   target weights each month
    ret_rec : dict[str → Series(T_test)]           gross monthly portfolio return
    to_rec  : dict[str → Series(T_test)]           one-way monthly turnover
    """
    cols    = rets.columns
    T_test  = len(rets) - WINDOW
    idx     = rets.index[WINDOW:]

    w_rec   = {s: pd.DataFrame(np.nan, index=idx, columns=cols) for s in STRATS}
    ret_rec = {s: pd.Series(np.nan,    index=idx) for s in STRATS}
    to_rec  = {s: pd.Series(np.nan,    index=idx) for s in STRATS}

    w_ew  = _w_ew(cols)
    w_vw  = _w_vw(caps, cols)
    prev  = {s: None for s in STRATS}          # drift weights from prior month
    n_fail = 0

    for i in range(T_test):
        t    = WINDOW + i
        date = idx[i]

        est_r  = rets.iloc[t - WINDOW : t]     # strictly no look-ahead
        est_rf = rf.iloc[t - WINDOW : t]
        r_now  = rets.iloc[t]                  # realised this month

        w_lo = _w_lo(est_r, est_rf)
        if w_lo.sum() < 0.99:
            n_fail += 1

        targets = {
            "EW":  w_ew.copy(),
            "VW*": w_vw.copy(),
            "LO":  w_lo.copy(),
            **{f"EW+{int(l*100)}%LO":  (1 - l) * w_ew  + l * w_lo for l in LAMBDAS},
            **{f"VW*+{int(l*100)}%LO": (1 - l) * w_vw  + l * w_lo for l in LAMBDAS},
        }

        for s, w in targets.items():
            w = w / w.sum()                    # numerical normalisation
            w_rec[s].loc[date] = w.values

            # Two-way turnover = Σ|w_new − w_drift|. Cost = bps × this.
            # First month: buying from cash (w_drift = 0), so turnover = 1.0.
            if prev[s] is None:
                to = 1.0
            else:
                to = float((w - prev[s]).abs().sum())
            to_rec[s].loc[date] = to

            r_p = float(w @ r_now)
            ret_rec[s].loc[date] = r_p

            # Drift weights for next period
            denom = 1.0 + r_p
            prev[s] = w * (1.0 + r_now) / denom if abs(denom) > 1e-10 else w.copy()

    if n_fail:
        print(f"  [warn] LO fallback to EW: {n_fail}/{T_test} months")

    return w_rec, ret_rec, to_rec


# ── Validation ────────────────────────────────────────────────────────────────

def validate(w_rec, ret_rec, to_rec):
    print("\n--- Validation ---")
    ok = True
    for s, wdf in w_rec.items():
        sums = wdf.sum(axis=1)
        if not (sums - 1.0).abs().lt(1e-5).all():
            print(f"  FAIL weight-sum {s}: max dev {(sums-1).abs().max():.2e}")
            ok = False
        if s not in ("VW*",) and "LO" in s or s in ("EW", "LO", "VW*"):
            neg = (wdf < -1e-6).any().any()
            if neg:
                print(f"  FAIL negative weight in {s}")
                ok = False
    # Check identical test-period index
    for s in STRATS:
        assert w_rec[s].index.equals(ret_rec[s].index)
        assert w_rec[s].index.equals(to_rec[s].index)
    # Check number of test months
    assert len(w_rec["EW"]) == 60, f"Expected 60 OOS months, got {len(w_rec['EW'])}"
    if ok:
        print("  All checks passed: weights sum to 1, non-negative, 60 OOS months.")
    return ok


# ── Performance analytics ────────────────────────────────────────────────────

def perf_stats(ret_s, to_s, wdf, rf_test, tc_bps=0):
    tc      = tc_bps / 10_000
    net     = ret_s - tc * to_s
    excess  = net - rf_test.values

    ann_r   = net.mean() * 12
    ann_v   = net.std()  * np.sqrt(12)
    sharpe  = excess.mean() / net.std() * np.sqrt(12) if net.std() > 1e-10 else np.nan

    wealth  = (1 + net).cumprod()
    max_dd  = float((wealth / wealth.cummax() - 1).min())

    avg_to  = float(to_s.iloc[1:].mean())          # exclude month-0 setup
    avg_gx  = float(wdf.abs().sum(axis=1).mean())
    max_w   = float(wdf.max().max())
    eff_n   = float((1.0 / (wdf ** 2).sum(axis=1)).mean())

    return {
        "ann. return":   round(ann_r,  4),
        "ann. vol":      round(ann_v,  4),
        "Sharpe":        round(sharpe, 4),
        "max drawdown":  round(max_dd, 4),
        "avg turnover":  round(avg_to, 4),
        "avg gross exp": round(avg_gx, 4),
        "max weight":    round(max_w,  4),
        "eff. N":        round(eff_n,  2),
    }


def build_stats(ret_rec, to_rec, w_rec, rf_test):
    return pd.DataFrame(
        {s: perf_stats(ret_rec[s], to_rec[s], w_rec[s], rf_test) for s in STRATS}
    ).T


def build_costs(ret_rec, to_rec, rf_test):
    rows = []
    for s in STRATS:
        for bps in TC_LIST:
            tc     = bps / 10_000
            net    = ret_rec[s] - tc * to_rec[s]
            excess = net - rf_test.values
            rows.append({
                "strategy": s,
                "TC (bps)": bps,
                "net ann. return": round(net.mean() * 12, 4),
                "net Sharpe":      round(
                    excess.mean() / net.std() * np.sqrt(12)
                    if net.std() > 1e-10 else np.nan, 4),
            })
    df = pd.DataFrame(rows)
    df = df.set_index(["strategy", "TC (bps)"])
    return df


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_performance(ret_rec, path):
    ew_set  = ["EW"]  + [f"EW+{int(l*100)}%LO"  for l in LAMBDAS] + ["LO"]
    vw_set  = ["VW*"] + [f"VW*+{int(l*100)}%LO" for l in LAMBDAS] + ["LO"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    for ax, strat_set, title in (
        (ax1, ew_set,  "EW-based hybrids"),
        (ax2, vw_set,  "VW*-based hybrids  (VW* = look-ahead biased)"),
    ):
        for s in strat_set:
            w  = (1 + ret_rec[s]).cumprod()
            ax.plot(w.index, w.values,
                    label=s, color=PAL.get(s, "#888"),
                    lw=1.8, ls="--" if s == "LO" else "-")
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("Cumulative wealth (Oct 2021 = 1)")
        ax.legend(fontsize=8.5, loc="upper left")
        ax.grid(linestyle=":", alpha=0.4)

    fig.suptitle("Out-of-sample cumulative wealth  Oct 2021 – Sep 2026", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"==> {path}")


def plot_sharpe(stats_df, path):
    sharpes = stats_df.loc[STRATS, "Sharpe"]
    colors  = [PAL.get(s, "#888") for s in STRATS]

    fig, ax = plt.subplots(figsize=(13, 5))
    x    = np.arange(len(STRATS))
    bars = ax.bar(x, sharpes.values, color=colors, edgecolor="white", width=0.65)
    ax.set_xticks(x, STRATS, rotation=28, ha="right", fontsize=9)
    ax.set_ylabel("Annualized Sharpe ratio")
    ax.set_title("Out-of-sample Sharpe ratios  (0 bps TC)   |   VW* = look-ahead biased",
                 fontsize=10)
    ax.axhline(0, color="k", lw=0.5)
    ax.grid(axis="y", linestyle=":", alpha=0.4)
    for bar, v in zip(bars, sharpes.values):
        if not np.isnan(v):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.01,
                    f"{v:.2f}", ha="center", va="bottom", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"==> {path}")


# ── Research summary ──────────────────────────────────────────────────────────

def print_summary(stats_df, costs_df):
    ew   = stats_df.loc
    lo   = stats_df.loc["LO"]

    print("\n" + "=" * 72)
    print("RESEARCH SUMMARY — Stage 4.1  Hybrid Portfolio Analysis")
    print("OOS: Oct 2021 – Sep 2026  |  Rolling 60-month estimation window")
    print("=" * 72)
    print("\n[Gross performance — 0 bps TC]")
    cols = ["ann. return", "ann. vol", "Sharpe", "max drawdown", "avg turnover", "eff. N"]
    print(stats_df[cols].to_string())

    print("\n[Net Sharpe by transaction cost]")
    print(costs_df["net Sharpe"].unstack("TC (bps)").to_string())

    ew_sh  = stats_df.loc["EW",       "Sharpe"]
    h10_sh = stats_df.loc["EW+10%LO", "Sharpe"]
    h20_sh = stats_df.loc["EW+20%LO", "Sharpe"]
    h30_sh = stats_df.loc["EW+30%LO", "Sharpe"]
    lo_sh  = stats_df.loc["LO",       "Sharpe"]

    print(f"\nSharpe gradient — EW: {ew_sh:.3f}  | +10%: {h10_sh:.3f}"
          f"  | +20%: {h20_sh:.3f}  | +30%: {h30_sh:.3f}  | LO: {lo_sh:.3f}")
    print(f"Turnover/month  — EW: {stats_df.loc['EW','avg turnover']:.2%}"
          f"   LO: {stats_df.loc['LO','avg turnover']:.2%}")

    # ── Summary table ─────────────────────────────────────────────────────────
    ew_sh_20  = costs_df.loc[("EW",       20), "net Sharpe"]
    h10_sh_20 = costs_df.loc[("EW+10%LO", 20), "net Sharpe"]
    h20_sh_20 = costs_df.loc[("EW+20%LO", 20), "net Sharpe"]
    h30_sh_20 = costs_df.loc[("EW+30%LO", 20), "net Sharpe"]
    lo_sh_20  = costs_df.loc[("LO",       20), "net Sharpe"]

    import pandas as pd
    summary = pd.DataFrame({
        "Ann. Return":    {p: f"{stats_df.loc[p, 'ann. return']:.1%}"  for p in stats_df.index},
        "Ann. Vol":       {p: f"{stats_df.loc[p, 'ann. vol']:.1%}"     for p in stats_df.index},
        "Sharpe (gross)": {p: f"{stats_df.loc[p, 'Sharpe']:.3f}"       for p in stats_df.index},
        "Max Drawdown":   {p: f"{stats_df.loc[p, 'max drawdown']:.1%}" for p in stats_df.index},
        "Avg Turnover":   {p: f"{stats_df.loc[p, 'avg turnover']:.1%}" for p in stats_df.index},
        "Sharpe (20bps)": {"EW": f"{ew_sh_20:.3f}", "EW+10%LO": f"{h10_sh_20:.3f}",
                           "EW+20%LO": f"{h20_sh_20:.3f}", "EW+30%LO": f"{h30_sh_20:.3f}",
                           "LO": f"{lo_sh_20:.3f}"},
    })
    summary.index.name = "Portfolio"
    print("\n[Summary Table — Stage 4.1]")
    print(summary.to_string())


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    rets, rf, caps = stage1.panel()
    C.EXHIBITS.mkdir(exist_ok=True)

    test_idx = rets.index[WINDOW:]
    rf_test  = rf.iloc[WINDOW:].reset_index(drop=True)
    rf_test.index = test_idx

    print(f"\nData: {rets.shape[1]} names, {rets.shape[0]} months "
          f"({rets.index[0]:%Y-%m} – {rets.index[-1]:%Y-%m})")
    print(f"Estimation window: {WINDOW} months  |  "
          f"Test period: {test_idx[0]:%Y-%m} – {test_idx[-1]:%Y-%m}  "
          f"({len(test_idx)} months)")
    print("NOTE: VW* uses current Yahoo market caps — LOOK-AHEAD BIASED.\n")

    print("Running rolling backtest …")
    w_rec, ret_rec, to_rec = rolling_backtest(rets, rf, caps)

    validate(w_rec, ret_rec, to_rec)

    stats_df = build_stats(ret_rec, to_rec, w_rec, rf_test)
    costs_df = build_costs(ret_rec, to_rec, rf_test)

    # Monthly returns table
    monthly_df = pd.DataFrame({s: ret_rec[s] for s in STRATS})
    monthly_df.index.name = "date"

    # Weights (long format)
    weight_rows = []
    for s in STRATS:
        for date, row in w_rec[s].iterrows():
            for ticker, w in row.items():
                weight_rows.append({"date": date, "strategy": s,
                                    "ticker": ticker, "weight": round(w, 6)})
    weights_long = pd.DataFrame(weight_rows)

    # Save CSVs
    p_stats   = C.EXHIBITS / "4_hybrid_stats.csv"
    p_costs   = C.EXHIBITS / "4_hybrid_costs.csv"
    p_monthly = C.EXHIBITS / "4_hybrid_monthly.csv"
    p_weights = C.EXHIBITS / "4_hybrid_weights.csv"

    stats_df.to_csv(p_stats)
    costs_df.to_csv(p_costs)
    monthly_df.to_csv(p_monthly)
    weights_long.to_csv(p_weights, index=False)

    for p in (p_stats, p_costs, p_monthly, p_weights):
        print(f"==> {p}")

    # Charts
    plot_performance(ret_rec, C.EXHIBITS / "4_hybrid_performance.png")
    plot_sharpe(stats_df, C.EXHIBITS / "4_hybrid_sharpe.png")

    print_summary(stats_df, costs_df)


if __name__ == "__main__":
    main()
