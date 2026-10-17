# Stage 2

Same sample and *r*f as Stage 1. Exhibits in `../exhibits/`.

## Choices

**Market proxy *R*M.** Full TOPIX, not the Core 30 book. Yahoo has no TOPIX index ticker. Nomura ETF `1306.T` has a broken March 2026 print, so the series is the Daiwa TOPIX ETF `1305.T` (auto-adjusted), cached in `../data/mkt.csv`. Aligned to the same 121 month-ends as the stocks.

**Regression.** One time-series CAPM per name, 120 months:

$$
R_{i,t}-R_{f,t}=\alpha_i+\beta_i(R_{M,t}-R_{f,t})+\varepsilon_{i,t}
$$

α̂ in the tables is annualized (12 × monthly intercept). *t*(α̂) and *R*<sup>2</sup> are from the monthly regression.

## 2a — CAPM time-series

`../exhibits/2a_capm.txt`

One row per name: β̂<sub>i</sub>, annualized α̂<sub>i</sub>, *t*(α̂<sub>i</sub>), *R*<sup>2</sup>. Sorted by |*t*(α̂)|.

- *t*(α̂) = monthly intercept / its OLS standard error. It asks whether leftover return is large relative to noise. |*t*| > 2 is roughly a 5% test for **one** name.
- *R*<sup>2</sup> = 1 − SSR/SST. Share of that name’s monthly excess variance explained by TOPIX. High *R*<sup>2</sup> means the months move with the market; it is not a test of whether average return is fair.

$$
t(\hat\alpha_i)=\frac{\hat\alpha_i}{\mathrm{se}(\hat\alpha_i)},\qquad
R^2_i=1-\frac{\sum_t\hat\varepsilon_{i,t}^2}{\sum_t\bigl((R_{i,t}-R_{f,t})-\overline{R_i-R_f}\bigr)^2}
$$

## 2b — empirical SML

`../exhibits/2b_sml.png`

Scatter of average excess return (annualized) against β̂i. Tickers on the points; ticker + name in the colour key.

- **Dashed:** theoretical SML, through the origin, slope = R̄M − R̄f. Green diamond is TOPIX at (1, that slope).
- **Solid:** OLS fit through the 30 dots (intercept and slope free).
- **Orange:** |*t*(α̂)| > 2. **Blue:** the rest.

The vertical gap from a point to the dashed line is that name’s 2a alpha.

## 2c — all α = 0?

`../exhibits/2c_grs.txt`

Two pieces:

1. Count of |*t*(α̂)| > 2. A single-name 5% test would expect about 0.05 × 30 = 1.5 such names by chance if tests were independent.
2. GRS (1989) joint test of the 30-vector of monthly alphas (*K* = 1 factor):

$$
\mathrm{GRS}=\frac{T-N-K}{N}\cdot\frac{\hat\alpha'\hat\Sigma^{-1}\hat\alpha}{1+\bar f^2/\hat\omega}\sim F_{N,\,T-N-K}
$$

Result: 3 of 30 names have |*t*| > 2 (Itochu, Tokio Marine, Advantest) vs ~1.5 expected by chance. GRS *F*(30, 89) = 1.57, *p* ≈ 0.054 — still just above 5%, not a clean joint reject. The 1.5 benchmark also assumes independent tests; the three banks are near-copies, so three loud *t*s are not three independent surprises. Residual covariance in GRS is the MLE (÷ *T*); *p* is the exact *F* tail.

## 2d — fitted SML vs theory

`../exhibits/2d_sml.txt`

Annualized intercept and slope of the two 2b lines. Theory: intercept 0, slope = R̄M − R̄f. Fitted: the OLS line through the 30 dots.
