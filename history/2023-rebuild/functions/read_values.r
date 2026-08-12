read_column_values <- function(file_path) {
  column_values <- readLines(file_path)
  column_values <- column_values[column_values != ""]
  return(column_values)
}
