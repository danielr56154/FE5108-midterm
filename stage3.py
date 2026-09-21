"""Stage 3: French SMB/HML + homemade 12-1 WML.

    python stage3.py
"""

import io
import zipfile
from urllib.request import Request, urlopen

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


def _period_align(s: pd.Series, idx) -> pd.Series:
    s = s.copy()
    s.index = pd.to_datetime(s.index).to_period("M")
    out = s.reindex(idx.to_period("M"))
    out.index = idx
    return out.astype(float)


def french() -> pd.DataFrame:
    path = C.DATA / "ff_japan.csv"
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)

    req = Request(C.FF_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=60) as r:
        raw = r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        txt = z.read(z.namelist()[0]).decode("latin-1")

    rows = []
    for line in txt.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4 or not (parts[0].isdigit() and len(parts[0]) == 6):
            continue
        smb, hml = float(parts[2]), float(parts[3])
        if min(smb, hml) < -99:
            continue
        rows.append((pd.to_datetime(parts[0], format="%Y%m"), smb / 100.0, hml / 100.0))
    out = pd.DataFrame(rows, columns=["date", "smb", "hml"]).set_index("date")
    out.to_csv(path)
    return out


def sort_prices() -> pd.DataFrame:
    path = C.DATA / "sort_px.csv"
    tickers = list(dict.fromkeys(C.TICKERS + C.SORT_EXTRA))
    if path.exists():
        px = pd.read_csv(path, index_col=0, parse_dates=True)
    else:
        px = yf.download(tickers, start=C.MOM_START, interval="1mo",
                         auto_adjust=True, progress=False)["Close"]
        px = px.sort_index()
        px.columns = [str(c) for c in px.columns]
        px = px.dropna(axis=1, how="all")
        px.to_csv(path)
    return px.dropna(axis=1, how="all")


def wml(px: pd.DataFrame) -> pd.Series:
    r = px.pct_change()
    # 12-1: product of months t-12…t-2, formed at t-1, paid at t.
    sig = np.expm1(np.log1p(r).rolling(11).sum()).shift(2)
    out = pd.Series(index=r.index, dtype=float, name="wml")
    for t in r.index:
        s, rt = sig.loc[t], r.loc[t]
        ok = s.notna() & rt.notna()
        s, rt = s[ok], rt[ok]
        if len(s) < 20:
            continue
        lo, hi = s.quantile(0.3), s.quantile(0.7)
        long, short = rt[s >= hi], rt[s <= lo]
        if len(long) >= 5 and len(short) >= 5:
            out.loc[t] = long.mean() - short.mean()
    return out.dropna()


def ts_reg(excess, factors):
    T = len(excess)
    X = np.column_stack([np.ones(T), factors.values])
    y = excess.values
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    k = factors.shape[1]
    s2 = (e ** 2).sum(axis=0) / (T - k - 1)
    se_a = np.sqrt(s2 * np.linalg.inv(X.T @ X)[0, 0])
    alpha_m = b[0]
    out = pd.DataFrame({
        "name": [C.NAMES[t] for t in excess.columns],
        "alpha": alpha_m * 12,
        "t_alpha": alpha_m / se_a,
    }, index=excess.columns)
    out.index.name = "ticker"
    return out, e, alpha_m, k


def grs(alpha_m, resid, f):
    T, N = resid.shape
    f = np.asarray(f, float)
    if f.ndim == 1:
        f = f.reshape(-1, 1)
    K = f.shape[1]
    Sigma = resid.T @ resid / (T - K - 1)
    fbar = f.mean(axis=0)
    omega = (f - fbar).T @ (f - fbar) / T
    q = float(alpha_m @ np.linalg.solve(Sigma, alpha_m))
    shr = float(fbar @ np.linalg.solve(omega, fbar))
    stat = ((T - N - K) / N) * q / (1 + shr)
    p = stage2._f_sf(stat, N, T - N - K)
    return stat, p, N, T - N - K, K


def plot_3b(a0, a1, path):
    order = a0.sort_values().index
    a0, a1 = a0.reindex(order), a1.reindex(order)
    labels = [f"{C.NAMES[t]}  ({t.replace('.T', '')})" for t in order]
    fig, ax = plt.subplots(figsize=(9.5, 11.5))
    y = np.arange(len(order))
    ax.barh(y - 0.18, a0.values, 0.36, label="CAPM")
    ax.barh(y + 0.18, a1.values, 0.36, label="+ SMB HML WML")
    ax.set_yticks(y, labels, fontsize=9)
    ax.axvline(0, color="k", lw=0.7)
    ax.set_xlabel("Annualized α")
    ax.legend(loc="lower right")
    ax.set_title("3b  Alphas before vs after factors")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    stage1._save(fig, path)


def _loud(t):
    return [f"{C.NAMES[i]} ({i.replace('.T', '')})"
            for i in t.index[t.abs() > 2]]


def _join(names):
    return ", ".join(names) if names else "none"


def main() -> None:
    rets, rf, _ = stage1.panel()
    mkt_e = stage2.market(rets.index) - rf
    ff = french()
    px = sort_prices()
    w = wml(px)
    C.EXHIBITS.mkdir(exist_ok=True)

    fac = pd.DataFrame({
        "mkt": mkt_e,
        "smb": _period_align(ff["smb"], rets.index),
        "hml": _period_align(ff["hml"], rets.index),
        "wml": _period_align(w, rets.index),
    })
    ok = fac.notna().all(axis=1)
    rets, rf, fac = rets.loc[ok], rf.loc[ok], fac.loc[ok]
    excess = rets.sub(rf, axis=0)
    span = (
        f"{excess.shape[1]} names, {len(excess)} months  "
        f"{excess.index[0]:%Y-%m} … {excess.index[-1]:%Y-%m}"
    )

    models = [
        ("capm", fac[["mkt"]], "CAPM"),
        ("ff3", fac[["mkt", "smb", "hml"]], "+ SMB HML"),
        ("full", fac[["mkt", "smb", "hml", "wml"]], "+ SMB HML WML"),
    ]
    tables, stats = {}, {}
    for key, F, _ in models:
        tab, resid, alpha_m, _k = ts_reg(excess, F)
        tables[key] = tab
        stats[key] = grs(alpha_m, resid, F.values)

    cmp = pd.DataFrame({"name": [C.NAMES[t] for t in excess.columns]},
                       index=excess.columns)
    cmp.index.name = "ticker"
    for key in ("capm", "ff3", "full"):
        cmp[f"a_{key}"] = tables[key]["alpha"]
        cmp[f"t_{key}"] = tables[key]["t_alpha"]
    cmp = cmp.sort_values("t_capm", key=np.abs, ascending=False)

    p3a = C.EXHIBITS / "3a_factors.txt"
    n_sort = px.shape[1]
    p3a.write_text(
        "Exhibit 3a — factor construction\n"
        f"{span}\n"
        f"sort universe {n_sort} names  (Core 30 + {n_sort - len(C.TICKERS)} extras)\n\n"
        "SMB. Small minus big. Each June, Japanese stocks are independently sorted "
        "on size (big = top 90% of market cap, small = bottom 10%) and book-to-market "
        "(30th/70th percentiles of the big stocks). That 2×3 produces six "
        "value-weighted books. SMB is the average of the three small books minus "
        "the average of the three big books, held until the next June. Here it is "
        "the size factor in the monthly excess-return regression of each of the "
        "30 Core 30 names.\n\n"
        "HML. High minus low. Same six books: the average of the two high B/M "
        "portfolios minus the average of the two low B/M portfolios. Here it is "
        "the value factor on those same 30 names, alongside SMB and TOPIX.\n\n"
        f"WML. Winners minus losers. Each month the {n_sort}-name sort list "
        f"(the 30 test names plus {n_sort - len(C.TICKERS)} other TSE names) "
        "is ranked on the 12–1 return — the product "
        "of monthly returns from t−12 through t−2, skipping t−1. Equal-weight top "
        "30% minus equal-weight bottom 30%, held one month. Here that yen spread "
        "is the momentum factor in the same 30 regressions.\n"
    )
    print(f"=== 3a  {p3a}")

    p3b = C.EXHIBITS / "3b_alphas.txt"
    p3b.write_text(
        "Exhibit 3b — alphas before vs after factors\n"
        f"{span}\n"
        "α annualized; t(α) from the monthly regression\n"
        "capm = Mkt;  ff3 = Mkt+SMB+HML;  full = Mkt+SMB+HML+WML\n\n"
        + cmp.round(3).to_string()
        + "\n"
    )
    print(f"=== 3b  {p3b}")
    png = C.EXHIBITS / "3b_alphas.png"
    plot_3b(tables["capm"]["alpha"], tables["full"]["alpha"], png)
    print(f"=== 3b  {png}")

    def line(key, label):
        Fstat, p, d1, d2, _k = stats[key]
        n_big = int((tables[key]["t_alpha"].abs() > 2).sum())
        return (f"{label:18} |t(α)| > 2: {n_big} of {len(tables[key])}   "
                f"GRS F({d1}, {d2}) = {Fstat:.2f}   p ≈ {p:.3f}")

    capm_l = set(_loud(tables["capm"]["t_alpha"]))
    ff3_l = set(_loud(tables["ff3"]["t_alpha"]))
    full_l = set(_loud(tables["full"]["t_alpha"]))

    def snap(ticker, key):
        row = tables[key].loc[ticker]
        return f"{row['alpha']:.3f} (t={row['t_alpha']:.2f})"

    stories = []
    for t in tables["capm"].sort_values("t_alpha", key=np.abs, ascending=False).index:
        if abs(tables["capm"].loc[t, "t_alpha"]) <= 2:
            continue
        stories.append(
            f"{C.NAMES[t]}: CAPM {snap(t, 'capm')};  "
            f"SMB+HML {snap(t, 'ff3')};  full {snap(t, 'full')}"
        )
    p_capm, p_ff3, p_full = (stats[k][1] for k in ("capm", "ff3", "full"))
    p3c = C.EXHIBITS / "3c_verdict.txt"
    p3c.write_text(
        "Exhibit 3c — which Stage-2 leftovers die?\n"
        f"{span}\n\n"
        + "\n".join(line(k, lab) for k, _, lab in models)
        + "\n\n"
        + "\n".join(stories)
        + "\n\n"
        f"Quiet after SMB+HML:  {_join(sorted(capm_l - ff3_l))}\n"
        f"Still loud in full:   {_join(sorted(capm_l & full_l))}\n"
        f"Newly loud after:     {_join(sorted(full_l - capm_l))}\n\n"
        f"Joint GRS p ≈ {p_capm:.3f} → {p_ff3:.3f} (SMB+HML) → {p_full:.3f} (full). "
        "Value-like leftovers shrink; growth names (semiconductors, HOYA, Sony, "
        "Hitachi) get louder because Japan HML paid a premium in this sample. "
        "Homemade WML does not repair the joint test.\n"
    )
    print(f"=== 3c  {p3c}")
    for k, _, lab in models:
        print("   ", line(k, lab))


if __name__ == "__main__":
    main()
