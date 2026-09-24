# Using Monarch Trailcam Classifier

This guide describes the public application. The [original illustrated protocol](https://kylenessen.github.io/monarch_trailcam_classifier/) remains unchanged so readers can review the instructions shared with the study team.

## Install on macOS

Download version 1.1.1 from [Releases](https://github.com/kylenessen/monarch_trailcam_classifier/releases/latest). Choose `arm64` for Apple silicon or `x64` for Intel. Open the DMG and drag Monarch Image Labeler to Applications. These research builds are unsigned and not notarized. macOS may require approval in System Settings, Privacy & Security after the first launch attempt. No OneDrive account is required. Windows and Linux installers have not been validated.

Download the example deployment ZIP from the same release and extract it to a working folder. Open the application, click the folder selector and choose the extracted `UDMH2` folder. The photograph and `configurations.json` must be directly inside that folder. The photograph has an 18-by-32 grid and saved annotations. Enter your initials before using Confirm or Unlock. Work on a copy if you want to experiment with edits.

## Run from source

Install Node.js 22.12 or newer and npm, then run the following commands.

```sh
git clone https://github.com/kylenessen/monarch_trailcam_classifier.git
cd monarch_trailcam_classifier/electron-app
npm ci
npm start
```

The application opens a desktop window. Select a folder containing local JPG, JPEG or PNG images. A new deployment prompts for its grid resolution. Keep the chosen grid fixed for that deployment. Existing deployments load their grid and labels from `configurations.json`. Use a working copy of the [example](examples/README.md) to explore the controls.

## Import study annotations

Install [uv](https://docs.astral.sh/uv/) to run the standalone import tool. It uses only the Python standard library. Run these commands from the repository root after placing a deployment's photographs in a separate working folder. Filenames must match the keys in that deployment's published JSON file.

For ten deployments, grid dimensions are already stored in the archive. For example, with an existing `working/SC4` folder containing the SC4 photographs, run the following command.

```sh
uv run --no-project python tools/prepare_deployment.py data/classifications/SC4.json working/SC4/configurations.json
```

SC1 and SC2 use the earlier format without grid metadata. Every populated record in these two published files has a complete 9-by-16 grid. Specify those dimensions explicitly.

```sh
uv run --no-project python tools/prepare_deployment.py data/classifications/SC1.json working/SC1/configurations.json --rows 9 --columns 16
uv run --no-project python tools/prepare_deployment.py data/classifications/SC2.json working/SC2/configurations.json --rows 9 --columns 16
```

The tool writes a new file and refuses to overwrite an existing one. It preserves original annotation fields and supplies `directSun` from the older `sunlight` flag where needed for display. The archived JSON files remain unchanged. Open the working folder in the application after conversion. Photographs are obtained separately from the USGS release. Before that release is available, the bundled example is sufficient to try the application.

## Save and back up work

The current application saves to `configurations.json` beside the images. Back up that file and the corresponding photographs together. The historical guide also mentions `classifications.json`, the filename used by an earlier application version. Published deployment JSON files retain their archival names and are prepared for the current application using the tool above.

Only one person or application instance should edit a deployment at a time. An image's confirmed state locks its labels until it is unlocked. Classification changes are saved automatically. Keep archival study files separate from files you edit.

## Build and test

From `electron-app`, run the tests and build a macOS installer with the following commands.

```sh
npm ci
npm run test:e2e -- --workers=1
npm run build -- --mac --arm64 --x64 --publish never
```

Node.js 22 is used for the automated macOS checks. Building a signed or notarized distribution additionally requires your own Apple signing configuration. Prebuilt releases do not require Node.js or Python for ordinary use. Python is needed only for the optional annotation preparation tool.
