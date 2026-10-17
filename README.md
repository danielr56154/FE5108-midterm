# FE 5108 midterm — Track A

Japan TOPIX Core 30, yen, monthly, Oct 2016 – Sep 2026. Assignment and FAQ: `[midterm_project_handout.pdf](midterm_project_handout.pdf)`.

## Where to look


| Path                               | What it is                                                                              |
| ---------------------------------- | --------------------------------------------------------------------------------------- |
| `[exhibits/](exhibits/)`           | Every table and chart the report will use.                                              |
| `[documentation/](documentation/)` | Documentation about what each stage actually did, and the data choices.                 |
| `[data/](data/)`                   | Cached CSVs (prices, caps, call money, TOPIX, French Japan, WML sort tape, World + FX). |
| `[config.py](config.py)`           | Tickers, dates, market tickers.                                                         |
| `stage1.py` … `stage4.py`, `stage4_hybrid.py` | Code for that stage. `[run_all.py](run_all.py)` runs them in order. Needs `pip install -r requirements.txt` (Python 3.11+). |




## Exhibits

- **1a** `[1a_summary.txt](exhibits/1a_summary.txt)` — mean, vol, Sharpe  
- **1b** `[1b_weights.png](exhibits/1b_weights.png)` — tangency vs value weights  
- **1c** `[1c_subsample.png](exhibits/1c_subsample.png)` — first-half vs second-half tangency  
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



## Still open

Not computed.

1. **Tamed book (Stage 1 / 4).** Long-only or shrunk tangency, so 1b is not only the wild unconstrained weights. FAQ asks us to show this; the Stage 4 memo needs a holdable “in between” book.

