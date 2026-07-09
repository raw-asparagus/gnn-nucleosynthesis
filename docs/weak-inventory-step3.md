# Weak-reaction inventory — mesa_80 / mesa_151 (Step 3; reconciled Step 4)

**Derived** by `scripts/graph_metrics.py --weak-inventory` (2026-07-09, commit b559dde); regenerate with that command.
Rate set: pynucastro 2.12.0 REACLIB + tabular (ordering suzuki<pruet_fuller<ffn<oda<langanke,
later wins — reproduces MESA weaklib LMP > Oda > FFN, the training-label configuration; ADR 0003),
duplicate links resolved tabular-wins, PYNA_ONLY channels dropped per
configs/reaction_disposition_*.yaml. **Reconciled against MESA r23.05.1** (Step 4,
docs/reaction-reconciliation.md); per-pair table sources verified to match weaklib.
dYe direction: EC/β⁺ lower Yₑ (−1), β⁻ raises it (+1).

## mesa_80 — 46 weak reactions (27 lower Yₑ, 19 raise Yₑ)

| dYₑ | type | source | rate |
| --- | --- | --- | --- |
| -1 | electron_capture | reaclib:ec | `Be7 + e⁻ ⟶ Li7 + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `N13 ⟶ C13 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `O14 ⟶ N14 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `O15 ⟶ N15 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `B8 ⟶ He4 + He4 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:bet+ | `p + p ⟶ H2 + e⁺ + 𝜈` |
| -1 | electron_capture | reaclib:ec | `p + p + e⁻ ⟶ H2 + 𝜈` |
| -1 | beta_pos | reaclib:bet+ | `He3 + p ⟶ He4 + e⁺ + 𝜈` |
| -1 | electron_capture | tabular:oda | `F17 + e⁻ ⟶ O17 + 𝜈` |
| +1 | beta_neg | tabular:oda | `O17 ⟶ F17 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `F18 ⟶ Ne18 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `F18 + e⁻ ⟶ O18 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ne18 + e⁻ ⟶ F18 + 𝜈` |
| +1 | beta_neg | tabular:oda | `O18 ⟶ F18 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `F19 ⟶ Ne19 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ne19 + e⁻ ⟶ F19 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Na21 + e⁻ ⟶ Ne21 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Ne21 ⟶ Na21 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Na22 + e⁻ ⟶ Ne22 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Ne22 ⟶ Na22 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Mg23 + e⁻ ⟶ Na23 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Na23 ⟶ Mg23 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Mg24 + e⁻ ⟶ Na24 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Na24 ⟶ Mg24 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Al25 + e⁻ ⟶ Mg25 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Mg25 ⟶ Al25 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Al26 + e⁻ ⟶ Mg26 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Mg26 ⟶ Al26 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `Al27 ⟶ Si27 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Si27 + e⁻ ⟶ Al27 + 𝜈` |
| -1 | electron_capture | tabular:oda | `P30 + e⁻ ⟶ Si30 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Si30 ⟶ P30 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `P31 ⟶ S31 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `S31 + e⁻ ⟶ P31 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ar35 + e⁻ ⟶ Cl35 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Cl35 ⟶ Ar35 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ca39 + e⁻ ⟶ K39 + 𝜈` |
| +1 | beta_neg | tabular:oda | `K39 ⟶ Ca39 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co56 + e⁻ ⟶ Fe56 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co56 ⟶ Ni56 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe56 ⟶ Co56 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni56 + e⁻ ⟶ Co56 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cu59 + e⁻ ⟶ Ni59 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ni59 ⟶ Cu59 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `n ⟶ p + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `p + e⁻ ⟶ n + 𝜈` |

## mesa_151 — 173 weak reactions (89 lower Yₑ, 84 raise Yₑ)

| dYₑ | type | source | rate |
| --- | --- | --- | --- |
| -1 | electron_capture | reaclib:ec | `Be7 + e⁻ ⟶ Li7 + 𝜈` |
| +1 | beta_neg | reaclib:wc12 | `Be10 ⟶ B10 + e⁻ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `N13 ⟶ C13 + e⁺ + 𝜈` |
| +1 | beta_neg | reaclib:wc12 | `N16 ⟶ O16 + e⁻ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `O15 ⟶ N15 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:wc12 | `B8 ⟶ He4 + He4 + e⁺ + 𝜈` |
| -1 | beta_pos | reaclib:bet+ | `p + p ⟶ H2 + e⁺ + 𝜈` |
| -1 | electron_capture | reaclib:ec | `p + p + e⁻ ⟶ H2 + 𝜈` |
| -1 | beta_pos | reaclib:bet+ | `He3 + p ⟶ He4 + e⁺ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Cl37 + e⁻ ⟶ S37 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `S37 ⟶ Cl37 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Ar38 + e⁻ ⟶ Cl38 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Cl38 ⟶ Ar38 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Ar39 ⟶ K39 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `K39 + e⁻ ⟶ Ar39 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Ar40 ⟶ K40 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Ca40 + e⁻ ⟶ K40 + 𝜈` |
| -1 | electron_capture | tabular:ffn | `K40 + e⁻ ⟶ Ar40 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `K40 ⟶ Ca40 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Ar41 ⟶ K41 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Ca41 + e⁻ ⟶ K41 + 𝜈` |
| -1 | electron_capture | tabular:ffn | `K41 + e⁻ ⟶ Ar41 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `K41 ⟶ Ca41 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Ca42 + e⁻ ⟶ K42 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `K42 ⟶ Ca42 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Ca43 ⟶ Sc43 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Sc43 + e⁻ ⟶ Ca43 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Ca44 ⟶ Sc44 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Sc44 + e⁻ ⟶ Ca44 + 𝜈` |
| +1 | beta_neg | tabular:ffn | `Sc44 ⟶ Ti44 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:ffn | `Ti44 + e⁻ ⟶ Sc44 + 𝜈` |
| -1 | electron_capture | tabular:oda | `F17 + e⁻ ⟶ O17 + 𝜈` |
| +1 | beta_neg | tabular:oda | `O17 ⟶ F17 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `F18 + e⁻ ⟶ O18 + 𝜈` |
| +1 | beta_neg | tabular:oda | `O18 ⟶ F18 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `F19 ⟶ Ne19 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `F19 + e⁻ ⟶ O19 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ne19 + e⁻ ⟶ F19 + 𝜈` |
| +1 | beta_neg | tabular:oda | `O19 ⟶ F19 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `F20 ⟶ Ne20 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ne20 + e⁻ ⟶ F20 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Na21 + e⁻ ⟶ Ne21 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Ne21 ⟶ Na21 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Na22 + e⁻ ⟶ Ne22 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Ne22 ⟶ Na22 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Mg23 + e⁻ ⟶ Na23 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Na23 ⟶ Mg23 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Na23 + e⁻ ⟶ Ne23 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Ne23 ⟶ Na23 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Mg24 + e⁻ ⟶ Na24 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Na24 ⟶ Mg24 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Al25 + e⁻ ⟶ Mg25 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Mg25 ⟶ Al25 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Al26 + e⁻ ⟶ Mg26 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Mg26 ⟶ Al26 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Al27 + e⁻ ⟶ Mg27 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Al27 ⟶ Si27 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `Mg27 ⟶ Al27 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Si27 + e⁻ ⟶ Al27 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Al28 ⟶ Si28 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Si28 + e⁻ ⟶ Al28 + 𝜈` |
| -1 | electron_capture | tabular:oda | `P30 + e⁻ ⟶ Si30 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Si30 ⟶ P30 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `P31 ⟶ S31 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `P31 + e⁻ ⟶ Si31 + 𝜈` |
| -1 | electron_capture | tabular:oda | `S31 + e⁻ ⟶ P31 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Si31 ⟶ P31 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `P32 ⟶ S32 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `P32 + e⁻ ⟶ Si32 + 𝜈` |
| -1 | electron_capture | tabular:oda | `S32 + e⁻ ⟶ P32 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Si32 ⟶ P32 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `P33 ⟶ S33 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `P33 + e⁻ ⟶ Si33 + 𝜈` |
| -1 | electron_capture | tabular:oda | `S33 + e⁻ ⟶ P33 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Si33 ⟶ P33 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:oda | `P34 ⟶ S34 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `S34 + e⁻ ⟶ P34 + 𝜈` |
| -1 | electron_capture | tabular:oda | `Cl35 + e⁻ ⟶ S35 + 𝜈` |
| +1 | beta_neg | tabular:oda | `S35 ⟶ Cl35 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ar36 + e⁻ ⟶ Cl36 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Cl36 ⟶ Ar36 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Cl36 + e⁻ ⟶ S36 + 𝜈` |
| +1 | beta_neg | tabular:oda | `S36 ⟶ Cl36 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:oda | `Ar37 + e⁻ ⟶ Cl37 + 𝜈` |
| +1 | beta_neg | tabular:oda | `Cl37 ⟶ Ar37 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ca45 ⟶ Sc45 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Sc45 + e⁻ ⟶ Ca45 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Sc45 ⟶ Ti45 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ti45 + e⁻ ⟶ Sc45 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ca46 ⟶ Sc46 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Sc46 + e⁻ ⟶ Ca46 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Sc46 ⟶ Ti46 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ti46 + e⁻ ⟶ Sc46 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ca47 ⟶ Sc47 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Sc47 + e⁻ ⟶ Ca47 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Sc47 ⟶ Ti47 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ti47 + e⁻ ⟶ Sc47 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ti47 ⟶ V47 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `V47 + e⁻ ⟶ Ti47 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ca48 ⟶ Sc48 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cr48 + e⁻ ⟶ V48 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Sc48 + e⁻ ⟶ Ca48 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Sc48 ⟶ Ti48 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ti48 + e⁻ ⟶ Sc48 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ti48 ⟶ V48 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `V48 ⟶ Cr48 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `V48 + e⁻ ⟶ Ti48 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ca49 ⟶ Sc49 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cr49 + e⁻ ⟶ V49 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Sc49 + e⁻ ⟶ Ca49 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Sc49 ⟶ Ti49 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ti49 + e⁻ ⟶ Sc49 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ti49 ⟶ V49 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `V49 ⟶ Cr49 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `V49 + e⁻ ⟶ Ti49 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cr50 + e⁻ ⟶ V50 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ti50 ⟶ V50 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `V50 ⟶ Cr50 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `V50 + e⁻ ⟶ Ti50 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Cr51 ⟶ Mn51 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cr51 + e⁻ ⟶ V51 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Mn51 + e⁻ ⟶ Cr51 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Ti51 ⟶ V51 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `V51 ⟶ Cr51 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `V51 + e⁻ ⟶ Ti51 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Cr52 ⟶ Mn52 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Cr52 + e⁻ ⟶ V52 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Fe52 + e⁻ ⟶ Mn52 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Mn52 + e⁻ ⟶ Cr52 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Mn52 ⟶ Fe52 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `V52 ⟶ Cr52 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Cr53 ⟶ Mn53 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Fe53 + e⁻ ⟶ Mn53 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Mn53 + e⁻ ⟶ Cr53 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Mn53 ⟶ Fe53 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Cr54 ⟶ Mn54 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Fe54 + e⁻ ⟶ Mn54 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Mn54 + e⁻ ⟶ Cr54 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Mn54 ⟶ Fe54 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co55 + e⁻ ⟶ Fe55 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Cr55 ⟶ Mn55 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe55 ⟶ Co55 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Fe55 + e⁻ ⟶ Mn55 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Mn55 + e⁻ ⟶ Cr55 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Mn55 ⟶ Fe55 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co56 + e⁻ ⟶ Fe56 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co56 ⟶ Ni56 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe56 ⟶ Co56 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Fe56 + e⁻ ⟶ Mn56 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Mn56 ⟶ Fe56 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni56 + e⁻ ⟶ Co56 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co57 + e⁻ ⟶ Fe57 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co57 ⟶ Ni57 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe57 ⟶ Co57 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni57 + e⁻ ⟶ Co57 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co58 + e⁻ ⟶ Fe58 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co58 ⟶ Ni58 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe58 ⟶ Co58 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni58 + e⁻ ⟶ Co58 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co59 + e⁻ ⟶ Fe59 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co59 ⟶ Ni59 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe59 ⟶ Co59 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni59 + e⁻ ⟶ Co59 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co60 + e⁻ ⟶ Fe60 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co60 ⟶ Ni60 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe60 ⟶ Co60 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni60 + e⁻ ⟶ Co60 + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Co61 + e⁻ ⟶ Fe61 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Co61 ⟶ Ni61 + e⁻ + 𝜈` |
| +1 | beta_neg | tabular:langanke | `Fe61 ⟶ Co61 + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `Ni61 + e⁻ ⟶ Co61 + 𝜈` |
| +1 | beta_neg | tabular:langanke | `n ⟶ p + e⁻ + 𝜈` |
| -1 | electron_capture | tabular:langanke | `p + e⁻ ⟶ n + 𝜈` |

