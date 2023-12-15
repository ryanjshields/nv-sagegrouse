# Function to rescale specified variables
rescale_variables <- function(data, columns) {
  for (col in columns) {
    scaled_col_name <- paste("scale", col, sep = "_")
    data[[scaled_col_name]] <- scale(data[[col]])
  }
  return(data)
}
