model_selection <- function(data, output_dir = getwd()) {
  # Load necessary libraries
  library(MuMIn)
  library(car)

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

  # Check for multicollinearity in the top 3 models using vif() on each model object and save the results to a file
  vif(m7)
  vif(m2)
  vif(m1)

  # save the vif results to a file
  write.csv(vif(m7), file.path(output_dir, "results\\m7_vif_results.csv"))
  write.csv(vif(m2), file.path(output_dir, "results\\m2_vif_results.csv"))
  write.csv(vif(m1), file.path(output_dir, "results\\m1_vif_results.csv"))

  # Run model averaging on the top 3 models
  avgmodel <- model.avg(m7, m2, m1)

  # save the model averaging results to a file
  model_averaging_results <- summary(avgmodel)

  # return the model averaging results
  return(model_averaging_results)
  
}