# Function to add predictions and write to CSV
generate_predictions <- function(data, model, filename) {
  # Add predictions column to the data frame
  data$predictions <- predict(model, newdata = data, type = "response")

  # Create a new dataframe with just the coordinates and predictions
  data_predict <- select(data, POINT_X, POINT_Y, predictions)

  # Write the new dataframe to a CSV file
  write.csv(data_predict, file = filename)
}
