# Stage 1

Same 30 names throughout. Yen, monthly, Oct 2016 – Sep 2026 (120 return months). Exhibits in `../exhibits/`.

## Choices

**Universe.** Today’s TOPIX Core 30 (JPX Oct 2025), not broad TOPIX. Dropped for thin history: Sony Financial (`8729.T`) and SoftBank Corp (`9434.T`). Added LY (`4689.T`) to keep *N* = 30.

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
