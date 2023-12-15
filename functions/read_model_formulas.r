read_model_formulas <- function(file_path) {
  formula_strings <- readLines(file_path)
  formula_strings <- formula_strings[formula_strings != ""]
  formulas <- lapply(formula_strings, as.formula)
  return(formulas)
}