model_selection <- function(data, output_dir = getwd()) {
  # Load necessary libraries
  library(MuMIn)

  #A Priori Models
  m1 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")
  m2 = glm(Use~scale_RoadsProximity + scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")
  m3 = glm(Use~scale_RoadsProximity + scale_Ruggedness + scale_Slope + Vegetation, data = data, family = "binomial")
  m4 = glm(Use~scale_RoadsProximity + scale_Ruggedness + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")
  m5 = glm(Use~scale_Curvature + scale_Slope + scale_Elevation + Vegetation, data = data, family = "binomial")
  m6 = glm(Use~scale_RoadsProximity + scale_Slope + Vegetation, data = data, family = "binomial")
  m7 = glm(Use~scale_Ruggedness + scale_Slope + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")
  m8 = glm(Use~scale_RoadsProximity + scale_Slope + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")
  m9 = glm(Use~scale_RoadsProximity + scale_Curvature + scale_Slope + Vegetation, data = data, family = "binomial")
  m10 = glm(Use~scale_Slope + scale_Elevation + Vegetation, data = data, family = "binomial")
  m11 = glm(Use~scale_Ruggedness + scale_Slope + Vegetation, data = data, family = "binomial")
  m12 = glm(Use~scale_RoadsProximity + Direction + scale_Elevation + Vegetation, data = data, family = "binomial")

  model_selection_results <- model.sel(m1, m2, m3, m4, m5, m6, m7, m8, m9, m10, m11, m12)

  # save the model selection results to a file
  write.csv(model_selection_results, file.path(output_dir, "model_selection_results.csv"))

  # Grab the name of the top 3 models from the model selection results
  top_models <- names(head(model_selection_results, 3))

  # Return the top models (you can also return the entire selection results if needed)
  return(list("top_models" = top_models))
}