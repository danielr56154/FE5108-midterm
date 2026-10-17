# Stage 3

Ken French’s Japan file ends 2026-07, so 118 months (Oct 2016 – Jul 2026). Exhibits in `../exhibits/`.

## Choices

**SMB and HML.** Ken French Japan 3-factor file (`../data/ff_japan.csv`). In USD as published; a long–short spread only picks up a second-order currency cross term, so used unconverted.

**WML.** Built here, yen, 12–1, on 78 TSE names (the 30 plus 48 others; `../data/sort_px.csv`). The list is today’s large/mid caps only, equal-weighted.

**Regression.** Stage 2 CAPM, then +SMB+HML, then +WML. α̂ and *t*(α̂) as in 2a. Same 118 months for all three specs, so the CAPM column differs slightly from 2a (120 months).

$$
R_{i,t}-R_{f,t}=\alpha_i+\beta_{i,M}(R_{M,t}-R_{f,t})+\beta_{i,\mathrm{SMB}}\,\mathrm{SMB}_t+\beta_{i,\mathrm{HML}}\,\mathrm{HML}_t+\beta_{i,\mathrm{WML}}\,\mathrm{WML}_t+\varepsilon_{i,t}
$$

WML is omitted in the middle spec; SMB, HML and WML are omitted in CAPM.

## 3a — factor construction

`../exhibits/3a_factors.txt`

**SMB.** June 2×3 on Japanese size (big = top 90% of cap) and B/M (30/70 of the big stocks). Average of the three small books minus the three big books.

**HML.** Same six books: average high B/M minus average low B/M.

**WML.** Each month, rank the 78 on the product of returns from *t*−12 through *t*−2. Equal-weight top 30% minus bottom 30%, hold one month.

The file ends with each factor’s annualized mean, vol and *t*(mean), and the correlation matrix. Only the market premium has |*t*| > 2 (HML 1.68, WML 1.43, SMB −1.07).

## 3b — alphas before vs after

`../exhibits/3b_alphas.txt` · `../exhibits/3b_alphas.png` · `../exhibits/3b_summary.txt` · `../exhibits/3b_loadings.txt`

One row per name, sorted by |*t*(α̂)| under CAPM. `a_*` = annualized α̂; `t_*` = monthly *t*(α̂). Suffixes: `capm`, `ff3` (+SMB+HML), `full` (+WML). Chart: CAPM vs full α̂ as bars.

**Summary.** Per model: names with α̂ > 0, names with |*t*(α̂)| > 2, mean α̂, mean |α̂|; then how many α̂ rose, fell or stayed within ±0.5% a year from CAPM to full.

**Loadings.** Full-model β̂ on each factor with *t*-stats and *R*², sorted by HML loading. Banks load +0.8 to +0.9 on HML; semiconductor and other growth names −0.8 to −1.2. A positive loading times the 6.9% HML premium shrinks α̂, a negative one enlarges it.

## 3c — which leftovers die?

`../exhibits/3c_verdict.txt`

Count of |*t*(α̂)| > 2 and GRS (as in 2c) on each spec.

| Model | loud names | GRS |
| --- | --- | --- |
| CAPM | 3 of 30 | *F*(30, 87) = 1.47, *p* ≈ 0.086 |
| + SMB HML | 3 of 30 | *F*(30, 85) = 2.20, *p* ≈ 0.003 |
| + SMB HML WML | 6 of 30 | *F*(30, 84) = 2.19, *p* ≈ 0.003 |

CAPM |*t*| > 2: Tokio Marine, Itochu, Advantest. |*t*| ≤ 2 after SMB+HML: Tokio Marine, Itochu. Still |*t*| > 2 in the full model: Advantest, Itochu. Newly |*t*| > 2 in the full model: HOYA, Hitachi, Sony, Tokyo Electron.

## 3d — sorted portfolios

`../exhibits/3d_sorted.txt`

Robustness. Each month the 78-name sort tape is cut into five equal-weight 12–1 books (P1 losers … P5 winners), run through the same three specs; P5−P1 is the zero-cost spread, not in the GRS.

| Model | P5−P1 α̂ | GRS (5 books) |
| --- | --- | --- |
| CAPM | 7.5%, *t* = 1.36 | *F*(5, 112) = 5.51, *p* < 0.001 |
| + SMB HML | 9.6%, *t* = 1.75 | *F*(5, 110) = 6.74, *p* < 0.001 |
| + SMB HML WML | 0.3%, *t* = 0.20 | *F*(5, 109) = 5.93, *p* < 0.001 |

WML closes the spread (partly mechanical, same tape), but every book keeps a positive α̂ and GRS rejects under all three specs. A long–short factor cannot price a level shared by every book.
