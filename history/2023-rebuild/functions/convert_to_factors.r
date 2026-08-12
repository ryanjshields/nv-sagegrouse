convert_to_factors <- function(data, columns) {
  for (col in columns) {
    data[[col]] <- as.factor(data[[col]])
  }
  return(data)
}