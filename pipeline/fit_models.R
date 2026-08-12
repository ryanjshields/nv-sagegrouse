#!/usr/bin/env Rscript
# fit_models.R -- the 12 a priori RSF models, verbatim from the 2023 analysis
# (history/ModAvg_ActiveOnly_LandJournal.R), refit on the v4 design.
# Reads  data-local/design/model_input.csv
# Writes reports/v4/{model_selection.csv, averaged_betas.csv, vif.csv}

if (!requireNamespace("MuMIn", quietly = TRUE))
  install.packages("MuMIn", repos = "https://cloud.r-project.org", quiet = TRUE)
suppressPackageStartupMessages(library(MuMIn))

# VIF in base R (car::vif's numeric core): diag of the inverse correlation
# matrix of the model matrix, intercept dropped. Equivalent for our all-additive models.
base_vif <- function(m) {
  mm <- model.matrix(m)[, -1, drop = FALSE]
  diag(solve(cor(mm)))
}

root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
rsf <- read.csv(file.path(root, "data-local/design/model_input.csv"))
dir.create(file.path(root, "reports/v4"), recursive = TRUE, showWarnings = FALSE)

# -- Variables, named as in the 2023 code --------------------------------------
rsf$Use                  <- as.factor(rsf$use)
rsf$scale_Curvature      <- as.numeric(scale(rsf$curvature))
rsf$scale_RoadsProximity <- as.numeric(scale(rsf$dist_road_m))
if ("dist_paved_m" %in% names(rsf)) {
  rsf$scale_PavedProximity   <- as.numeric(scale(rsf$dist_paved_m))
  rsf$scale_UnpavedProximity <- as.numeric(scale(rsf$dist_unpaved_m))
}
rsf$scale_Elevation      <- as.numeric(scale(rsf$elevation))
rsf$scale_Ruggedness     <- as.numeric(scale(rsf$tri))
rsf$scale_Slope          <- as.numeric(scale(rsf$slope))
rsf$Direction            <- as.factor(rsf$direction)          # ref = "E" (alphabetical), as in 2023
veg <- as.character(rsf$evt_phys)
veg[is.na(veg) | veg == ""] <- "Other"
tab <- table(veg); veg[veg %in% names(tab[tab < 10])] <- "Other"  # collapse rare classes, as in 2023
rsf$Vegetation <- {rf <- if ("Shrubland" %in% veg) "Shrubland" else names(sort(table(veg), decreasing=TRUE))[1]; relevel(as.factor(veg), ref = rf)}

# -- The 12 a priori models, verbatim ------------------------------------------
m1  <- glm(Use ~ scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m2  <- glm(Use ~ scale_RoadsProximity + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m3  <- glm(Use ~ scale_RoadsProximity + scale_Ruggedness + scale_Slope + Vegetation, data = rsf, family = "binomial")
m4  <- glm(Use ~ scale_RoadsProximity + scale_Ruggedness + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m5  <- glm(Use ~ scale_Curvature + scale_Slope + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m6  <- glm(Use ~ scale_RoadsProximity + scale_Slope + Vegetation, data = rsf, family = "binomial")
m7  <- glm(Use ~ scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m8  <- glm(Use ~ scale_RoadsProximity + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m9  <- glm(Use ~ scale_RoadsProximity + scale_Curvature + scale_Slope + Vegetation, data = rsf, family = "binomial")
m10 <- glm(Use ~ scale_Slope + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m11 <- glm(Use ~ scale_Ruggedness + scale_Slope + Vegetation, data = rsf, family = "binomial")
m12 <- glm(Use ~ scale_RoadsProximity + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
# Road-class a priori models (2026): decompose the all-roads association.
m13 <- glm(Use ~ scale_PavedProximity + scale_UnpavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m14 <- glm(Use ~ scale_PavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")
m15 <- glm(Use ~ scale_UnpavedProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = rsf, family = "binomial")

sel <- model.sel(m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12, m13, m14, m15)
write.csv(as.data.frame(sel), file.path(root, "reports/v4/model_selection.csv"))

top3_names <- rownames(as.data.frame(sel))[1:3]
top3 <- mget(top3_names)
cat("road-class betas (m13):\n")
print(round(summary(m13)$coefficients[c("scale_PavedProximity","scale_UnpavedProximity"), 1:2], 4))
avg <- model.avg(top3)
s <- summary(avg)
betas <- as.data.frame(s$coefmat.full)
ci <- confint(avg, level = 0.85, full = TRUE)
betas$ci85_low  <- ci[, 1]
betas$ci85_high <- ci[, 2]
write.csv(betas, file.path(root, "reports/v4/averaged_betas.csv"))

vifs <- do.call(rbind, lapply(top3_names, function(n) {
  v <- base_vif(get(n)); data.frame(model = n, term = names(v), vif = v)
}))
write.csv(vifs, file.path(root, "reports/v4/vif.csv"), row.names = FALSE)

cat("top 3 models:", paste(top3_names, collapse = ", "), "\n")
key <- c("scale_Ruggedness", "scale_Elevation", "scale_Slope")
print(round(betas[rownames(betas) %in% key, c("Estimate", "ci85_low", "ci85_high")], 3))
cat("MODEL_FIT_COMPLETE\n")

# -- Diagnostics: AUC, 5-fold CV, calibration (base R, no extra packages) ------
auc <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0)
  (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }
p_full <- predict(avg, type = "response")
set.seed(20260811)
folds <- sample(rep(1:5, length.out = nrow(rsf)))
cv_auc <- sapply(1:5, function(k) {
  fit <- glm(formula(get(top3_names[1])), data = rsf[folds != k, ], family = "binomial")
  auc(as.numeric(as.character(rsf$Use[folds == k])), predict(fit, rsf[folds == k, ], type = "response"))
})
y <- as.numeric(as.character(rsf$Use))
dec <- cut(p_full, quantile(p_full, seq(0, 1, 0.1)), include.lowest = TRUE, labels = FALSE)
calib <- data.frame(decile = 1:10,
                    mean_predicted = tapply(p_full, dec, mean),
                    observed_rate  = tapply(y, dec, mean))
write.csv(calib, file.path(root, "reports/v4/calibration.csv"), row.names = FALSE)
diag_df <- data.frame(metric = c("AUC (full model average)", "AUC (5-fold CV, top model)", "CV sd"),
                      value = c(auc(y, p_full), mean(cv_auc), sd(cv_auc)))
write.csv(diag_df, file.path(root, "reports/v4/diagnostics.csv"), row.names = FALSE)
cat("AUC full:", round(auc(y, p_full), 3), "| CV AUC:", round(mean(cv_auc), 3), "+/-", round(sd(cv_auc), 3), "\n")
cat("DIAGNOSTICS_COMPLETE\n")
