# Load the necessary function definitions
source("functions/read_and_summarize.R")
source("functions/bin_aspect.R")
source("functions/convert_to_factors.R")
source("functions/read_column_names.R")
source("functions/rescale_variables.R")
source("functions/multicollinearity_tests.R")
source("functions/model_selection.R")

# Read and summarize the data
rsf <- read_and_summarize("C:\\Users\\spati\\Downloads\\RSF_Ready_ActiveOnly_Land.csv")

# Bin aspect values
rsf <- bin_aspect_values(rsf)

# Convert specified columns to factors
factor_columns <- read_column_names("function_inputs\\factors_columns.txt")
rsf <- convert_to_factors(rsf, factor_columns)

# Rescale variables based on column names from a text file
column_names <- read_column_names("function_inputs\\columns_to_scale.txt")
rsf <- rescale_variables(rsf, column_names)

# Print the structure and summary of the dataframe
str(rsf)
summary(rsf)

# Check for multicollinearity
#cor_matrix_1 <- multicollinearity_tests(rsf, 6:11)
#cor_matrix_2 <- multicollinearity_tests(rsf, 15:19)

# Run model selection and averaging
analysis_results <- model_selection(rsf)

# Check if the model analysis was successful and proceed accordingly
#if (!is.null(analysis_results)) {
  # Further analysis or predictions can go here, using `analysis_results$avgmodel`
#}
