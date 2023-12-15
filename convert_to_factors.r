convert_to_factors <- function(data) {
  data$Use <- as.factor(data$Use)
  data$Vegetation <- as.factor(data$Vegetation)
  data$Direction <- as.factor(data$Direction)
  return(data)
}