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

**How much moves.** The bottom block of 4a summarises the shift from TOPIX to World: mean β 1.00 → 0.77 (lower for 28 of 30), cross-sectional corr of the two β vectors 0.93 (rank 0.95), mean R² 0.26 → 0.19, mean |Δα| 2.2 pp a year (max 6.6 pp, SoftBank Group). Alphas barely move because mean β × premium barely moves: 1.00 × 0.144 = 0.144 vs 0.77 × 0.178 = 0.138. Largest β falls are domestic names (Mitsubishi Electric, Mitsubishi Corp, Daiichi Sankyo); the only rises are global tech (LY, SoftBank Group, Recruit roughly flat).
