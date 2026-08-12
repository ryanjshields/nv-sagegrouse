multicollinearity_tests <- function(data, columns) {
  # Ensure the 'ggplot2' package is available for plotting
  if (!require(ggplot2, quietly = TRUE)) {
    install.packages("ggplot2")
    library(ggplot2)
  }

  # Check if all specified columns are numeric
  if (!all(sapply(data[columns], is.numeric))) {
    stop("All specified columns must be numeric for multicollinearity tests.")
  }

  # Compute correlation matrix
  corr_matrix <- cor(data[columns])

  # Print the correlation matrix
  print(corr_matrix)

  # Plotting pairwise relationships
  pairs(data[columns], main = "Multicollinearity Plot", pch = 21, bg = c("red", "green", "blue")[unclass(data$Use)])

  # Alternatively, use ggplot2 for a more advanced plotting (Optional)
  # Ensure reshape2 package is available
  if (!require(reshape2, quietly = TRUE)) {
    install.packages("reshape2")
    library(reshape2)
  }

  # Convert data to long format for ggplot
  long_data <- reshape2::melt(data[columns])
  ggplot(long_data, aes(x = value, fill = variable)) + 
    geom_histogram(bins = 30, position = "identity", alpha = 0.6) +
    theme_minimal() +
    labs(title = "Multicollinearity Plot", x = "Value", y = "Frequency")

  return(corr_matrix)
}