# Load the necessary function definitions
source("functions/read_and_summarize.R")
source("functions/bin_aspect.R")
source("functions/convert_to_factors.R")
source("functions/read_column_names.R")
source("functions/rescale_variables.R")
source("functions/multicollinearity_tests.R")
source("functions/model_selection.R")

# Read and summarize the datasets
model_data <- read_and_summarize("D:\\CarverMikiah_rsf_nevada_sagegrouse\\Data\\RSF_Ready_ActiveOnly_Land.csv")
prediction_surface <- read_and_summarize("D:\\CarverMikiah_rsf_nevada_sagegrouse\\Data\\rediction_surface_sample.csv")

# Bin aspect values
model_data <- bin_aspect_values(rsf)
prediction_surface <- bin_aspect_values(prediction_surface)

# Convert specified columns to factors
factor_columns <- read_column_names("function_inputs\\factors_columns.txt")
model_data <- convert_to_factors(rsf, factor_columns)
prediction_surface <- convert_to_factors(prediction_surface, factor_columns)

# Rescale variables based on column names from a text file
scale_columns <- read_column_names("function_inputs\\columns_to_scale.txt")
model_data <- rescale_variables(rsf, scale_columns)
prediction_surface <- rescale_variables(prediction_surface, scale_columns)

# Run model selection and averaging
model_avg_results <- model_selection(model_data)

# Collapse the vegetation classes for the sample point grid
prediction_surface <- collapse_veg_classes(prediction_surface)

# Use model avg results to generate prediction values for the sample point grid
generate_predictions(prediction_surface, model_avg_results, "prediction_surface.csv")
