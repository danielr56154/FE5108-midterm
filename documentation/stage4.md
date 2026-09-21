# Stage 4

**Global proxy.** MSCI World via iShares `URTH` (dollars). Converted to yen unhedged with Yahoo `JPY=X` (USDJPY): dollar return on World, times one plus the yen–dollar move that month. Same Japanese cash rate as Stage 2 is subtracted after.

$$
R_{\mathrm{world,JPY},t}=(1+R_{\mathrm{URTH,USD},t})(1+R_{\mathrm{USDJPY},t})-1
$$

## 4a

`../exhibits/4a_roll.txt`

Stage 2 CAPM twice: TOPIX vs World-in-yen. One row per name (β̂, α̂, *t*(α̂), *R*² under each). Bottom: |*t*| > 2 count, GRS, and which names are loud under both, only TOPIX, or only World.

## 4b

`../exhibits/4b_roll.png`

The 4a alphas as bars. Blue = TOPIX, orange = World.
