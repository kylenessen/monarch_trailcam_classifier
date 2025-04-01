# Prompt

I would like your help to develop a new feature for my @/electron-app/ . Right now there is a default and unchangeable number of cell grids that the app utilizes. I would like the option to have to change the resolution that I can select at the beginning of a new deployment. I imagine this feature only becomes relevant when loading a folder without a configurations.json file. the app should prompt the user what resolution they want, and then it will generate the appropriate number of cells within that configuration.json file.The user should not be able to change the resolution once that file has been generated. It's important that it stays consistent. And the only way to regenerate it is to delete the configurations file. I think the simplest way to do this is simply ask the user the number of columns and rows they want for that deployment. Provide a default value, which is whatever I'm using currently. This feature will require you to carefully examine the existing code and perhaps rewrite some of the existing logic. I would like to enforce a square ratio for the cells. So it'll be important to calculate the aspect ratio of the image and have some mechanisms to ensure that an appropriate ratio of columns to rows is enforced. Maintain the same naming convention for the grid cells within the configuration.json file. Do you have any questions for me?

---

# Implementation Plan (Dynamic Grid Resolution) - Final

This plan outlines the steps taken to allow users to define the grid resolution (rows and columns) for a new deployment, using a fixed 16:9 aspect ratio for calculations. It assumes that existing `configurations.json` files will be manually updated or handled separately to conform to the new structure if needed.

**New `configurations.json` Structure:**

When a configuration is generated for a new deployment, the file will have the following structure:

```json
{
  "rows": <user_input_rows>,
  "columns": <calculated_columns>,
  "classifications": {
     // Image filename keys and their cell data will be added here
     // e.g., "image1.JPG": { "confirmed": false, "cells": {...}, ... },
     //       "image2.JPG": { "confirmed": false, "cells": {...}, ... }
  }
}
```

**Implementation Steps:**

1.  **Modify State Management (`electron-app/src/renderer/modules/state.js`):**
    *   Removed the exported `GRID_CONFIG` constant (`{ columns: 16, rows: 9 }`).
    *   Introduced a new state variable, `currentGridConfig`, initialized to `{ rows: null, columns: null }`.
    *   Updated the `createDefaultGridCells` function to use `currentState.currentGridConfig.rows` and `currentState.currentGridConfig.columns` when generating the default cell structure for a *new* image classification entry.
    *   Added getter (`getGridConfig`) and setter (`setGridConfig`) functions for `currentGridConfig`.

2.  **Modify File Loading Logic (`electron-app/src/renderer/modules/file-system.js`):**
    *   Renamed `loadClassifications` to `loadOrInitializeConfiguration`.
    *   Updated `getConfigurationFilePath` to use the `deploymentFolder`.
    *   When a deployment folder is selected, construct the path to `configurations.json`.
    *   Use an IPC call (`window.electronAPI.checkFileExists`) to check if `configurations.json` exists.
    *   **If it exists:**
        *   Load and parse the JSON content (`parsedData`).
        *   Validate that `parsedData.rows`, `parsedData.columns`, and `parsedData.classifications` exist. Show error if not.
        *   Update the `currentGridConfig` state using `parsedData.rows` and `parsedData.columns`.
        *   Load the object from `parsedData.classifications` into the main `classifications` state.
    *   **If it does *not* exist:**
        *   Trigger the display of the UI prompt (Step 3). **Do not load any images for display yet.** (Removed logic for getting first image dimensions).

3.  **Create UI Prompt (`electron-app/src/renderer/modules/ui.js` and `index.html`):**
    *   Added a `<dialog>` element (`#grid-resolution-dialog`) to `index.html` for the prompt.
    *   Implemented the `promptForGridResolution` function in `ui.js`.
    *   This function shows the modal dialog which:
        *   Prompts the user: "Enter the desired number of grid rows for this deployment:".
        *   Displays the default value (9 rows).
        *   Includes a number input field (`#grid-rows-input`).
        *   Has "Confirm" and "Cancel" buttons.
    *   The "Confirm" button's event handler:
        *   Reads and validates the user's input for rows (`userRows`).
        *   Calculates the number of columns using a **fixed 16:9 aspect ratio**: `calculatedColumns = Math.max(1, Math.round(userRows * (16 / 9)))`.
        *   Updates the `currentGridConfig` state.
        *   Creates the initial `configurations.json` content string: `JSON.stringify({ rows: userRows, columns: calculatedColumns, classifications: {} }, null, 2)`.
        *   Uses an IPC call (`window.electronAPI.writeFile`) to save the new `configurations.json`.
        *   Initializes the main `classifications` state to `{}`.
        *   Closes the modal and resolves a promise indicating success/failure.

4.  **Modify Grid Creation (`electron-app/src/renderer/modules/image-grid.js`):**
    *   In the `createGrid` function:
        *   Retrieve the current grid dimensions using `getGridConfig()` from the state.
        *   Use these dynamic `rows` and `columns` variables in the loops and style calculations.
        *   Added validation to ensure grid config is set before attempting creation.

5.  **Modify Initialization (`electron-app/src/renderer/modules/ui.js`):**
    *   Refactored the `handleFolderSelection` function to manage the correct asynchronous flow:
        1.  Select Folder.
        2.  Call `loadOrInitializeConfiguration` (which handles checking the file and potentially showing the prompt).
        3.  If configuration is successful, load the image list (`loadImageList`).
        4.  If images exist, load the first unclassified image (`findNextUnclassifiedHandler`).
        5.  Handle errors and state resets appropriately if configuration or image loading fails.

**Note:** The implementation assumes that any existing `configurations.json` files created before this change will be manually updated to include the top-level `rows`, `columns`, and `classifications` keys. The application no longer contains backward compatibility logic for the old file format.
