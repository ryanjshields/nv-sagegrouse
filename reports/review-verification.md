# Verification Memo — Fresh-Eyes Review Repairs ("Predicting fine-scale lek site selection…", v4)

**Scope:** independent re-verification of every finding in `reports/review-fresh-eyes.md` against
`reports/paper.qmd`, `reports/findings.qmd`, all `reports/v4/*.csv` + `reports/v4/tables/*.md`
(regenerated 2026-08-12), `reports/v4/usgs_validation.txt`, and the `pipeline/` scripts.
`data-local/` was not opened; no coordinates appear here.

**Headline verdict:** the analysis-side repairs are real and mostly landed — the separation guard,
the Flat aspect category, the m13 spatial validation, the fire-sensitivity refit, and the corrected
USGS contingency all check out against the regenerated artifacts. The **paper's Results/Methods
largely caught up; the Discussion did not** (one 2024 fossil survives verbatim), and
**findings.qmd was left substantially stale** — it still carries pre-refit coefficients, a
pre-pooling vegetation narrative that contradicts its own included table, and a "planned checks"
sentence for work that is finished. Four new misroundings entered the paper with the refreshed
numbers, and one stale statistic (lek-size ρ = 0.07) survived in the paper.

**Verdict counts (unique prior findings, dupes merged):** **FIXED 11 · PARTIAL 19 · STILL PRESENT 17** — plus **13 NEW issues** (N1–N13 below).

---

## Part 1 — Prior findings, verdict by verdict

### Axis 1 (internal consistency, C1–C16)

| # | Verdict | Evidence |
|---|---------|----------|
| C1 road-effect fossil | **FIXED** | "did not significantly affect" is gone (grep: no match). Results now reports the class-specific opposing effects, paper.qmd:398–402, matching `averaged_betas.csv` (paved +0.096 CI excl. 0; unpaved −0.087 CI incl. 0). |
| C2 curvature fossil | **FIXED** | "less support for … curvature" gone. Curvature reported significant (β = −0.42, CI −0.55 – −0.29), paper.qmd:402–404 = CSV (−0.4219, −0.5506, −0.2932). Model-support paragraph now written from Table 3 (paper.qmd:354–359). |
| C3 aspect list wrong twice | **PARTIAL** | Results fixed (paper.qmd:395–398: NE/NW/SW/W significant; N and S "did not differ" — all correct per CSV: NE CI −0.539 – −0.057 excludes 0; N −0.337 – +0.136 and S −0.350 – +0.123 include 0). **Discussion still carries the 2024 sentence verbatim** at paper.qmd:517–518: "less likely to be located on N-, NW-, S-, SW-, and W-facing slopes" — lists two n.s. terms (N, S) and omits significant NE. |
| C4 \|0.6\| claim vs Fig. 3 | **FIXED** | Rewritten precisely: "no pair of covariates appearing together in any single model exceeded \|r\| = 0.6 … (Distance to any road and distance to unpaved roads are nearly collinear, r = 0.99 … never co-occur in a model)", paper.qmd:296–300; same in findings.qmd:135–139. |
| C5 USGS 49%/40% narrative | **FIXED** | Text now 46% / 41% (paper.qmd:411–414 and 436–439) = regenerated `usgs_contingency.md` (cat 1 × very-low = 46%; cat 4 × very-high = 41%). Residual nit → N8 ("monotone" still overstated for the cat-2 row). |
| C6 "10 categories" list | **PARTIAL** | Paper fixed: 12-class enumeration incl. developed/agricultural/open-water + explicit pooling rule (<10 sites or <5 used leks → Other) with the separation rationale, paper.qmd:224–233. **findings.qmd:85–90 still carries the old 10-category draft list** ("follow the draft analysis"). Paper list omits Hardwood but hedges with "include" — harmless post-pooling. |
| C7 VIF < 1.6 | **FIXED** | Methods "VIF ≤ 1.8" (paper.qmd:315–316), Results "1.0–1.8" (paper.qmd:357–359), findings "VIF ≤ 1.8" (×2) — `vif.csv` max = 1.7986 (m13 DirectionSE), min = 1.012. ✔ |
| C8 figure numbering | **PARTIAL** | The Fig.-4-should-be-Fig.-8 fossil is fixed (paper.qmd:333 → Fig. 8; Fig. 1–8 sequence internally consistent and each in-text ref anchors correctly). Still broken: **"Figs. 2a–2b in supporting charts below" (paper.qmd:264–265)** — the road charts remain unnumbered images and "Fig. 2" is already the covariate-multiples figure. Nine figures still unnumbered (roads ×2, forest, response curves, ROC, Boyce, USGS side-by-side, bins-multiples, zoom) amid numbered neighbors. |
| C9 misrounded coefficients | **PARTIAL** | The two flagged instances no longer exist (numbers re-baselined by the refit), but **four new misroundings** entered the paper — see N9. findings' VRM CI (−1.27) is correct where the paper's (−1.28) is not. |
| C10 which model was CV'd | **PARTIAL** | Spatial CV now attributed to the top model (paper.qmd:407–408) and explicitly "top model m13" in findings.qmd:191–193. Remaining: the abstract attributes the spatially blocked CV to "the averaged model" (paper.qmd:50–51 — it was m13, see N10); the random-CV attribution in the Results sentence is still ambiguous ("The averaged model discriminated well … random 5-fold cross-validation 0.80 ± 0.01" — `diagnostics.csv` labels it "top model"); ROC caption still "top model" beside averaged-model prose. |
| C11 spatial validation on wrong model | **PARTIAL** | Pipeline fixed: `validate_spatial.R:28–29` fits paved+unpaved (m13), comment now "# m13 (top model)"; `spatial_validation.csv` regenerated (folds 0.777/0.834/0.835/0.744/0.812; mean 0.80 sd 0.039; Spearman 0.041). Paper picked up the new spatial AUC (0.80 ± 0.04 ✔) **but not the new lek-size Spearman: paper.qmd:441 still says ρ = 0.07** — the stale m1-era value (see N1). findings.qmd:195–196 correctly says 0.04. |
| C12 S1 table mismatch | **PARTIAL** | The 100,000-point Monte Carlo estimator is now stated (paper.qmd:286–290) ✔. Still: "each continuous variable" while `validation.md` shows "—" (no study-area mean) for all three road rows yet marks them "Covered: yes"; the **Ruggedness "Covered: no" row is acknowledged only in findings** (findings.qmd:152–154, "~1%" miss — arithmetically right: 0.002068 vs CI-high 0.002049 ≈ 0.9%) and **nowhere in the paper**. |
| C13 716 vs 718 | **PARTIAL** | Footnote added and parent population restored: "n = 718, from 2,253 records statewide … (An earlier draft reported n = 716; the register contains 718 in-state active records…)", paper.qmd:154–157. The attribute-vs-geometry criterion is still not explicit: text says "located within Nevada" while `prepare_design.py:49` filters on the STATE attribute. |
| C14 references-as-diff | **STILL PRESENT** | paper.qmd:569–574 still opens "References [1]–[30] as in the 2024 draft … with the following updates". Mixed numeric/author-year styles persist (WAFWA 2015, Coates et al. 2020 in Study Area vs [1]/[36]). [6] still carries three different claims: fragmentation (line 73), lek-counts→nesting habitat (line 82), and placement-vs-size (line 441–442) — if [6] = Van Horne 1983, the first two are miscited. |
| C15 pipeline fossils | **PARTIAL** | `validate_spatial.R` m1 comment fixed ✔. **`extract_covariates.py:13` docstring still reads "Distance-to-road is computed against TIGER NV primary/secondary roads"** (stale — all classes used, as the corrected line-66 comment says). VRM still lives in a column named `tri` (commented). New fossil at N4b. |
| C16 90-m distance grid unstated | **STILL PRESENT (in paper)** | Scripts now document it (`build_roads_raster.sh` header: 90-m compute → bilinear 30-m, error ≈ 1 compute cell; same note in `build_roads_by_class.sh`). The paper still says the surfaces were "computed … on the DEM grid, ensuring cell-location continuity" (paper.qmd:278–279) with no 90-m mention. |

### Axis 2 (against the archive, A2–A11)

| # | Verdict | Evidence |
|---|---------|----------|
| A2 / S6 quasi-separation | **FIXED** | `fit_models.R:37–42` separation guard (<5 used leks → Other); `coefficients.md` has no ±700 CIs — largest SE is 0.343 (VegetationOther); Methods states the guard and names the old pathology (paper.qmd:228–233); Results/Discussion report conifer <5 sites → pooled avoidance (β = −2.57, CI −3.06 – −2.07 = CSV). |
| A3 / S15 availability justification + VRM row | **PARTIAL** | MC estimator stated; findings acknowledges the VRM miss. The paper still offers **no justification or citation for 1:10** (paper.qmd:215–217), never acknowledges the failed VRM coverage row, and the availability sample was not increased. |
| A4 define "active" lek | **STILL PRESENT** | paper.qmd:151–154 — categories listed, criterion never defined. |
| A5 interactions/quadratics | **STILL PRESENT** | All 15 models linear-additive (`fit_models.R:45–60`); no defense of linearity anywhere in the paper. |
| A6 broader-scale nesting context | **STILL PRESENT** | No landscape-composition covariates; the one-sentence rebuttal survives uncited (paper.qmd:471–473; see W6). External USGS correlation is still the only answer. |
| A7 anthropogenic covariates beyond roads | **STILL PRESENT** | No justification sentence anywhere. |
| A8 silent ruggedness reversal | **PARTIAL** | Disclosure added: the old index "proved unstable across DEM generations … entered those models as an effectively binary covariate; ruggedness results are therefore not directly comparable across versions" (paper.qmd:252–256); findings adds the 63%-agreement statistic (findings.qmd:100–104). The **sign flip itself (+0.14 → −1.02) is still never stated**. |
| A9 parent lek count | **FIXED** | "from 2,253 records statewide" (paper.qmd:154) — matches the Dec-2023 record. Buffer-bug and EVT_PHYS descriptions remain consistent with code. |
| A10 lost-2024 elements | **PARTIAL** | Averaging type restored ("full (zero-substitution) average in MuMIn", paper.qmd:317–319 = `fit_models.R:71–72`) ✔; parent count restored ✔; availability justification still absent; bold-CI caption convention not restored (cosmetic). |
| A11 clustered-lek pseudoreplication omen | **STILL PRESENT** | Same as S1 below. |

### Axis 3 (good science, S1–S17)

| # | Verdict | Evidence |
|---|---------|----------|
| S1 spatial autocorrelation (inference) | **STILL PRESENT** | No Moran's I, no cluster bootstrap/GLMM, no limitation paragraph. The blocked CV (predictive) is the only spatial treatment, as before. |
| S2 design leaks | **STILL PRESENT** | `prepare_design.py:39–43` still buffers ALL out-of-range active leks (incl. out-of-state) into the study area while excluding them from used (line 49); no justification text; no available-points-on-leks sentence. |
| S3 temporal mismatch | **FIXED** (the "better" fix) | Vintages stated; Martin Fire named (paper.qmd:331–337, 474–477); LF2016↔LF2025 cross-tab + top-model refit implemented (`veg_change_check.py`, `sensitivity_fire.R`) and honestly reported: 35/718 (4.9%) changed, 8 fire-signature, grassland 0.43→0.21 with explicit caution (paper.qmd:416–422, 473–483) — all = `veg_change.md` / `sensitivity_fire.csv` (0.431→0.211). One overstatement leaked into the abstract → N7. |
| S4 "15 a priori" framing | **FIXED** | Abstract: "twelve a priori covariate combinations and a planned second-stage decomposition"; Methods: "specified after the combined-roads models had been examined, and their support should be read in that light" (paper.qmd:300–311). Minor residual tension between abstract's "planned" and Methods' admission. |
| S5 averaging choices | **PARTIAL** | Full average now stated ✔. Still: no conditional-average or top-model comparison; "top three" cutoff undefended (includes m15 Δ4.5, excludes m1 Δ5.7 per `model_selection.csv`); Grueber/Banner uncited; nonlinearity undefended (A5). |
| S6 | **FIXED** — see A2. |
| S7 quantile bins / lek-capture stat | **STILL PRESENT** | `prediction_bins_v4.md` is still five rows of 20.0%; no leks-captured-per-bin statistic anywhere; the "survey-targeting product" caption survives verbatim (paper.qmd:451–454). R1's "too large to be useful" jab remains unanswered. |
| S8 flat-as-north artifact | **FIXED** | Flat category implemented (`extract_covariates.py:44–48`, slope < 0.5°; mirrored in `build_prediction.py:115–121`), documented with rationale (paper.qmd:242–246), and reported (Flat β = −1.20, CI −1.48 – −0.91 per CSV; "playa and lake-bed surfaces… leks occupy gentle, but not featureless, terrain"). |
| S9 Arnold 2010 for 85% CIs | **STILL PRESENT** | No Arnold citation (grep: none); "85% confidence intervals consistent with AIC-based selection" stands bare (paper.qmd:318–319). |
| S10 curvature undefined/undiscussed | **PARTIAL** | One interpretive clause added ("avoidance of locally convex microtopography", paper.qmd:402–404). Curvature type and sign convention still undefined in both documents; Discussion still silent; and `build_dem.sh:8–10` claims the convention "is documented in the findings report" — **it is not** (findings mentions curvature only in a covariate list) → N12. |
| S11 paved/unpaved labels overstate TIGER | **STILL PRESENT** | Covariates still named paved/unpaved (paper.qmd:279–282); no surface-is-inferred caveat; S1740 (988 km) still in Table 2's low-usage group yet excluded from both class surfaces (`build_roads_by_class.sh:14–15`), unreconciled. |
| S12 standardization unstated | **PARTIAL** | findings.qmd:113 states z-scaling ✔. The **paper never does** (grep "standard": only "standard errors" and "standard ruggedness metric"), and Table 4 still shows `scale_*` row names. |
| S13 external validation framing | **PARTIAL** | Numbers corrected (ρ = 0.53 = 0.527; 46/41); "aligned with independent data while retaining the complementary, lek-specific information" phrasing retained (paper.qmd:414–416). |
| S14 "well calibrated" + probability language | **STILL PRESENT** | "well calibrated across deciles" retained (paper.qmd:408–409) while `calibration.csv` decile 4 = 0.0285 predicted vs 0.0139 observed (2.05×); "probability of lek occurrence" language throughout abstract/map/captions; no relative-selection-intensity framing; Keating & Cherry uncited. |
| S15 | **PARTIAL** — see A3. |
| S16 shrubland reference justification | **STILL PRESENT** | Stated as the reference (Table 4 caption) but never justified. |
| S17 reproducibility overclaim | **STILL PRESENT** | Abstract still "every run is exactly reproducible" (paper.qmd:52–54); "every acquisition writes a provenance manifest" (paper.qmd:159–162) and findings.qmd:65–66 ("All acquisition … write provenance manifests") remain false for `fetch_roads_all.py` (writes none — verified, lines 33–45); the fetch_tnm most-recent-tile dedup caveat is unaddressed. |

### Axis 4 (writing, W1–W8)

| # | Verdict | Evidence |
|---|---------|----------|
| W1 abstract README paragraph | **STILL PRESENT** | paper.qmd:52–54, verbatim. |
| W2 machine aphorisms | **PARTIAL** | The road-axis aphorism was properly softened ("suggesting that road class carries more ecological information … the unpaved association, however, was weak and should not be over-interpreted", paper.qmd:512–515). Still present: "aligned with independent data while retaining the complementary…" (paper.qmd:414–416); "directly actionable for treatment prioritization" (paper.qmd:490); "four times smoother than the landscape offers" (findings.qmd:179). |
| W3 "decorrelated by construction (r = 0.40)" / "the standard ruggedness metric" | **STILL PRESENT** | Verbatim at paper.qmd:249–252 and findings.qmd:104–106. |
| W4 caption salesmanship | **STILL PRESENT** | "survey-targeting product" caption verbatim (paper.qmd:451–454). |
| W5 internal artifacts | **PARTIAL** | m13–m15 now explained in the Table 3 caption ✔. Still: subtitle "(v4 pipeline)"; Table 4 rows `scale_Elevation`/`DirectionN`/`VegetationGrassland`. |
| W6 uncited nesting-scale rebuttal | **STILL PRESENT** | paper.qmd:471–473, still no citation. |
| W7 abstract "herbaceous… favored" plural | **FIXED** | Abstract now claims grassland only (β = 0.44) and handles conifer via the pooled class; exotic herbaceous correctly reported as trending n.s. in Results. |
| W8 references / quantify declines | **STILL PRESENT** | Same as C14; "significant population reduction" still unquantified in the abstract (the 17–47% figures appear only in the Introduction). |

---

## Part 2 — Full number audit (both documents vs regenerated artifacts)

**Verified correct** (paper unless noted): elevation 0.94 (0.85–1.03) = 0.9394 (0.8506–1.0281); slope −1.31 (−1.47 – −1.16) = −1.3129 (−1.4660 – −1.1598); VRM estimate −1.02 = −1.0152; Flat −1.20 = −1.1964; curvature −0.42 (−0.55 – −0.29); paved 0.10 & CI-low 0.03 = 0.0959/0.0272; unpaved −0.09 (−0.19 – 0.01) = −0.0873 (−0.1871 – 0.0126); exotic herbaceous 0.20 (−0.06 – 0.46); pooled Other −2.57 (−3.06 – −2.07); grassland estimate 0.44 & CI-high 0.72; riparian/exotic-tree-shrub "avoided" (both CIs exclude 0); aspect significance calls in Results; AUC 0.81 = 0.8072; random CV 0.80 ± 0.01 = 0.7998 ± 0.0078 (paper); spatial CV 0.80 ± 0.04 = 0.800 ± 0.039; Boyce 0.92 = 0.915; USGS ρ 0.53 = 0.527 at 147,036 (~147,000) of 150,000; 46%/41% contingency; 35/718 = 4.9%, 8 fire-signature leks; grassland 0.43→0.21 = 0.431→0.211; VRM means 0.00046/0.00197; VIF 1.0–1.8 (1.012–1.7986); road total 100,790 km (column-exact); 202,967 segments; 17 counties; n = 718 / 7,180 / 2,253; seed 20260811; m13–m15 order, ΔAICc, weights, df per `model_selection.csv`; findings' VRM −1.02 (−1.27 – −0.76), spatial CV, lek-size 0.04, "~1%" VRM coverage miss (0.9%).

**Mismatches (every one found):**

| Doc:line | Text | Ground truth | Should read |
|---|---|---|---|
| paper:441 | lek-size Spearman **ρ = 0.07** | `spatial_validation.csv` = 0.041 | 0.04 |
| paper:400–401 | "lek sites averaged **896 m** from the nearest unpaved route" | `summary_stats.md`: used-lek unpaved mean = **711.4 m** (896 matches no current output; nearest are available any-road 893.1 / available unpaved 914.1) | 711 m |
| paper:42–43, 381–382 | VRM CI low **−1.28** (abstract + Results) | −1.27455 | −1.27 (findings already correct) |
| paper:48, 399 | paved CI high **0.17** (abstract + Results) | 0.16464 | 0.16 |
| paper:44–45, 387 | grassland CI low **0.16** (abstract + Results) | 0.15470 | 0.15 |
| paper:385 | Flat CI low **−1.49** | −1.48472 | −1.48 |
| findings:172–173 | elevation **0.96 (0.87–1.05)** | 0.9394 (0.8506–1.0281) | 0.94 (0.85–1.03) — pre-Flat-refit value |
| findings:173–174 | slope **−1.19 (−1.34 – −1.05)** | −1.3129 (−1.4660 – −1.1598) | −1.31 (−1.47 – −1.16) — stale |
| findings:183–185 | random 5-fold CV **0.791 ± 0.012** | `diagnostics.csv` 0.7998 ± 0.0078 | 0.80 ± 0.01 — stale |
| findings:207–209 | "conifer, sparsely vegetated … fall well below … conifer most strongly avoided" | `coefficients.md` contains **no Conifer or Sparsely Vegetated rows** (pooled into Other) | describes the superseded pre-pooling fit; contradicts the table included 40 lines earlier |

---

## Part 3 — NEW issues (not in the prior review, or introduced by the repairs)

1. **N1 (MAJOR).** paper.qmd:441 — stale lek-size Spearman 0.07 (current 0.041). The one number from the C11 rerun that was not carried into the paper.
2. **N2 (MAJOR).** paper.qmd:400–401 — "896 m" mean distance to unpaved routes traces to nothing in the current outputs; used-lek mean is 711.4 m. Wrong value, possibly wrong population (available vs used).
3. **N3 (MAJOR).** findings.qmd:172–175 — elevation and slope coefficients/CIs are from a superseded fit (pre-Flat, pre-pooling); both documents now disagree with each other on headline betas.
4. **N4 (MAJOR).** findings.qmd:183–185 — stale random-CV value 0.791 ± 0.012 vs diagnostics 0.7998 ± 0.0078. Companion pipeline fossil: `validate_spatial.R:63` **hardcodes 0.791** as "random-fold AUC (reference)" into `spatial_validation.csv`, so a regenerated artifact now embeds a stale constant inconsistent with `diagnostics.csv`.
5. **N5 (MAJOR).** findings.qmd:203–215 — vegetation narrative ("conifer most strongly avoided", "herbaceous cover over conifer… each element carries a coefficient with a clean confidence interval") describes the pre-pooling model; the included coefficients table has no conifer term, exotic herbaceous's CI crosses zero, and the referenced `vegetation.png` sits beside text it no longer supports.
6. **N6 (superseded-analysis sentence).** findings.qmd:197–201 — "A Boyce index on the full surface and external correlation against the USGS 2024/2025 habitat rasters are the **remaining planned checks**" — both are complete (`boyce.md`, `usgs_validation.txt`) and reported in the paper.
7. **N7 (abstract vs Results contradiction).** paper.qmd:50–52 — "its predictions were insensitive to post-2018 vegetation change at lek sites" overstates its own sensitivity analysis, which halved the grassland coefficient (0.431→0.211) and prompted explicit caution in Results and Discussion.
8. **N8 (minor).** paper.qmd:436–437 — "the gradient is monotone" is not strictly true of the included table: USGS cat-2 row runs 9/18/25/26/**22**% (dips in the final bin). Cats 1, 3, 4 are monotone.
9. **N9 (minor, 4 instances).** New misroundings introduced with the refreshed numbers (rows 3–6 of the mismatch table): −1.28/−1.27, 0.17/0.16, 0.16/0.15, −1.49/−1.48. Individually trivial; collectively the same "unverified numbers" signal C7/C9 warned about.
10. **N10 (minor).** Abstract attributes the spatially blocked CV to "the averaged model" (paper.qmd:50–51); it was run on top model m13 (Results and findings say so correctly).
11. **N11 (minor).** paper.qmd:419–420 claims the sensitivity refit left "terrain, **road**, and exotic herbaceous coefficients essentially unchanged," but `sensitivity_fire.csv` contains no road terms — `sensitivity_fire.R:35–36`'s keep-list omits paved/unpaved (and still lists "VegetationConifer", which can never appear post-pooling). The road half of the sentence has no artifact behind it.
12. **N12 (minor, pipeline).** `build_dem.sh:8–10` says the curvature sign/scale convention "is documented in the findings report" — findings.qmd contains no such documentation (curvature appears only in a covariate list).
13. **N13 (minor).** findings.qmd:85–90 still carries the old 10-category vegetation list "follow[ing] the draft analysis," inconsistent with the paper's corrected 12-class enumeration (C6's fix was applied to one document only).

---

## Part 4 — What a resubmission still rides on

The fossil-purge succeeded in the paper's Results but not its Discussion (C3), and findings.qmd
was never re-synchronized after the final refit — it now contradicts the paper and its own included
tables (N3–N6). The structural reviewer bait flagged in 2023 remains substantially unaddressed:
active-lek definition (A4), nonlinearity (A5), broader-scale nesting context (A6), non-road
anthropogenic covariates (A7), spatial-autocorrelation inference (S1/A11), 1:10 availability
justification (A3), the information-free quantile-bin table (S7), and the RSF-probability language
(S14). The genuinely repaired items — separation guard, Flat category, fire sensitivity, m13
validation, corrected USGS narrative — are solid and verifiable, but the two documents must tell
the same story before either is shown to a reviewer.

— end of verification memo —
