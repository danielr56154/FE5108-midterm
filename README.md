# FE 5108 midterm — Track A

Japan TOPIX Core 30, yen, monthly, Oct 2016 – Sep 2026. Assignment and FAQ: `[midterm_project_handout.pdf](midterm_project_handout.pdf)`.

The universe is **today’s** Core 30 (JPX Oct 2025) backfilled ten years, so failed and delisted firms are missing. Average returns, Sharpes and CAPM alphas are biased up. Equal-weight (1/N) of these 30 names avoids using today’s market caps as weights; it does not undo survivorship.

Python 3.11+. `pip install -r requirements.txt` then `python run_all.py`.

## Where to look


| Path                               | What it is                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------- |
| `[exhibits/](exhibits/)`           | Every table and chart the report will use.                                              |
| `[documentation/](documentation/)` | Documentation about what each stage actually did, and the data choices.                 |
| `[data/](data/)`                   | Cached CSVs; one row per file below.                                                    |
| `[config.py](config.py)`           | Tickers, `START`/`END`/`LAST`, market tickers.                                          |
| `stage1.py` … `stage4.py`, `stage4_hybrid.py` | Code for that stage. `[run_all.py](run_all.py)` runs them in order.                     |

## Packages

Pinned in `[requirements.txt](requirements.txt)`: `numpy==2.5.3`, `pandas==3.0.6`, `matplotlib==3.11.2`, `yfinance==1.7.0`, `scipy==1.18.1`.

## Data files

Yahoo downloads use `start=2016-09-01` and exclusive `end=2026-10-01`, so the last complete month is Sep 2026. Cached files are reused if present.

| File | Source |
| --- | --- |
| `[data/prices.csv](data/prices.csv)` | Yahoo Finance monthly adjusted close, 30 names |
| `[data/caps.csv](data/caps.csv)` | Yahoo `fast_info.market_cap` (current yen caps, look-ahead) |
| `[data/rf.csv](data/rf.csv)` | FRED `IRSTCI01JPM156N` yen overnight call, annual % / (100 × 12) |
| `[data/mkt.csv](data/mkt.csv)` | Yahoo Daiwa TOPIX ETF `1305.T` monthly adjusted close |
| `[data/ff_japan.csv](data/ff_japan.csv)` | Ken French Japan 3 Factors (USD); SMB and HML only |
| `[data/sort_px.csv](data/sort_px.csv)` | Yahoo monthly adjusted close, 78 TSE names for homemade WML |
| `[data/urth.csv](data/urth.csv)` | Yahoo iShares MSCI World ETF `URTH` (USD) |
| `[data/fx.csv](data/fx.csv)` | Yahoo `JPY=X` (USDJPY), for unhedged World-in-yen |




## Exhibits

- **1a** `[1a_summary.txt](exhibits/1a_summary.txt)` — mean, vol, Sharpe  
- **1b** `[1b_weights.png](exhibits/1b_weights.png)` — tangency vs value weights  
- **1c** `[1c_subsample.png](exhibits/1c_subsample.png)` — first-half vs second-half tangency  
- **1d** `[1d_tamed.txt](exhibits/1d_tamed.txt)` / `[1d_tamed.png](exhibits/1d_tamed.png)` — long-only and shrunk tangency vs value, 1/N, raw tangency  
- **1e** `[1e_oos.txt](exhibits/1e_oos.txt)` — rolling 60-month out-of-sample test of those books  
- **2a** `[2a_capm.txt](exhibits/2a_capm.txt)` — CAPM β, α, *t*(α), R²  
- **2b** `[2b_sml.png](exhibits/2b_sml.png)` — empirical SML  
- **2c** `[2c_grs.txt](exhibits/2c_grs.txt)` — joint α = 0  
- **2d** `[2d_sml.txt](exhibits/2d_sml.txt)` — fitted SML vs theory  
- **3a** `[3a_factors.txt](exhibits/3a_factors.txt)` — SMB, HML, WML construction  
- **3b** `[3b_alphas.txt](exhibits/3b_alphas.txt)` / `[3b_alphas.png](exhibits/3b_alphas.png)` — alphas before vs after factors  
- **3c** `[3c_verdict.txt](exhibits/3c_verdict.txt)` — which leftovers die  
- **3b** `[3b_summary.txt](exhibits/3b_summary.txt)` — alpha counts per model · `[3b_loadings.txt](exhibits/3b_loadings.txt)` — full-model factor loadings  
- **3d** `[3d_sorted.txt](exhibits/3d_sorted.txt)` — same models on 12–1 sorted portfolios  
- **4a** `[4a_roll.txt](exhibits/4a_roll.txt)` — TOPIX vs World-in-yen CAPM  
- **4b** `[4b_roll.png](exhibits/4b_roll.png)` — those alphas as bars  
- **4.1** `[4_hybrid_stats.csv](exhibits/4_hybrid_stats.csv)` / `[4_hybrid_costs.csv](exhibits/4_hybrid_costs.csv)` / `[4_hybrid_performance.png](exhibits/4_hybrid_performance.png)` / `[4_hybrid_sharpe.png](exhibits/4_hybrid_sharpe.png)` — rolling 60-month out-of-sample backtest of EW, VW, long-only tangency and EW/VW + 10–30% LO hybrids (`stage4_hybrid.py`); monthly returns and weights in `4_hybrid_monthly.csv`, `4_hybrid_weights.csv`
