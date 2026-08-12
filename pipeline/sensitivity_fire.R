#!/usr/bin/env Rscript
# sensitivity_fire.R -- refit the top model excluding used leks whose
# vegetation class changed between LANDFIRE eras (post-2018 disturbance,
# e.g. the 2018 Martin Fire). If the herbaceous/vegetation effects hold,
# the temporal-mismatch critique is answered with evidence.
suppressPackageStartupMessages(library(MuMIn))
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
rsf <- read.csv(file.path(root, "data-local/design/model_input.csv"))
flags <- read.csv(file.path(root, "data-local/design/veg_changed_lekids.csv"))

prep <- function(d) {
  d$Use <- as.factor(d$use)
  d$scale_Curvature      <- as.numeric(scale(d$curvature))
  d$scale_PavedProximity   <- as.numeric(scale(d$dist_paved_m))
  d$scale_UnpavedProximity <- as.numeric(scale(d$dist_unpaved_m))
  d$scale_Elevation <- as.numeric(scale(d$elevation))
  d$scale_Ruggedness <- as.numeric(scale(d$tri))
  d$scale_Slope <- as.numeric(scale(d$slope))
  d$Direction <- as.factor(d$direction)
  veg <- as.character(d$evt_phys); veg[is.na(veg) | veg == ""] <- "Other"
  tab <- table(veg); veg[veg %in% names(tab[tab < 10])] <- "Other"
  ut <- table(veg[d$use == 1])
  veg[veg %in% setdiff(unique(veg), names(ut[ut >= 5]))] <- "Other"
  d$Vegetation <- relevel(as.factor(veg), ref = "Shrubland")
  d
}
form <- Use ~ scale_PavedProximity + scale_UnpavedProximity + scale_Curvature +
  scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation

full <- prep(rsf)
excl <- prep(rsf[!(rsf$use == 1 & rsf$lekid %in% flags$lekid), ])
m_full <- glm(form, data = full, family = "binomial")
m_excl <- glm(form, data = excl, family = "binomial")

keep <- c("VegetationGrassland", "VegetationExotic Herbaceous", "VegetationConifer",
          "scale_Ruggedness", "scale_Slope", "scale_Elevation")
cf <- function(m) { s <- summary(m)$coefficients; s[intersect(keep, rownames(s)), 1] }
out <- merge(data.frame(term = names(cf(m_full)), all_leks = round(cf(m_full), 3)),
             data.frame(term = names(cf(m_excl)), excl_changed = round(cf(m_excl), 3)))
write.csv(out, file.path(root, "reports/v4/sensitivity_fire.csv"), row.names = FALSE)
cat(sprintf("n used: full %d | excluding veg-changed %d\n",
            sum(full$use == 1), sum(excl$use == 1)))
print(out)
cat("SENSITIVITY_COMPLETE\n")
