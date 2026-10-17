# Stage 1

Same 30 names throughout. Yen, monthly, Oct 2016 – Sep 2026 (120 return months). Exhibits in `../exhibits/`.

## Choices

**Universe.** Today’s TOPIX Core 30 (JPX Oct 2025), not broad TOPIX. Dropped for thin history: Sony Financial (`8729.T`) and SoftBank Corp (`9434.T`). Added LY (`4689.T`) to keep *N* = 30. That is today’s members backfilled ten years: failed and delisted firms are missing, so average returns, Sharpes and CAPM alphas are biased up (survivorship). We do not have historical constituents.

**Risk-free rate.** Yen overnight call money (FRED `IRSTCI01JPM156N`). NIRP negatives kept.

$$r_{f,t}=\frac{\text{annual percent}_t}{100\times 12}$$

**Prices.** Yahoo monthly adjusted close (splits and dividends in the series). Cached in `../data/`. First return month is Oct 2016.

$$R_t=\frac{P_t}{P_{t-1}}-1$$

**Value weights (1b only).** Current yen market cap, not 2016 size.

$$w_i^{\mathrm{val}}=\frac{\mathrm{Cap}_i}{\sum_{j=1}^{30}\mathrm{Cap}_j}$$

## Names

| Ticker | Name | Ticker | Name |
| --- | --- | --- | --- |
| 2914.T | Japan Tobacco | 7267.T | Honda |
| 3382.T | Seven & i | 7741.T | HOYA |
| 4063.T | Shin-Etsu | 7974.T | Nintendo |
| 4502.T | Takeda | 8001.T | Itochu |
| 4568.T | Daiichi Sankyo | 8031.T | Mitsui |
| 4689.T | LY (Yahoo) | 8035.T | Tokyo Electron |
| 6098.T | Recruit | 8058.T | Mitsubishi Corp |
| 6367.T | Daikin | 8306.T | MUFG |
| 6501.T | Hitachi | 8316.T | SMFG |
| 6503.T | Mitsubishi Electric | 8411.T | Mizuho |
| 6758.T | Sony | 8766.T | Tokio Marine |
| 6857.T | Advantest | 9432.T | NTT |
| 6861.T | Keyence | 9433.T | KDDI |
| 7011.T | MHI | 9983.T | Fast Retailing |
| 7203.T | Toyota | 9984.T | SoftBank Group |

## 1a — stand-alone performance

`../exhibits/1a_summary.txt`

For each name, full 120 months, call money as *r*<sub>f</sub>. Sorted by Sharpe.

$$
\mu_i=12\,\bar R_i,\qquad
\sigma_i=\sqrt{12}\,\mathrm{sd}(R_i),\qquad
\mathrm{Sharpe}_i=\sqrt{12}\,\frac{\overline{R_i-r_f}}{\mathrm{sd}(R_i)}
$$

## 1b — tangency vs value weights

`../exhibits/1b_weights.png`

Two fully invested portfolios of the same 30 names. Horizontal bars, sorted by value weight (largest at the top).

- **Orange:** value weights (current cap share). Long-only.
- **Blue:** sample tangency, shorts allowed.

$$w\propto\Sigma^{-1}\mu_e,\qquad \sum_i w_i=1$$

## 1c — half-sample weights

`../exhibits/1c_subsample.png`

Same tangency recipe on Oct 2016–Sep 2021 and on Oct 2021–Sep 2026 (60 months each). Scatter: first-half weight vs second-half. Diagonal = same weight both times. Tickers on the points; ticker + name in the colour key.

- Blue: long both · Green: short then long · Orange: long then short · Brown: short both

## 1d — taming the tangency book

`../exhibits/1d_tamed.txt` · `../exhibits/1d_tamed.png`

Two fixes for the wild 1b weights, next to value, 1/N and the raw tangency.

- **Long-only tangency.** Max Sharpe with no shorts, solved as min *y*′Σ̂*y* s.t. μ̂<sub>e</sub>′*y* = 1, *y* ≥ 0, then *w* = *y* / Σ*y* (scipy SLSQP).
- **Shrunk tangency.** Shorts allowed, but both inputs shrunk. Mean: Bayes–Stein (Jorion 1986), pulled toward the minimum-variance portfolio's mean with weight φ. Covariance: Ledoit–Wolf (2004), pulled toward a scaled identity with weight δ.

$$
\hat\mu_{BS}=(1-\phi)\hat\mu+\phi\,\mu_0\mathbf 1,\qquad
\phi=\frac{N+2}{(N+2)+T(\hat\mu-\mu_0\mathbf 1)'S^{-1}(\hat\mu-\mu_0\mathbf 1)},\qquad
\hat\Sigma_{LW}=\delta\,m I+(1-\delta)S
$$

Full sample: δ = 0.11, φ = 0.54. Gross exposure falls from 3.8 (tangency) to 2.0 (shrunk) and 1.0 (long-only, 13 names held). Neither fix makes the weights stable: half-sample weight correlation is −0.17 (tangency), −0.26 (shrunk), −0.24 (long-only). In-sample Sharpe in the table flatters every optimized book.

## 1e — out of sample

`../exhibits/1e_oos.txt`

Each month from Oct 2021, re-estimate every book on the trailing 60 months and hold it one month (60 out-of-sample months). Excess over call money, annualized.

| Book | Sharpe | Avg gross | Monthly turnover |
| --- | --- | --- | --- |
| Value (today's caps) | 1.79 | 1.0 | — |
| Equal 1/N | 1.80 | 1.0 | — |
| Tangency | 0.03 | 5.7 (max 12.0) | 1.89 |
| Long-only tangency | 1.06 | 1.0 | 0.29 |
| Shrunk tangency | 0.80 | 2.1 | 0.38 |

The ranking is the DeMiguel–Garlappi–Uppal (2009) one: the naive books win, the raw tangency is worthless out of sample, and the fixes recover part of the gap but not all. Caveat: value uses today's caps for every month, which is look-ahead (today's big names are yesterday's winners), so its Sharpe is flattered relative to the optimized books. 1/N avoids that cap look-ahead and still matches it. 1/N does **not** avoid survivorship: it is equal-weight of the same 2025 Core 30, so failed names are still missing.
