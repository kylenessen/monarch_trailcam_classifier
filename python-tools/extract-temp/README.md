# Historical temperature extraction and review tools

These tools supported OCR extraction and manual review of camera-overlay temperatures. [METHODS.md](METHODS.md) describes the cleaning process. The CSV files and exploration scripts here record intermediate work. The reviewed manuscript input is maintained in the [manuscript data directory](https://github.com/kylenessen/monarch-wind-light-manuscript/tree/main/data), and release-ready observations are described by the [USGS release](https://doi.org/10.5066/P13IEKEB).

For the OCR utility, install uv, open this directory and run the following commands with Python 3.12 or newer.

```sh
uv sync --locked
uv run extract_temp.py sample_images -o example_temperatures.csv
```

The command writes `sample_images/example_temperatures.csv`. EasyOCR may download model weights on first use. The included images are a small software example, not a validation dataset. Inspect extracted values against the image overlays. Do not substitute unreviewed OCR results for the published reviewed temperatures.

Other scripts retain research-specific paths and interactive review assumptions. Read their configuration and [cleaning workflow](Workflow_for_Manual_Temperature_Data_Cleaning.md) before using them on a new dataset. Camera temperature readings were not independently calibrated against reference sensors.
