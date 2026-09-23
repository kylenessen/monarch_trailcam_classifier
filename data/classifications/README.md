# Original monarch image classifications

These 12 deployment JSON files preserve the original cell classifications from the 2023 to 2024 monarch monitoring season at Vandenberg Space Force Base. They include cell positions, ordinal butterfly categories, sunlight labels and saved annotation fields in the native Monarch Trailcam Classifier format.

The files were copied without modification on September 22, 2026 from [the manuscript source data](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/9603041e214d22ad4f0bc02c86814ad1476f9423/data/deployments). SHA256SUMS records their SHA-256 checksums. The manuscript repository retains matching copies for its analysis scripts.

The [USGS data release](https://doi.org/10.5066/P13IEKEB) contains photographs, deployment metadata, wind and temperature observations, and image-level classification summaries. Its classifications.csv contains BI, sun-exposed BI and category counts. These native cell-level JSON files are hosted here alongside the software and are not attachments to that release.

Each JSON filename identifies a deployment. Image keys correspond to image_filename in the release photo_index.csv. Use deployment_id and image_filename together to join release records.

Files contain an object keyed by image filename, either at the top level or within
a classifications object. Each image record contains cells keyed by cell_row_column.
Each cell stores count, an ordinal category, and directSun, a sunlight flag. Some
older records use sunlight for the same flag. Categories are 0, 1-9, 10-99 and
100-999. Image records also contain confirmed and index, and may contain user,
isNight and notes. These retain confirmation state, image sequence, saved user,
night flag and annotation notes.

The JSON includes unclassified placeholders. classifications.csv summarizes
saved daytime classifications, including unconfirmed annotations and excluding
untouched placeholders. Night records are identified using saved night flags and
recorded SC1 and SC2 night intervals when a JSON flag is absent. Butterfly Index sums category lower bounds of 0, 1, 10 and 100.
Sun-exposed Butterfly Index sums those values for occupied cells marked in sunlight.


The [illustrated protocol](https://kylenessen.github.io/monarch_trailcam_classifier/) describes the labeling procedure. The [application source](../../electron-app/) implements the classifier. The [manuscript repository](https://github.com/kylenessen/monarch-wind-light-manuscript) contains the analysis inputs, scripts and model outputs.
