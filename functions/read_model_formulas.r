# Function to read formulas from a file
read_model_formulas <- function(file_path) {
  formulas <- read.csv(file_path, header = FALSE, stringsAsFactors = FALSE)
  lapply(formulas$V1, as.formula)
}