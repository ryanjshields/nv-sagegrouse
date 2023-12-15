# Function for Multicollinearity Tests
multicollinearity_tests <- function(data, columns) {
  # Ensure the 'ggplot2' package is available for plotting
  if (!require(ggplot2, quietly = TRUE)) {
    install.packages("ggplot2")
    library(ggplot2)
  }

  # Compute correlation matrix
  corr_matrix <- cor(data[columns])

  # Print the correlation matrix
  print(corr_matrix)

  # Plotting
  pairs(data[columns], main = "Multicollinearity Plot", pch = 21, bg = c("red", "green", "blue")[unclass(data$Use)])

  # Alternatively, use ggplot2 for a more advanced plotting (Optional)
  # long_data <- reshape2::melt(data[columns])
  # ggplot(long_data, aes(x = value, fill = variable)) + 
  #   geom_histogram(bins = 30, position = "identity", alpha = 0.6) +
  #   theme_minimal() +
  #   labs(title = "Multicollinearity Plot", x = "Value", y = "Frequency")

  return(corr_matrix)
}

# Using the function
# For columns 6 to 11
cor_matrix_1 <- perform_multicollinearity_tests(rsf, 6:11)

# For columns 15 to 19
cor_matrix_2 <- perform_multicollinearity_tests(rsf, 15:19)
