rsf <- read_and_summarize("RSF_Ready_ActiveOnly_Land.csv")
rsf <- bin_aspect_values(rsf)
rsf <- convert_to_factors(rsf)
column_names <- read_column_names("columns_to_scale.txt")
rsf <- rescale_variables(rsf, column_names)

str(rsf)
summary(rsf)

# check for multicollinearity
# For columns 6 to 11
cor_matrix_1 <- perform_multicollinearity_tests(rsf, 6:11)

# For columns 15 to 19
cor_matrix_2 <- perform_multicollinearity_tests(rsf, 15:19)

#run model selection and averaging
formulas <- read_model_formulas("model_formulas.txt")
analysis_results <- complete_model_analysis(rsf, formulas, family = "binomial")
