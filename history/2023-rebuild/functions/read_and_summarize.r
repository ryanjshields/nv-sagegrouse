read_and_summarize <- function(file_path, output_dir = getwd()) {
  rsf <- read.csv(file_path, header = TRUE)
  
  # Create file names based on the input file name
  base_name <- tools::file_path_sans_ext(basename(file_path))
  str_output_file <- file.path(output_dir, paste0(base_name, "_structure.txt"))
  summary_output_file <- file.path(output_dir, paste0(base_name, "_summary.txt"))
  
  # Capture the output of str() and write it to a file
  capture.output(str(rsf), file = str_output_file)
  
  # Capture the output of summary() and write it to a file
  capture.output(summary(rsf), file = summary_output_file)
  
  return(rsf)
}