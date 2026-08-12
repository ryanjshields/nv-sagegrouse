#!/usr/bin/env Rscript
# test_r_models.R -- adversarial checks on pipeline/fit_models.R.
#
# Run: Rscript tests/test_r_models.R
#
# No lek data is touched. The a priori formulas are checked by PARSING the
# pipeline source (never by running it, which would require data-local/), and
# the separation guard and AICc ranking are exercised on synthetic frames built
# here with a fixed seed.

suppressPackageStartupMessages(library(MuMIn))

root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
fit_models_path <- file.path(root, "pipeline", "fit_models.R")
stopifnot("pipeline/fit_models.R must exist" = file.exists(fit_models_path))

pass <- function(msg) cat("ok   -", msg, "\n")

# ---------------------------------------------------------------------------
# 1. The 12 a priori formulas are VERBATIM from the 2023 analysis.
#
# fit_models.R:2 claims these are unchanged from
# history/ModAvg_ActiveOnly_LandJournal.R. Any silent edit -- a dropped term, a
# reordered predictor, a swapped covariate -- would change the entire model
# ranking while every downstream script kept running. This canonical list is the
# tripwire: if the pipeline changes, this file must be edited deliberately.
# ---------------------------------------------------------------------------
CANONICAL_FORMULAS <- c(
  m1  = "Use ~ scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation",
  m2  = "Use ~ scale_RoadsProximity + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation",
  m3  = "Use ~ scale_RoadsProximity + scale_Ruggedness + scale_Slope + Vegetation",
  m4  = "Use ~ scale_RoadsProximity + scale_Ruggedness + Direction + scale_Elevation + Vegetation",
  m5  = "Use ~ scale_Curvature + scale_Slope + scale_Elevation + Vegetation",
  m6  = "Use ~ scale_RoadsProximity + scale_Slope + Vegetation",
  m7  = "Use ~ scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation",
  m8  = "Use ~ scale_RoadsProximity + scale_Slope + Direction + scale_Elevation + Vegetation",
  m9  = "Use ~ scale_RoadsProximity + scale_Curvature + scale_Slope + Vegetation",
  m10 = "Use ~ scale_Slope + scale_Elevation + Vegetation",
  m11 = "Use ~ scale_Ruggedness + scale_Slope + Vegetation",
  m12 = "Use ~ scale_RoadsProximity + Direction + scale_Elevation + Vegetation"
)

# The three 2026 road-class models are not part of the verbatim-2023 guarantee,
# but they drive the reported top-3 average, so they are pinned too.
CANONICAL_ROAD_CLASS_FORMULAS <- c(
  m13 = "Use ~ scale_PavedProximity + scale_UnpavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation",
  m14 = "Use ~ scale_PavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation",
  m15 = "Use ~ scale_UnpavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation"
)

source_lines <- readLines(fit_models_path, warn = FALSE)

extract_formula <- function(model_name) {
  pattern <- paste0("^\\s*", model_name, "\\s*<-\\s*glm\\(")
  hits <- grep(pattern, source_lines, value = TRUE)
  if (length(hits) != 1L) {
    stop(sprintf("Expected exactly one glm() definition for %s, found %d", model_name, length(hits)))
  }
  inner <- sub("^\\s*[A-Za-z0-9_.]+\\s*<-\\s*glm\\(", "", hits)
  formula_text <- sub(",\\s*data\\s*=.*$", "", inner)
  # Collapse runs of whitespace so alignment padding is not mistaken for drift.
  trimws(gsub("\\s+", " ", formula_text))
}

for (model_name in names(CANONICAL_FORMULAS)) {
  found <- extract_formula(model_name)
  expected <- CANONICAL_FORMULAS[[model_name]]
  if (!identical(found, expected)) {
    stop(sprintf("A priori formula drift in %s\n  expected: %s\n  found:    %s", model_name, expected, found))
  }
}
pass(sprintf("the %d a priori formulas match the canonical 2023 list verbatim", length(CANONICAL_FORMULAS)))

for (model_name in names(CANONICAL_ROAD_CLASS_FORMULAS)) {
  found <- extract_formula(model_name)
  expected <- CANONICAL_ROAD_CLASS_FORMULAS[[model_name]]
  if (!identical(found, expected)) {
    stop(sprintf("Road-class formula drift in %s\n  expected: %s\n  found:    %s", model_name, expected, found))
  }
}
pass("the 3 road-class formulas (m13-m15) match their canonical definitions")

# Guard the count itself: an added m16 that never reaches model.sel(), or a
# deleted model, would otherwise slip past the per-name checks above.
glm_definition_count <- length(grep("^\\s*m[0-9]+\\s*<-\\s*glm\\(", source_lines))
stopifnot("fit_models.R must define exactly 15 candidate models" = glm_definition_count == 15L)

model_sel_line <- grep("^\\s*sel\\s*<-\\s*model\\.sel\\(", source_lines, value = TRUE)
stopifnot("fit_models.R must call model.sel() exactly once" = length(model_sel_line) == 1L)
ranked_models <- trimws(strsplit(gsub(".*model\\.sel\\(|\\).*", "", model_sel_line), ",")[[1]])
stopifnot(
  "model.sel() must rank all 15 candidate models" =
    identical(sort(ranked_models), sort(paste0("m", 1:15)))
)
pass("all 15 defined models are passed to model.sel(), none orphaned")

# ---------------------------------------------------------------------------
# 2. The separation guard.
#
# fit_models.R:36 pools classes with < 10 TOTAL sites; fit_models.R:39-41 then
# pools any class holding < 5 USED leks. The boundary is >= 5, so a class with
# exactly 5 used leks must SURVIVE and a class with 4 must be pooled. Getting
# this backwards reintroduces the quasi-separation that produced |beta| ~ 14
# with SE ~ 500 in earlier fits.
# ---------------------------------------------------------------------------
apply_separation_guard <- function(veg, use) {
  # Verbatim reimplementation of fit_models.R:34-41.
  veg <- as.character(veg)
  veg[is.na(veg) | veg == ""] <- "Other"
  tab <- table(veg)
  veg[veg %in% names(tab[tab < 10])] <- "Other"
  used_tab <- table(veg[use == 1])
  zero_used <- setdiff(unique(veg), names(used_tab[used_tab >= 5]))
  veg[veg %in% zero_used] <- "Other"
  veg
}

make_class <- function(label, n_used, n_available) {
  data.frame(
    veg = rep(label, n_used + n_available),
    use = c(rep(1L, n_used), rep(0L, n_available)),
    stringsAsFactors = FALSE
  )
}

guard_frame <- rbind(
  make_class("Shrubland", 40, 200),   # reference class, comfortably retained
  make_class("KeptFive", 5, 30),      # exactly 5 used leks -> must SURVIVE
  make_class("PooledFour", 4, 30),    # 4 used leks -> must be pooled into Other
  make_class("RareTotal", 3, 4),      # 7 total sites -> pooled by the < 10 total rule
  make_class("Other", 6, 40)          # a real Other class already present
)
guarded <- apply_separation_guard(guard_frame$veg, guard_frame$use)

stopifnot(
  "a class with exactly 5 used leks must be retained" =
    all(guarded[guard_frame$veg == "KeptFive"] == "KeptFive")
)
stopifnot(
  "a class with 4 used leks must be pooled into Other" =
    all(guarded[guard_frame$veg == "PooledFour"] == "Other")
)
stopifnot(
  "a class with fewer than 10 total sites must be pooled into Other" =
    all(guarded[guard_frame$veg == "RareTotal"] == "Other")
)
stopifnot(
  "the shrubland reference must never be pooled" =
    all(guarded[guard_frame$veg == "Shrubland"] == "Shrubland")
)
stopifnot(
  "pooling must not invent classes beyond the surviving set" =
    setequal(unique(guarded), c("Shrubland", "KeptFive", "Other"))
)
pass("separation guard pools the 4-used-lek class and keeps the 5-used-lek class")

# Empty and NA vegetation strings must land in Other rather than becoming their
# own factor level (fit_models.R:35).
blank_frame <- rbind(
  make_class("Shrubland", 40, 200),
  data.frame(veg = c(NA_character_, "", NA_character_), use = c(1L, 0L, 0L), stringsAsFactors = FALSE)
)
blank_guarded <- apply_separation_guard(blank_frame$veg, blank_frame$use)
stopifnot(
  "NA and empty vegetation must be folded into Other" =
    all(blank_guarded[is.na(blank_frame$veg) | blank_frame$veg == ""] == "Other")
)
pass("NA and empty vegetation strings are folded into Other")

# ---------------------------------------------------------------------------
# 3. AICc ranking is deterministic on a fixed synthetic dataset.
#
# model.sel() ordering feeds top3_names, which feeds the model average, the
# reported betas and every number in the paper. A ranking that varied between
# runs on identical input would make the whole report irreproducible.
# ---------------------------------------------------------------------------
set.seed(20260811)
n <- 600
synthetic <- data.frame(
  scale_Slope = rnorm(n),
  scale_Elevation = rnorm(n),
  scale_Ruggedness = rnorm(n),
  scale_Curvature = rnorm(n)
)
eta <- -2.0 - 1.3 * synthetic$scale_Slope + 0.9 * synthetic$scale_Elevation - 1.0 * synthetic$scale_Ruggedness
synthetic$Use <- as.factor(rbinom(n, 1, 1 / (1 + exp(-eta))))

s1 <- glm(Use ~ scale_Slope, data = synthetic, family = "binomial")
s2 <- glm(Use ~ scale_Slope + scale_Elevation, data = synthetic, family = "binomial")
s3 <- glm(Use ~ scale_Slope + scale_Elevation + scale_Ruggedness, data = synthetic, family = "binomial")
s4 <- glm(Use ~ scale_Curvature, data = synthetic, family = "binomial")

first <- as.data.frame(model.sel(s1, s2, s3, s4))
second <- as.data.frame(model.sel(s1, s2, s3, s4))

stopifnot("model.sel ordering must be identical across repeated calls" = identical(rownames(first), rownames(second)))
stopifnot(
  "AICc values must be bit-identical across repeated calls" =
    isTRUE(all.equal(first$AICc, second$AICc, tolerance = 0))
)
stopifnot("AICc must be sorted ascending" = !is.unsorted(first$AICc))
stopifnot("delta of the top model must be exactly 0" = first$delta[1] == 0)
stopifnot("Akaike weights must sum to 1" = abs(sum(first$weight) - 1) < 1e-9)

# The generative model included slope, elevation and ruggedness, so the full
# model must win; a ranking that put the curvature-only model on top would mean
# the AICc comparison is not doing what the pipeline assumes.
stopifnot("the correctly specified model must rank first" = rownames(first)[1] == "s3")
stopifnot("the curvature-only model must rank last" = rownames(first)[nrow(first)] == "s4")
pass("AICc ranking is deterministic, sorted, weight-normalised and recovers the true model")

# ---------------------------------------------------------------------------
# 4. The base-R VIF helper (fit_models.R:13-16).
# ---------------------------------------------------------------------------
base_vif <- function(m) {
  mm <- model.matrix(m)[, -1, drop = FALSE]
  diag(solve(cor(mm)))
}
independent_vif <- base_vif(s3)
stopifnot("VIF must be >= 1 for every term" = all(independent_vif >= 1 - 1e-9))
stopifnot("uncorrelated synthetic predictors must have VIF near 1" = all(independent_vif < 1.2))

collinear <- synthetic
collinear$scale_Twin <- collinear$scale_Slope + rnorm(n, sd = 0.01)
collinear_fit <- glm(Use ~ scale_Slope + scale_Twin, data = collinear, family = "binomial")
stopifnot(
  "a near-duplicate predictor must produce a VIF far above the 10 threshold" =
    all(base_vif(collinear_fit) > 10)
)
pass("base_vif returns ~1 for independent predictors and blows up on a near-duplicate")

cat("\nALL R MODEL TESTS PASSED\n")
