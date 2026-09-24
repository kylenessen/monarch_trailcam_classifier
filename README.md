# Monarch Trailcam Classifier

A desktop application for manually classifying monarch butterflies in trail-camera photographs. Users label image-grid cells by butterfly abundance category and direct sunlight, then save the annotations locally. The application is also called Monarch Image Labeler.

Start with the [current installation and usage instructions](GETTING_STARTED.md). Download macOS builds and the example deployment from [Releases](https://github.com/kylenessen/monarch_trailcam_classifier/releases/latest), or run the application from source. The current release is 1.1.1. The builds are unsigned and are not notarized. The source workflow is tested on macOS. Windows and Linux packages have not been validated.

The [illustrated classification guide](https://kylenessen.github.io/monarch_trailcam_classifier/) is preserved unchanged as the protocol shared with the original research team. Its OneDrive and personalized installer instructions describe that team's workflow. Use the current instructions above to install the public application.

The [original classification data](data/classifications/) contain annotations for 12 deployments from the western monarch study at Vandenberg Space Force Base. Their README explains the categories, file structures and checksums. [Import instructions](GETTING_STARTED.md#import-study-annotations) cover both saved formats, including the older SC1 and SC2 files. The [example deployment](examples/README.md) provides one photograph and its original annotations for trying the interface.

The [manuscript repository](https://github.com/kylenessen/monarch-wind-light-manuscript) is the authoritative source for the paper's analysis inputs, scripts and model outputs. The [USGS data release](https://doi.org/10.5066/P13IEKEB) supplies photographs, deployment metadata, wind and temperature observations, and image-level classification summaries. Its assigned publication date is September 30, 2026. The DOI may not resolve before release activation. Native cell-level JSON files are hosted here rather than in the USGS package.

The application source is in [electron-app](electron-app/). Historical exploratory analyses and support utilities remain in [analysis](analysis/), [python-tools](python-tools/) and [qaqc](qaqc/). These are research development records, not the final manuscript workflow. [AI](AI/) contains historical development notes. The [OCR utility guide](python-tools/extract-temp/README.md) describes the temperature extraction materials.

Original software is available under the [ISC license](LICENSE). [Reuse notes](REUSE.md) distinguish software from study data, the historical protocol and third-party assets. Citation metadata is in [CITATION.cff](CITATION.cff). Please [open an issue](https://github.com/kylenessen/monarch_trailcam_classifier/issues) with your operating system, application version and steps to reproduce a problem. See [CONTRIBUTING.md](CONTRIBUTING.md) for checks to run before proposing changes.
