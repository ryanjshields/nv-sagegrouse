# Fresh-Eyes Review — "Predicting fine-scale lek site selection of greater sage-grouse in Nevada, USA" (2026 draft, v4 pipeline)

**Reviewer posture:** demanding but fair; no prior involvement. Reviewed against: the 2024 PLOS-bound draft, the 2023 REMA rejection reviews (REMA-D-23-00165), the coauthor email record (Nov 2023–Jan 2024, plus the 2021–22 RSF-issues thread), the 2021 REMA sheep-RSF reviews, the v4 pipeline code, and every CSV/table output in `reports/v4/`.

**Overall verdict:** The 2026 revision is a genuine methodological upgrade — reproducible pipeline, corrected study-area figure, VRM instead of a broken ruggedness index, road-class models, and a real validation battery (random + spatial CV, calibration, Boyce, external USGS comparison). But the manuscript text has not caught up with its own analysis. There are at least **eight places where the prose contradicts the tables it includes**, one reported validation statistic that was **computed on the wrong model**, and the two criticisms that actually sank the 2023 submission — **quasi-separation in the vegetation coefficients** and the **absence of any broader-scale/nesting-habitat context** — are still present. Submitting as-is invites a repeat rejection, possibly from the same reviewers.

---

## Top findings (severity-ranked)

| # | Severity | Finding |
|---|----------|---------|
| 1 | MAJOR | Results state roads had no significant effect and "less support for … curvature" — both directly contradicted by the paper's own Table 3, Table 4, and abstract (fossils from the 2024 draft). |
| 2 | MAJOR | Spatially blocked CV (0.80 ± 0.03) and lek-size Spearman (0.07) were computed on **m1**, not the reported top model m13 (`validate_spatial.R` still carries the stale comment `# m1 (top model)`). |
| 3 | MAJOR | Four vegetation classes still show the exact separation pathology Reviewer 2 rejected in 2023 (β ≈ −13 to −14, SE 475–656, CIs spanning ±700–950). |
| 4 | MAJOR | The aspect-effects sentence (Results *and* Discussion) lists N and S as avoided (both n.s. at 85% CI) and omits NE (which is significant). Carried verbatim from 2024. |
| 5 | MAJOR | "No pairwise correlation more extreme than \|0.6\| (Fig. 3)" — Fig. 3 itself shows r = 0.99 (distance-to-any-road vs distance-to-unpaved). |
| 6 | MAJOR | USGS cross-tab text claims "49% … and 40%" — the included table says 23% and 22%, and the gradient is only weakly monotone. |
| 7 | MAJOR | "15 a priori models" misdescribes history: 12 models are the 2023 set verbatim; the 3 road-class models were added in 2026 after the all-roads null result and after Reviewer 1 demanded road classes. |
| 8 | MAJOR | Temporal mismatch (leks active as of 2018 vs LF2025 vegetation, TIGER 2024 roads) is nowhere acknowledged — despite the team's own lit-review memo planning exactly that statement. Post-2018 megafires make the herbaceous-selection result vulnerable. |
| 9 | MAJOR | VIF claims ("< 1.6", "1.0–1.6") are false against `vif.csv` (max 1.77). |
| 10 | MAJOR | Reviewer 1's structural criticisms — define "active" lek; no interactions/quadratics; no broader-scale nesting context; 20%-of-state "high" bin too large to be useful — remain unaddressed or only rhetorically addressed. |

---

## Axis 1 — Internal consistency (prose vs. outputs)

### C1. MAJOR — Road-effect fossil in Results
> "Road proximity did not significantly affect the probability of lek occurrence."

This is the 2024 draft's conclusion. It flatly contradicts this draft's abstract ("leks sat farther from paved roads (β = 0.10, 85% CI 0.04 – 0.17)"), Table 4 (paved CI excludes zero), and the entire road-class Discussion section. **Fix:** replace with the class-specific result; if a sentence about the *combined* all-roads distance is wanted, say explicitly that the single-distance term was uninformative *because* it pools opposing signals.

### C2. MAJOR — Curvature fossil in Results
> "We found less support for road proximity and curvature."

In the v4 model set, **curvature is in all three top models** (m13/m14/m15), its averaged coefficient is strongly supported (−0.42, 85% CI −0.55 – −0.29), and models without curvature sit ΔAICc ≥ 28 behind (`model_selection.csv`: m2/m7). This sentence described the 2024 ranking (where m7, no curvature, won). **Fix:** rewrite the model-support paragraph from the actual Table 3; add a curvature interpretation to the Discussion (see S10 — currently a significant covariate is never discussed at all).

### C3. MAJOR — Aspect significance list wrong (Results and Discussion)
> "Leks were less likely to be located on N-, NW-, S-, SW-, and W-facing slopes relative to E-facing slopes."

Against `averaged_betas.csv` at the paper's own 85% convention: **N (−0.14, CI −0.37 – +0.09) and S (−0.05, CI −0.28 – +0.17) are not distinguishable from zero; NE (−0.28, CI −0.52 – −0.05) is, and is omitted.** The correct list is NE, NW, SW, W. The same wrong sentence appears twice (Results ¶ after Fig. 6; Discussion aspect paragraph). This is the 2024 result pasted onto 2026 numbers.

### C4. MAJOR — Multicollinearity claim contradicted by its own figure
> "found no pairwise correlation more extreme than \|0.6\| (Fig. 3)"

Fig. 3 (`v4/figs/correlation.png`) displays **r = 0.99** between distance-to-any-road and distance-to-unpaved-road. The claim is false as written. The defensible statement: *no two predictors that co-occur in any candidate model exceed \|r\| = 0.48* (the three road-distance variables never share a model). **Fix:** rewrite precisely; a reviewer who reads the figure will not forgive the current sentence.

### C5. MAJOR — USGS contingency narrative does not match the included table
> "the gradient is monotone — 49% of the USGS lowest-selection cells fall in our lowest bin, and 40% of their highest-selection cells fall in our highest."

`v4/tables/usgs_contingency.md` (included two lines later) reads 23% for USGS cat 1 × ours-very-low and 22% for cat 4 × ours-very-high — and cat 4's row is not monotone (…22%, 23%, 22%). The 49/40 numbers belong to some earlier computation. **Fix:** recompute or restate from the current table ("the association is positive but modest; row proportions shift from 23%→17% across our bins for the lowest USGS category and 16%→22% for the highest"), and drop "monotone."

### C6. MAJOR — "10 categories" vegetation description contradicts Table 4
> "The vegetation cover layer had 10 categories: conifer, conifer-hardwood, exotic herbaceous, exotic tree-shrub, grassland, quarries…, riparian, shrubland, sparsely vegetated, and other."

Table 4 contains **13 contrasts + shrubland reference = 14 classes**, including Agricultural, Developed-Roads, Hardwood, and Open Water — none of which are in the Methods list. The list describes the LANDFIRE 2014 legend from the old draft, not LF2025 EVT_PHYS. Also unstated: `fit_models.R` collapses classes with <10 design points into "Other." **Fix:** enumerate the actual modeled classes and state the rare-class collapsing rule.

### C7. MAJOR — VIF claims false against vif.csv
> Methods: "all variables in all top models had VIF < 1.6." Results: "VIF … (1.0–1.6)."

`vif.csv`: maximum is **1.77** (m13 DirectionSE), with several Direction terms 1.69–1.77. Trivial substantively, fatal credibilibly — it signals unverified numbers. **Fix:** "all VIF < 1.8 (range 1.00–1.77)."

### C8. MAJOR — Figure numbering is broken
- Methods (RSF section): "…classified into five bins … (Fig. 4)" — but Fig. 4 is the used/available distributions figure; the prediction map is **Fig. 8**. Fossil of the 2024 numbering, where Fig. 4 *was* the map.
- "Figs. 2a–2b in supporting charts below" — the road charts are unnumbered images, not 2a/2b.
- ROC, Boyce, USGS side-by-side, bins-multiples, and zoom figures are unnumbered while neighbors are numbered.
**Fix:** renumber every figure and re-anchor every in-text reference; Quarto will not do it for you.

### C9. MINOR — Misrounded coefficients (Abstract and Results)
- VRM: reported "β = −1.01"; `averaged_betas.csv` says −1.0045 → **−1.00**.
- Paved: reported CI "0.04 – 0.17"; actual lower bound 0.0347 → **0.03**.
All other headline numbers check out (elevation 0.96 [0.87, 1.05]; slope −1.18 [−1.32, −1.04]; AUC 0.80/0.79 ± 0.01; spatial 0.80 ± 0.03; Boyce 0.99; ρ = 0.52 at 147,036 points; VRM means 0.00046/0.00197; road-length totals sum exactly to 100,790 km).

### C10. MINOR — Which model was cross-validated?
The text attributes AUC, random CV, and spatial CV to "the fitted model average." `diagnostics.csv` labels random CV "top model," and the ROC caption says "top model." State which object each metric belongs to.

### C11. MAJOR — Spatial validation was run on the wrong model
`validate_spatial.R` builds `form` = roads + curvature + ruggedness + slope + direction + elevation + vegetation with the *combined* `scale_RoadsProximity`, annotated `# m1 (top model)`. In the current selection, m1 ranks **4th** (ΔAICc 6.4); the top model is m13 (paved + unpaved). The reported spatial-block AUC (0.80 ± 0.03) and the lek-size Spearman (ρ = 0.068) therefore describe a model the paper does not report. Results will barely move, but as it stands the number is unattributable. **Fix:** rerun `validate_spatial.R` on m13 (or the average) and refresh `spatial_validation.csv`; delete the stale comment.

### C12. MINOR — S1 table doesn't do what the text says
Methods claim the study-area mean was compared for "each continuous variable," yet `validation.md` shows "—" (no study-area mean) for all three road-distance variables while still marking them "Covered: yes," and the **Ruggedness row is marked "Covered: no"** with no acknowledgment anywhere. Also "mean of the study area's pixels … at full raster resolution" is actually a 100,000-point Monte Carlo estimate — say so. The VRM coverage failure is substantive (see A3/S15).

### C13. MINOR — n = 718 vs. the record's 716
The 2024 draft, the REMA submission, and the Dec 2023 email thread ("It looks like in our paper we said 716 active leks?… the extra 9 … fall outside of the state of NV") all say **716** NV-active leks; this draft says **718** with no comment. Cause is visible in the code: `prepare_design.py` filters on the `STATE == "NV"` *attribute*, while the 2023 count was geometric containment — so "located within Nevada (n = 718)" is not literally what the pipeline does if any STATE=NV lek plots outside the boundary. **Fix:** reconcile the definition (attribute vs. geometry), state the criterion, and footnote the change from 716.

### C14. MINOR — The reference section is a diff, not a bibliography
"References [1]–[30] as in the 2024 draft (…) with the following updates and additions" is not submittable, and the body mixes numeric ([1], [36]) with author-year citations ("(WAFWA, 2015)", "(Coates et al., 2020)" in Study Area). Verify the numeric mapping while rebuilding: [6] is cited for population fragmentation *and* for lek counts indicating nesting habitat — in the REMA text both claims cited Crawford et al. 2004, but position 6 in the 2024 list is Van Horne 1983.

### C15. MINOR — Fossils in the pipeline itself (the pipeline is the methods)
- `extract_covariates.py` docstring: "Distance-to-road is computed against TIGER NV primary/secondary roads" — stale; all classes are used.
- The VRM covariate is stored in a column named `tri` (with a comment, but reviewers reading code will stumble).
- `validate_spatial.R`: `# m1 (top model)` (see C11).

### C16. MINOR — Distance surfaces: 90-m compute grid unstated
Methods say the Euclidean-distance surfaces were computed "on the DEM grid"; `build_roads_raster.sh`/`build_roads_by_class.sh` compute at 90 m and bilinearly resample to 30 m (error ≈ one 90-m cell). With used-lek mean distances of ~700 m, that is a ~10% relative error scale — state the approximation.

---

## Axis 2 — Against the archive

### A1. The 2023 REMA reviews, point by point

**Reviewer 1 (drove the rejection):**

| Criticism | Status in 2026 draft |
|---|---|
| Lek occurrence is driven by *nesting habitat suitability* at broader scales; without it "no applicability" | **NOT addressed structurally.** No landscape-composition covariates (e.g., % sagebrush within 1–5 km). The rebuttal is one uncited sentence ("vegetation patterns that influence nesting occur at much broader scales…") plus the external USGS correlation. Vulnerable — see S6 fix options. |
| A 30-m pixel meeting the criteria is not a lek; the qualifying area will be uselessly large | **NOT addressed.** The quantile map guarantees the top bin is exactly 20% of 152,458 km² (~30,500 km²). The caption even concedes "(equal-area by construction)." No lek-capture-per-bin statistic is reported. See S7. |
| Why no interaction terms, quadratics, or threshold models? | **NOT addressed, not even defended.** All 15 models are strictly linear-additive. See S5 fix. |
| "You must define what an 'active' lek is" | **NOT addressed.** Same sentence as 2024: categories listed, criterion never defined. This is a one-paragraph fix via the NDOW protocol — do it. |
| Not subsetting roads into classes is "non-sensical" | **ADDRESSED** (m13–m15; paved effect resolved). But see S4 (a-priori framing) and S11 (paved/unpaved mislabel). |

**Reviewer 2:**

| Criticism | Status |
|---|---|
| "Large standard errors [for intercept and vegetation categories] suggest model convergence or fit problem" — the stated reason for the revision designation | **PARTIALLY addressed.** EVT_PHYS (≈14 classes) replaced 44 SAF_SRM classes and the shrubland reference fixed the intercept. But Table 4 still carries Conifer-Hardwood (−13.1, CI −697 to 671), Hardwood (−14.3), Open Water (−14.3), and Other (−13.7) — textbook quasi-separation (zero used points in those classes). The same reviewer will make the same objection. See S6. |

**Reviewer 3:**

| Criticism | Status |
|---|---|
| Insufficient methods detail to replicate | **Largely addressed** (pipeline, sources, grains) — the strongest improvement. Residual gaps: standardization unstated (S12), curvature undefined (S10), flat-aspect handling unstated (S8), 90-m road grid (C16). |
| Confirmatory approach: categorize cover types by expected influence on sage-grouse | **NOT addressed** — EVT_PHYS used as-is. |
| Standardize covariates | **Done in code, never stated in text.** |
| Landcover *composition* in a broader landscape (Doherty et al. 2010) | **NOT addressed.** |
| Roads-only anthropogenic covariate is a weakness; include energy infrastructure/transmission/towers or justify | **NOT addressed, no justification added.** One sentence would do (e.g., statewide infrastructure layers of consistent vintage unavailable at 30 m). |
| Justify the 1:10 used:available ratio (Barbet-Massin et al. 2012) | **REGRESSED.** The 2024 draft at least attempted a (flawed) density justification; the 2026 draft removed all justification. See A3/S15. |
| Model validation (AUC, k-fold, PCC/sensitivity/specificity) | **ADDRESSED, and then some** — AUC, random CV, spatial CV, calibration, Boyce, external comparison. This is the paper's best answer to 2023. (But see C11.) |
| Discussion contradicted results on ruggedness ("relationships remain unclear") | Old text removed, but the ruggedness **sign flipped** between drafts (+0.14 → −1.00) and the metric changed (Eq.-1 index → VRM) with no disclosure. See A8. |
| m7 with 49 parameters unclear; aggregate cover types | Resolved (df now 24–27). |
| Quantify declines in abstract; "suitable" terminology; "ran"→"fit"; move computing narrative to supplement | Mostly adopted (declines still unquantified — trivial). |

**Associate Editor:** "appropriate for a more regional journal." The added validation, the road-class finding, and the reproducible pipeline are the generalizability argument — but only if the R1 structural gaps are answered, not just the R3 checklist.

### A2. MAJOR — The rejection-driving defect survives
See Reviewer 2 row above and S6. Table 4's four ±700-logit confidence intervals are the single most likely trigger for a repeat rejection.

### A3. MAJOR — Availability-sample justification regressed while its own diagnostic fails
7,180 available points over 152,458 km² is ~1 point per 21 km², for inference at 30-m grain — and the paper's own S1 table shows the available-sample 85% CI **fails to cover** the study-area VRM mean. No ratio justification, no citation, no acknowledgment of the failed row. **Fix:** either (a) increase the availability sample (this is free — the pipeline is scripted; 10:1 was a 2021 ArcGIS-era constraint, not a 2026 one) and show coefficient stability, or (b) justify 1:10 with citations and address the VRM row explicitly.

### A4–A7. See the R1/R3 table rows above (active-lek definition; nonlinearity; broader-scale context; anthropogenic covariates).

### A8. MAJOR — The silent ruggedness reversal
The 2024 draft reported ruggedness **+0.14** (selection *for* rugged terrain) and discussed it as contradicting Coates et al. The 2026 draft reports **−1.00** with a different metric and claims consistency with Coates — with no mention that the previous instrument produced the opposite sign. The pipeline documents why (`build_prediction.py`: the old Eq.-1 covariate was effectively **binary 0/1** — mean 0.454, SD 0.498 — i.e., the 2023 ruggedness index was defective). This is exactly the kind of change a returning REMA reviewer or editor will notice. **Fix:** one transparent supplementary paragraph: the original TRI implementation, why it was pathological, VRM as replacement, and the sign change as a correction, with the Lautenbach 2025 corroboration. This converts a liability into a strength.

### A9. Email-record cross-checks
- Total known leks (n = 1,989 in the 2024 draft; layer actually held 2,253 sites per the Dec 2023 thread) — the 2026 draft drops the total entirely. Reporting the parent-population count is standard; restore it with the correct number.
- The Dec 2023 buffer bug ("we had buffered all leks by 5 km … never revised it when we switched to active leks only") is fixed and documented in `prepare_design.py` — good, and the Methods sentence now matches the code.
- SAF_SRM → EVT_PHYS switch (Dec 2023) is consistently described.
- 716 vs 718: see C13.

### A10. Things the 2024 draft had that 2026 lost (restore)
1. Table-4 caption language: "values … obtained from the **full average**" and "**bold font** highlights covariates whose 85% CIs did not overlap zero" — both conventions vanished; the averaging type is now stated nowhere (see S5).
2. Any justification of the availability sample (see A3).
3. The total-lek denominator (A9).

### A11. The 2021 sheep-paper omen
REMA's reviewers went straight at autocorrelated locations and design validity in this team's 2021 sheep RSF, and the AE listed serial correlation as issue #1. Leks are not GPS fixes, but they **cluster in complexes**; 718 "independent" Bernoulli trials is optimistic. Expect the same reviewer instinct; see S1.

---

## Axis 3 — General good science

### S1. MAJOR — Spatial autocorrelation and pseudoreplication of clustered leks
Every 85% CI in Table 4 assumes independent observations. Neighboring leks share the same ridge systems, veg mosaics, and road networks; residual spatial autocorrelation would shrink effective n well below 718 and make the CIs anti-conservative. The spatially blocked CV is the right move for *predictive* honesty but does nothing for *inferential* honesty. **Fix (minimum):** Moran's I / correlogram on deviance residuals, reported. **Fix (better):** cluster bootstrap over lek complexes or a spatial GLMM/GEE sensitivity fit; state whether the headline CIs widen. **Fix (floor):** an explicit limitation paragraph. Given this team's 2021 review history, silence here is a known reviewer trigger.

### S2. MAJOR — Use-availability design leaks
1. `prepare_design.py` buffers *all* active leks outside the range polygon — including the ~9 out-of-state leks that are then **excluded from the used sample**. Their 5-km buffers (prime lekking landscape) enter the study area purely as "available," mildly biasing availability toward lek-like terrain. Either buffer only NV used leks or justify.
2. "Located within Nevada" vs the STATE-attribute filter (C13).
3. Available points may fall on leks — with 718 leks in 152k km² this is negligible; one sentence saying so inoculates it.

### S3. MAJOR — Temporal mismatch, unacknowledged
Lek status: **2018** (NDOW, dataset acquired 2020). Vegetation: **LF2025** (2026 release). Roads: TIGER **2024**. DEM tiles: 2013–2026. Nevada's sage-grouse range burned extensively after 2018 (e.g., the 2018 Martin Fire, the largest in state history, in core lek country). A lek listed active-2018 whose surrounding shrubland burned in 2018–2024 is now classified Grassland/Exotic Herbaceous by LF2025 — which means part of the reported grassland/herbaceous selection could be a **fire-reclassification artifact**, not display-ground ecology. The team's own `lit-review-2026.md` planned "an explicit statement that our lek-status vintage is 2018" — the statement never made it into the draft. **Fix (minimum):** limitation paragraph naming the vintages and the fire confound. **Fix (better):** sensitivity refit with a LANDFIRE vintage contemporaneous with the lek data (LF2016/LF2020); if grassland/exotic-herbaceous coefficients hold, the result is safe and demonstrably so.

### S4. MAJOR — "15 a priori models" is not an accurate history
`fit_models.R` says it plainly: "the 12 a priori RSF models, verbatim from the 2023 analysis" plus "Road-class a priori models (2026)." The road-class models were added *after* the all-roads term returned null in 2023–24, after Reviewer 1 demanded class subsetting, and after the 2024 draft's own Discussion recommended it. Calling all 15 "a priori" in the abstract and Methods is the kind of framing that, once noticed (and the same journal/editor may notice), reads as data dredging even though the underlying move is legitimate and hypothesis-driven. **Fix:** "Twelve candidate models retained from the original analysis, plus three road-class models specified before refitting the revised data, motivated by review and by Knick et al. (2013)." Transparency costs one clause and buys immunity.

### S5. MAJOR — Model-averaging choices unstated and undefended
- `fit_models.R` uses `coefmat.full` and `confint(avg, full = TRUE)` — the **full (zero-substituted) average** — but the text never says which average, and the 2024 caption that did say it was dropped. Full averaging shrinks terms absent from some models toward zero: unpaved distance appears in models carrying ~78% of renormalized weight, so its "marginal" CI (−0.199, +0.004) is partly a shrinkage artifact. Report the conditional average alongside, or interpret the top model; cite Grueber et al. 2011 / Banner & Higgs 2017; add Arnold 2010 for the 85% convention (currently uncited).
- "Top three models" is an arbitrary subset rule: it includes m15 (ΔAICc = 5.1) and excludes m1 (ΔAICc = 6.4). Use a Δ-threshold or cumulative-weight rule, or defend top-3.
- Nonlinearity (R1): at minimum, defend linearity or add quadratic elevation/slope to the candidate set; monotone response curves are currently guaranteed by construction, not discovered.

### S6. MAJOR — Quasi-separation in vegetation classes (the 2023 rejection, still live)
Conifer-Hardwood, Hardwood, Open Water, and Other have zero (or near-zero) used points → infinite MLEs, β ≈ −13/−14, SEs of 475–656, CIs spanning ±950. **Fix options:** (a) collapse all zero-used classes into a single "unused cover (no leks observed)" category — honest and simple; (b) Firth's penalized logistic regression (`logistf`/`brglm2`) for the whole model set; (c) report those classes as "complete avoidance (no leks observed; coefficient not estimable)" in the table rather than pretending the numbers are estimates. Any of the three defuses Reviewer 2. Doing nothing re-runs 2023.

### S7. MAJOR — Quantile bins can't answer the "is this useful?" question
Five equal-area bins mean the bins table is five rows of "20.0%" — information-free — and R1's core jab ("the qualifying area is so large it is not useful") stands. The data to answer him already exist: the Boyce table shows the top probability classes at P/E ≈ 5–8. **Fix:** report the *gain* statistic managers need — "the top quantile bin contains X% of all known active leks in one-fifth of the area; the top two bins contain Y%" — and/or offer a sensitivity-targeted threshold (e.g., the area needed to capture 90% of leks). That single number transforms the management story.

### S8. MINOR→MAJOR — Flat terrain is silently coded as "north-facing"
`build_dem.sh` uses `gdaldem aspect -zero_for_flat`; `extract_covariates.py` maps aspect ≤ 22.5° (including 0) to "N." Leks sit on conspicuously flat ground (mean slope 3.7° vs 8.2° available), so used points are disproportionately assigned Direction = N by convention, not by ecology — plausibly why DirectionN moved from significant (−0.32, 2024) to null (−0.14, 2026). The E-facing preference narrative (soil-moisture speculation in the Discussion) sits on top of this artifact. **Fix:** add a "Flat" category (e.g., slope < 1–2°) or model aspect as northness/eastness (sin/cos) with a flat indicator; at minimum, document the convention.

### S9. MINOR — 85% CIs uncited
The 85% convention pairs with AIC selection via Arnold (2010). Cite it or reviewers will read it as significance shopping.

### S10. MINOR — Curvature: undefined, significant, and undiscussed
The paper never says which curvature (profile? tangential? total?), and `build_dem.sh` itself warns that ArcGIS and GRASS conventions "differ by sign/scale." A coefficient of −0.42 with a strong CI is then uninterpretable to any reader — and the Discussion never mentions curvature at all. Define the measure, state the sign convention, and give it two Discussion sentences (concave/convex position of display grounds is ecologically interesting).

### S11. MINOR→MAJOR — "Paved vs unpaved" overstates what TIGER encodes
MTFCC is a *functional* classification; it does not encode surface. S1400 ("local neighborhood road, rural road, city street") includes paved streets; meanwhile S1740 private service roads (988 km — typically unpaved mine/ranch access) are excluded from **both** class surfaces, even though the paper's own Table 2 groups S1740 with the low-usage class. **Fix:** rename the covariates to what they are (primary/secondary-highway distance vs local-road-and-trail distance), reconcile Table 2's grouping with the model split (or justify excluding S1740), and note that surface type is inferred, not encoded.

### S12. MINOR — Standardization unstated
All continuous covariates are z-scored (`scale()` in R; training moments reused for prediction in `build_prediction.py`). The Methods never say so; Table 4's magnitudes are uninterpretable without it. One sentence.

### S13. MINOR — External validation: temper and correct
ρ = 0.52 against a telemetry-based, broader-scale seasonal-selection product is a reasonable, *moderate* agreement — the honest framing is that full agreement is neither expected nor desirable (different response, different scale). Fix the contingency narrative (C5) and drop "aligned with independent data" phrasing in favor of the number.

### S14. MINOR — "Well calibrated" and the meaning of "probability"
Decile 4 predicts 0.031 vs observed 0.014 (2.2× over) — "well calibrated across deciles" overstates. More fundamentally, with a 1:10 use-availability design the fitted values are **relative selection intensities**, not absolute occurrence probabilities (Keating & Cherry 2004); the map legend and abstract's "probability of lek occurrence" language should be softened to "relative probability/selection intensity" — this also preempts a classic RSF-methods reviewer.

### S15. See A3 — availability sample size and the failed VRM coverage row.

### S16. MINOR — Shrubland reference class
Sensible (dominant cover; ecological null for a sagebrush obligate) but never justified in text. One clause.

### S17. MINOR — "Every run is exactly reproducible" is overclaimed
`fetch_tnm.py` deduplicates DEM tiles to the *most recent publication per cell* — a rerun after USGS publishes new lidar fetches different tiles by design. Reproducibility holds *conditional on the archived manifests/inputs*, which is the claim to make (and pin the manifest in the repo). Also "every acquisition writes a provenance manifest" — true for TNM; `fetch_roads_all.py` writes none.

---

## Axis 4 — Writing and register

W1. **Abstract carries a README paragraph.** "The analysis is implemented as a fully scripted, openly licensed pipeline in which every environmental input is fetched from its authoritative public source and every run is exactly reproducible" — promotional, partly overclaimed (S17), and not a result. Move to a Data Availability / Code Availability statement; one neutral Methods sentence suffices.

W2. **Machine-flavored aphorisms.** These read as generated-text patterns, not REM register:
- "The class-split models outranked every single-distance formulation, indicating road type — not road presence — is the ecologically relevant axis."
- "display grounds occupy terrain roughly four times smoother than the landscape offers"
- "aligned with independent data while retaining the complementary, lek-specific information of this analysis"
- "making lek-scale conifer avoidance directly actionable for treatment prioritization"
Each should become a plain declarative with the number doing the work.

W3. **Internal contradictions in promotional claims.** "VRM … is decorrelated from slope by construction (r = 0.40 in our design)" — 0.40 is not decorrelated, and VRM is designed to be *less* slope-confounded, not orthogonal. "It is the standard ruggedness metric in wildlife habitat analysis" — overclaim; "widely used" with the citation.

W4. **Caption salesmanship.** "The highest-probability class alone constitutes the survey-targeting product: one-fifth of the study area capturing the terrain-and-vegetation conditions of active leks" — 30,500 km² is not a targeting product (see S7); rewrite once the lek-capture statistic exists.

W5. **Internal artifacts leaking into the manuscript.** Subtitle "(v4 pipeline)"; Table 4 rows named `scale_Elevation`, `DirectionN`, `VegetationConifer`; model IDs m13/m14/m15 unexplained to readers. Clean for submission.

W6. **Uncited load-bearing claim.** "males primarily select display areas in response to hens' preference for proximal nesting habitat" — this is the paper's entire rebuttal to Reviewer 1 and it carries no citation (Gibson 1996 / Bradbury et al. would serve).

W7. **Abstract precision.** "herbaceous cover types were favored" — plural overreaches: grassland's CI excludes zero; exotic herbaceous (+0.21, CI −0.05 – +0.47) does not. Also "favored over conifer" reads as a direct contrast when both are contrasts to shrubland.

W8. **References.** Rebuild the list (C14); unify citation style; quantify the abstract's "significant population reduction" if keeping R3's suggestion.

---

## Recommended fix order (what a rejection would actually ride on)

1. Purge the fossils: C1, C2, C3, C4, C5, C6, C7, C8 — every one is a prose-vs-own-table contradiction a reviewer can find with a highlighter.
2. Rerun spatial validation on m13 (C11); refresh numbers.
3. Fix separation (S6) — the documented 2023 rejection cause.
4. Reframe the 15-model history honestly (S4) and state the averaging type (S5).
5. Add the three limitation paragraphs the archive demands: spatial autocorrelation (S1), temporal mismatch (S3), availability sample + VRM coverage (A3).
6. Answer R1 where it's cheap: define "active" (A4); report lek-capture-per-bin (S7); cite the nesting-scale claim (W6); justify roads-only (A7).
7. De-promotionalize the abstract and captions (W1–W4); rebuild references (C14).

Items 1–2 are hours. Items 3–5 are days. Item 6 is the difference between resubmitting the 2023 paper with better plumbing and submitting a paper the 2023 reviewers would pass.

— end of review —
