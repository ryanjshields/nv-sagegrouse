# Function to read column names from a text file
read_column_names <- function(file_path) {
  column_names <- readLines(file_path)
  # Filter out any empty lines or spaces
  column_names <- column_names[column_names != ""]
  return(column_names)
}