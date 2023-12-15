read_and_summarize <- function(file_path) {
  rsf <- read.csv(file_path, header = TRUE)
  print(str(rsf))
  print(summary(rsf))
  return(rsf)
}