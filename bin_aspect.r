bin_aspect_values <- function(data) {
  aspect_breaks <- c(-Inf, 22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5, Inf)
  aspect_labels <- c("N", "NE", "E", "SE", "S", "SW", "W", "NW", "N")
  data$Direction <- cut(data$Aspect, breaks = aspect_breaks, labels = aspect_labels, right = FALSE)
  return(data)
}
