# Stage 3

Ken French’s Japan file ends 2026-07, so 118 months (Oct 2016 – Jul 2026). Exhibits in `../exhibits/`.

## Choices

**SMB and HML.** Ken French Japan 3-factor file (`../data/ff_japan.csv`).

**WML.** Built here, yen, 12–1, on 78 TSE names (the 30 plus 48 others; `../data/sort_px.csv`).

**Regression.** Stage 2 CAPM, then +SMB+HML, then +WML. α̂ and *t*(α̂) as in 2a.

$$
R_{i,t}-R_{f,t}=\alpha_i+\beta_{i,M}(R_{M,t}-R_{f,t})+\beta_{i,\mathrm{SMB}}\,\mathrm{SMB}_t+\beta_{i,\mathrm{HML}}\,\mathrm{HML}_t+\beta_{i,\mathrm{WML}}\,\mathrm{WML}_t+\varepsilon_{i,t}
$$

WML is omitted in the middle spec; SMB, HML and WML are omitted in CAPM.

## 3a — factor construction

`../exhibits/3a_factors.txt`

**SMB.** June 2×3 on Japanese size (big = top 90% of cap) and B/M (30/70 of the big stocks). Average of the three small books minus the three big books.

**HML.** Same six books: average high B/M minus average low B/M.

**WML.** Each month, rank the 78 on the product of returns from *t*−12 through *t*−2. Equal-weight top 30% minus bottom 30%, hold one month.

## 3b — alphas before vs after

`../exhibits/3b_alphas.txt` · `../exhibits/3b_alphas.png`

One row per name, sorted by |*t*(α̂)| under CAPM. `a_*` = annualized α̂; `t_*` = monthly *t*(α̂). Suffixes: `capm`, `ff3` (+SMB+HML), `full` (+WML). Chart: CAPM vs full α̂ as bars.

## 3c — which leftovers die?

`../exhibits/3c_verdict.txt`

Count of |*t*(α̂)| > 2 and GRS (as in 2c) on each spec.

| Model | loud names | GRS |
| --- | --- | --- |
| CAPM | 3 of 30 | *F*(30, 87) = 1.44, *p* ≈ 0.096 |
| + SMB HML | 3 of 30 | *F*(30, 85) = 2.12, *p* ≈ 0.004 |
| + SMB HML WML | 6 of 30 | *F*(30, 84) = 2.09, *p* ≈ 0.004 |

CAPM |*t*| > 2: Tokio Marine, Itochu, Advantest. |*t*| ≤ 2 after SMB+HML: Tokio Marine, Itochu. Still |*t*| > 2 in the full model: Advantest, Itochu. Newly |*t*| > 2 in the full model: HOYA, Hitachi, Sony, Tokyo Electron.
