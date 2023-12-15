complete_model_analysis <- function(data, formulas, family) {
  models <- list()
  vif_results_df <- data.frame(model = character(), variable = character(), vif = numeric())

  # Fit each model
  for (i in seq_along(formulas)) {
    model_name <- paste("m", i, sep = "")
    models[[model_name]] <- glm(formulas[[i]], data = data, family = family)
  }

  # Perform model selection using the fitted models
  model_selection <- model.sel(models)

  # Check VIF for each of the top models
  top_model_names <- names(head(model_selection, 3))
  top_models <- lapply(top_model_names, function(name) models[[name]])

  for (model_name in top_model_names) {
    vif_values <- vif(top_models[[model_name]])
    vif_df <- data.frame(model = model_name, variable = names(vif_values), vif = vif_values)
    vif_results_df <- rbind(vif_results_df, vif_df)
  }

  # Plotting VIF results
  vif_plot <- ggplot(vif_results_df, aes(x = variable, y = vif, fill = model)) +
              geom_bar(stat = "identity", position = position_dodge()) +
              theme_minimal() +
              labs(title = "VIF Values", x = "Variable", y = "VIF")
  
  print(vif_plot)

  # If all VIF values are less than 10, perform model averaging
  if (all(vif_results_df$vif < 10)) {
    avgmodel <- model.avg(do.call("list", top_models))
    model_summary <- summary(avgmodel)

    # Return the averaged model as part of the results
    return(list("avgmodel" = avgmodel, "model_summary" = model_summary, "vif_results" = vif_results_df, "vif_plot" = vif_plot))
  } else {
    warning("One or more models have VIF values >= 10")
    return(NULL)
  }
}
