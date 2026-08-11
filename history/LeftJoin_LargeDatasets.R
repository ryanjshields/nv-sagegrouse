###Updating the DEMPointsVeg_#_corrected_cleaned files by adding EVT_PHYS columns

rsf_3 = read.csv("DEMPointsVeg_3_corrected_cleaned.csv", header = TRUE)
vegclass = read.csv("vegetation_reclass_dictionary.csv", header = TRUE)

#perform left join
rsf_3 = left_join(rsf_3, vegclass, by = "SAF_SRM")
head(rsf_3)

#check for NAs
rows_with_na_data <- which(apply(rsf_3, 1, function(row) any(is.na(row))))
