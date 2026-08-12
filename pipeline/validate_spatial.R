#!/usr/bin/env Rscript
# validate_spatial.R -- spatially honest validation of the RSF.
#  1. Spatially blocked 5-fold CV: k-means clusters on coordinates define
#     folds, so no lek's neighbors leak into its training set.
#  2. Lek-size axis: Spearman correlation between peak male counts and the
#     predicted probability at each used lek.
# Writes reports/v4/spatial_validation.csv

suppressPackageStartupMessages(library(MuMIn))
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
rsf <- read.csv(file.path(root, "data-local/design/model_input.csv"))

rsf$Use                  <- as.factor(rsf$use)
rsf$scale_Curvature      <- as.numeric(scale(rsf$curvature))
rsf$scale_RoadsProximity <- as.numeric(scale(rsf$dist_road_m))
rsf$scale_Elevation      <- as.numeric(scale(rsf$elevation))
rsf$scale_Ruggedness     <- as.numeric(scale(rsf$tri))
rsf$scale_Slope          <- as.numeric(scale(rsf$slope))
rsf$Direction            <- as.factor(rsf$direction)
veg <- as.character(rsf$evt_phys); veg[is.na(veg) | veg == ""] <- "Other"
tab <- table(veg); veg[veg %in% names(tab[tab < 10])] <- "Other"
rsf$Vegetation <- relevel(as.factor(veg), ref = "Shrubland")

form <- Use ~ scale_RoadsProximity + scale_Curvature + scale_Ruggedness +
  scale_Slope + Direction + scale_Elevation + Vegetation   # m1 (top model)

auc <- function(y, p) { r <- rank(p); n1 <- sum(y == 1); n0 <- sum(y == 0)
  (sum(r[y == 1]) - n1 * (n1 + 1) / 2) / (n1 * n0) }

# --- 1. Spatially blocked CV ---------------------------------------------------
set.seed(20260811)
km <- kmeans(rsf[, c("x", "y")], centers = 5, nstart = 10)
rsf$block <- km$cluster
res <- sapply(1:5, function(k) {
  tr <- rsf[rsf$block != k, ]; te <- rsf[rsf$block == k, ]
  # guard: a block may lack some factor level -- drop unseen levels from test
  te <- te[te$Vegetation %in% unique(tr$Vegetation) & te$Direction %in% unique(tr$Direction), ]
  fit <- glm(form, data = tr, family = "binomial")
  c(auc = auc(as.numeric(as.character(te$Use)), predict(fit, te, type = "response")),
    n_test_used = sum(te$use == 1))
})
sp_auc <- res["auc", ]; n_used <- res["n_test_used", ]

# --- 2. Lek-size axis ----------------------------------------------------------
leks <- read.csv(file.path(root, "data-local/leks_all.csv"))
names(leks) <- trimws(names(leks))
fit_all <- glm(form, data = rsf, family = "binomial")
rsf$p_hat <- predict(fit_all, type = "response")
used <- rsf[rsf$use == 1, c("lekid", "p_hat")]
m <- merge(used, leks[, c("LEKID", "PEAKMALE")], by.x = "lekid", by.y = "LEKID")
m <- m[!is.na(m$PEAKMALE) & m$PEAKMALE > 0, ]
size_cor <- cor(m$p_hat, m$PEAKMALE, method = "spearman")

out <- data.frame(
  metric = c(paste0("spatial-block AUC fold ", 1:5), "spatial-block AUC mean",
             "spatial-block AUC sd", "random-fold AUC (reference)",
             "lek-size Spearman (p_hat vs PEAKMALE)", "n leks with counts"),
  value = c(round(sp_auc, 3), round(mean(sp_auc), 3), round(sd(sp_auc), 3),
            0.791, round(size_cor, 3), nrow(m)))
write.csv(out, file.path(root, "reports/v4/spatial_validation.csv"), row.names = FALSE)
cat("spatial-block AUC:", round(mean(sp_auc), 3), "+/-", round(sd(sp_auc), 3),
    "(folds:", paste(round(sp_auc, 2), collapse = " "), "| held-out used per fold:",
    paste(n_used, collapse = " "), ")\n")
cat("lek-size Spearman:", round(size_cor, 3), "on", nrow(m), "leks\n")
cat("SPATIAL_VALIDATION_COMPLETE\n")
