# README.md for nv-sagegrouse Repository

## Project Overview
This repository hosts the analysis for the Greater Sage-grouse in Nevada. The project employs a Resource Selection Function (RSF) analysis, leveraging FOSS4G technologies and advanced statistical methods in R for efficient, scalable, and replicable data processing and analysis. It aims to predict fine-scale lek site selection by analyzing various environmental and anthropogenic factors.

## Contents
- `function_inputs/`: Input data and parameters for various functions.
- `functions/`: Modular R scripts for specific analysis tasks, including data preprocessing, model fitting, and validation.
- `results/`: Output data and results from the analysis.
- `main.r`: Main R script that orchestrates the analysis workflow.
- `Utilities/`: Additional scripts and tools for data management and analysis.

## Setup and Requirements
- Requirements: R (with packages like `car`, `MuMIn`, `data.table`), PostgreSQL/PostGIS for spatial data management.
- `environment.yml`: Contains information for setting up the analysis environment.
- Database setup instructions are provided separately, focusing on efficient raster data management in PostGIS.

## Data Processing
- Detailed processing of raster data using PostGIS for spatial calculations like slope, aspect, and ruggedness.
- Efficient extraction of raster values and spatial feature generation in R.

## Analysis
- Comprehensive RSF analysis using a modular approach in R.
- Functions include model fitting with `glm`, model selection, and variance inflation factor (VIF) analysis.
- Emphasis on efficient data handling, modular coding, and parallel processing for large datasets.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgements
This work is part of a collaborative effort involving multiple stakeholders and contributors dedicated to the conservation and study of the Greater Sage-grouse in Nevada.
