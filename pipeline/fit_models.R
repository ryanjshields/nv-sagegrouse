#!/usr/bin/env Rscript
# fit_models.R -- the 12 a priori RSF models, verbatim from the 2023 analysis
# (history/ModAvg_ActiveOnly_LandJournal.R), refit on the v4 design.
# Reads  data-local/design/model_input.csv
# Writes reports/v4/{model_selection.csv, averaged_betas.csv, vif.csv}

for (p in c("MuMIn", "car")) if (!requireNamespace(p, quietly = TRUE))
  install.packages(p, repos = "https://cloud.r-project.org", quiet = TRUE)
suppressPackageStartupMessages({ library(MuMIn); library(car) })

root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
rsf <- read.csv(file.path(root, "data-local/design/model_input.csv"))
dir.create(file.path(root, "reports/v4"), recursive = TRUE, showWarnings = FALSE)

# -- Variables, named as in the 2023 code --------------------------------------
rsf$Use                  <- as.factor(rsf$use)
rsf$scale_Curvature      <- as.numeric(scale(rsf$curvature))
rsf$scale_RoadsProximity <- as.numeric(scale(rsf$dist_road_m))
rsf$scale_Elevation      <- as.numeric(scale(rsf$elevation))
rsf$scale_Ruggedness     <- as.numeric(scale(rsf$tri))
rsf$scale_Slope          <- as.numeric(scale(rsf$slope))
rsf$Direction            <- as.factor(rsf$direction)          # ref = "E" (alphabetical), as in 2023
veg <- as.character(rsf$evt_phys)
veg[is.na(veg) | veg == ""] <- "Other"
tab <- table(veg); veg[veg %in% names(tab[tab < 10])] <- "Other"  # collapse rare classes, as in 2023
rsf$Vegetation <- relevel(as.factor(veg), ref = "Other")

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

sel <- model.sel(m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)
write.csv(as.data.frame(sel), file.path(root, "reports/v4/model_selection.csv"))

top3_names <- rownames(as.data.frame(sel))[1:3]
top3 <- mget(top3_names)
avg <- model.avg(top3)
s <- summary(avg)
betas <- as.data.frame(s$coefmat.full)
ci <- confint(avg, level = 0.85, full = TRUE)
betas$ci85_low  <- ci[, 1]
betas$ci85_high <- ci[, 2]
write.csv(betas, file.path(root, "reports/v4/averaged_betas.csv"))

vifs <- do.call(rbind, lapply(top3_names, function(n)
  data.frame(model = n, term = names(vif(get(n))[, 1]), gvif = vif(get(n))[, 1])))
write.csv(vifs, file.path(root, "reports/v4/vif.csv"), row.names = FALSE)

cat("top 3 models:", paste(top3_names, collapse = ", "), "\n")
key <- c("scale_Ruggedness", "scale_Elevation", "scale_Slope")
print(round(betas[rownames(betas) %in% key, c("Estimate", "ci85_low", "ci85_high")], 3))
cat("MODEL_FIT_COMPLETE\n")
