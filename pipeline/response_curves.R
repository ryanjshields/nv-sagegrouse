#!/usr/bin/env Rscript
# response_curves.R -- marginal response curves, coefficient forest plot, and
# ROC curve for the averaged model. Base R graphics; writes PNGs to
# reports/v4/figs/.
suppressPackageStartupMessages(library(MuMIn))
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
rsf <- read.csv(file.path(root, "data-local/design/model_input.csv"))
figs <- file.path(root, "reports/v4/figs")

rsf$Use <- as.factor(rsf$use)
rsf$scale_Curvature      <- as.numeric(scale(rsf$curvature))
rsf$scale_RoadsProximity <- as.numeric(scale(rsf$dist_road_m))
rsf$scale_PavedProximity   <- as.numeric(scale(rsf$dist_paved_m))
rsf$scale_UnpavedProximity <- as.numeric(scale(rsf$dist_unpaved_m))
rsf$scale_Elevation <- as.numeric(scale(rsf$elevation))
rsf$scale_Ruggedness <- as.numeric(scale(rsf$tri))
rsf$scale_Slope <- as.numeric(scale(rsf$slope))
rsf$Direction <- as.factor(rsf$direction)
veg <- as.character(rsf$evt_phys); veg[is.na(veg) | veg == ""] <- "Other"
tab <- table(veg); veg[veg %in% names(tab[tab < 10])] <- "Other"
rsf$Vegetation <- relevel(as.factor(veg), ref = "Shrubland")

m13 <- glm(Use ~ scale_PavedProximity + scale_UnpavedProximity + scale_Curvature +
             scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation,
           data = rsf, family = "binomial")

# --- response curves (top model, others at reference/mean=0) -------------------
vars <- list(
  c("scale_Slope", "slope", "Slope (°)"),
  c("scale_Elevation", "elevation", "Elevation (m)"),
  c("scale_Ruggedness", "tri", "Ruggedness (VRM)"),
  c("scale_PavedProximity", "dist_paved_m", "Distance to paved road (km)"),
  c("scale_UnpavedProximity", "dist_unpaved_m", "Distance to unpaved road (km)"))
png(file.path(figs, "response_curves.png"), width = 2100, height = 1300, res = 200)
par(mfrow = c(2, 3), mar = c(4, 4, 2, 1))
for (v in vars) {
  sv <- v[1]; raw <- v[2]; lab <- v[3]
  grid <- seq(quantile(rsf[[raw]], 0.01), quantile(rsf[[raw]], 0.99), length.out = 120)
  zgrid <- (grid - mean(rsf[[raw]])) / sd(rsf[[raw]])
  nd <- data.frame(scale_PavedProximity = 0, scale_UnpavedProximity = 0,
                   scale_Curvature = 0, scale_Ruggedness = 0, scale_Slope = 0,
                   scale_Elevation = 0,
                   Direction = factor("E", levels = levels(rsf$Direction)),
                   Vegetation = factor("Shrubland", levels = levels(rsf$Vegetation)))
  nd <- nd[rep(1, length(zgrid)), ]; nd[[sv]] <- zgrid
  pr <- predict(m13, nd, type = "link", se.fit = TRUE)
  inv <- function(x) 1 / (1 + exp(-x))
  xplot <- if (grepl("km", lab)) grid / 1000 else grid
  plot(xplot, inv(pr$fit), type = "l", lwd = 2, col = "#3a6ea5",
       ylim = c(0, max(inv(pr$fit + 1.44 * pr$se.fit))), xlab = lab,
       ylab = "P(lek)", main = "")
  lines(xplot, inv(pr$fit + 1.44 * pr$se.fit), lty = 2, col = "#3a6ea5")
  lines(xplot, inv(pr$fit - 1.44 * pr$se.fit), lty = 2, col = "#3a6ea5")
}
plot.new()
title(main = "", outer = TRUE)
dev.off()

# --- forest plot of averaged coefficients ---------------------------------------
b <- read.csv(file.path(root, "reports/v4/averaged_betas.csv"), row.names = 1)
b <- b[!grepl("Intercept", rownames(b)), ]
keep <- c(grep("^scale_", rownames(b), value = TRUE),
          grep("^Direction", rownames(b), value = TRUE),
          grep("^Vegetation", rownames(b), value = TRUE))
b <- b[keep, ]
lab <- gsub("^scale_", "", rownames(b)); lab <- gsub("^Vegetation", "Veg: ", lab)
lab <- gsub("^Direction", "Aspect: ", lab)
o <- order(b$Estimate)
png(file.path(figs, "forest.png"), width = 1500, height = 1800, res = 200)
par(mar = c(4, 12, 2, 1))
plot(b$Estimate[o], seq_along(o), pch = 19, col = "#3a6ea5",
     xlim = range(c(b$ci85_low, b$ci85_high)), yaxt = "n",
     xlab = "standardized coefficient (85% CI)", ylab = "",
     main = "Model-averaged effects (top three models)")
segments(b$ci85_low[o], seq_along(o), b$ci85_high[o], seq_along(o), col = "#3a6ea5")
abline(v = 0, col = "#999")
axis(2, at = seq_along(o), labels = lab[o], las = 1, cex.axis = 0.7)
dev.off()

# --- ROC curve -------------------------------------------------------------------
avgfile <- file.path(root, "reports/v4/averaged_betas.csv")
p <- predict(m13, type = "response")
y <- as.numeric(as.character(rsf$Use))
th <- sort(unique(quantile(p, seq(0, 1, 0.002))))
tpr <- sapply(th, function(t) mean(p[y == 1] >= t))
fpr <- sapply(th, function(t) mean(p[y == 0] >= t))
png(file.path(figs, "roc.png"), width = 1100, height = 1100, res = 200)
par(mar = c(4, 4, 2, 1))
plot(fpr, tpr, type = "l", lwd = 2, col = "#3a6ea5", xlab = "false positive rate",
     ylab = "true positive rate", main = "ROC, top model (AUC = 0.80)")
abline(0, 1, col = "#999", lty = 2)
dev.off()
cat("CURVES_COMPLETE\n")
