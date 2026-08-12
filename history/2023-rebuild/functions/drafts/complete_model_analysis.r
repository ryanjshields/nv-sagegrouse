# Define the complete_model_analysis function
complete_model_analysis <- function(data, formulas, family, output_dir = getwd()) {
  # Load necessary libraries
  library(car)  # Required for VIF calculations
  library(MuMIn)  # Used for model selection functions

  # Fit models and store them in a list with proper names
  models <- setNames(lapply(seq_along(formulas), function(i) {
    glm(formulas[[i]], data = data, family = family)
  }), paste("m", seq_along(formulas), sep = ""))

  # Perform model selection using the fitted models and store the results
  model_selection <- model.sel(do.call("list", models))

  # Convert model selection results to a data frame
  model_selection_df <- as.data.frame(model_selection)

  # Add model names to the data frame
  model_names <- names(models)
  model_selection_df$model_name <- model_names[match(rownames(model_selection_df), model_names)]

  # Reorder columns to make model_name the first column
  model_selection_df <- model_selection_df[c("model_name", setdiff(names(model_selection_df), "model_name"))]

  # Save model selection results with model names
  model_selection_output_file <- file.path(output_dir, "model_selection_output.csv")
  write.csv(model_selection_df, model_selection_output_file, row.names = FALSE)

  # Extract the top 3 models based on AICc ranking
  top_model_names <- head(rownames(model_selection_df), 3)
  top_models <- models[top_model_names]

  # Initialize data frame for VIF results
  vif_results_df <- data.frame(model = character(), variable = character(), vif = numeric(), stringsAsFactors = FALSE)

  # Calculate VIF for each of the top 3 models
  for (model_name in top_model_names) {
    model <- models[[model_name]]
    if (!is.null(model)) {
      vif_values <- vif(model)
      # Check if vif_values are not empty and synchronize with their names
      if (!is.null(vif_values) && length(vif_values) == length(names(vif_values))) {
        vif_df <- data.frame(model = model_name, variable = names(vif_values), vif = vif_values, stringsAsFactors = FALSE)
        vif_results_df <- rbind(vif_results_df, vif_df)
      }
    }
  }

  # Save VIF results to a file
  vif_output_file <- file.path(output_dir, "vif_results.csv")
  write.csv(vif_results_df, vif_output_file, row.names = FALSE)

  # Return models, VIF results, and file paths
  return(list("models" = models, "vif_results" = vif_results_df, "vif_output_file" = vif_output_file))
}
