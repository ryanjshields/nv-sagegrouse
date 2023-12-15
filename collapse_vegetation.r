collapse_vegetation <- function(data, column_name, threshold = 10, output_csv_path = "collapsed_levels.csv") {
  # Count the frequency of each level
  freq <- table(data[[column_name]])

  # Find levels with frequency less than the threshold
  levels_to_collapse <- names(freq[freq < threshold])

  # Write the levels to collapse to a CSV file
  collapsed_levels_df <- data.frame(Level = levels_to_collapse, Frequency = freq[freq < threshold])
  write.csv(collapsed_levels_df, output_csv_path, row.names = FALSE)

  # Collapse these levels into 'Other'
  data[[column_name]] <- as.factor(data[[column_name]])
  levels(data[[column_name]])[data[[column_name]] %in% levels_to_collapse] <- "Other"

  # Relevel to make 'Other' the reference level, if necessary
  if("Other" %in% levels(data[[column_name]])) {
    data[[column_name]] <- relevel(data[[column_name]], ref = "Other")
  }

  return(data)
}