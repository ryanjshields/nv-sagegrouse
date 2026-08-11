# Data Manifest

No data lives in git. Sources:

- **Leks (SENSITIVE)**: gs://ssm-nv-sagegrouse-secure/leks/ — request from NDOW to replicate
- **Archive**: gs://ssm-nv-sagegrouse-open/ (raw 2021 extractions, veg tables, dictionaries)
- **DEM**: 3DEP 1 arc-second via pipeline/fetch_tnm.py → data/manifest-3dep-v4.json
- **Range**: USFWS 2015 Status Review Current Range (ScienceBase 56f96693e4b0a6037df06034)
- **Roads**: TIGER 2024 NV primary/secondary (tl_2024_32_prisecroads)
- **Vegetation**: LANDFIRE latest EVT (fetch script TBD)

Published runs snapshot their exact inputs to gs://ssm-nv-sagegrouse-open/snapshots/<version>/.
