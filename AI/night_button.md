# Project Context and "Night" Button Feature Plan

This document provides context for the Monarch Trailcam Classifier project and outlines the implementation plan for the "Night" button feature.

## Project Overview

*   **Purpose:** An Electron-based desktop application designed for classifying monarch butterflies in trail camera photos.
*   **Goal:** To allow users to efficiently load folders of images, view them with an overlaid grid, classify monarch counts within each grid cell, mark cells with direct sunlight, add notes, and save these classifications to a JSON file (`classifications.json`) within the image folder.
*   **Structure:** The project is organized into several main directories:
    *   `electron-app/`: Contains the core Electron application source code, build configurations, and dependencies. See `AI/reorganization_plan.md` for more details.
    *   `python-tools/`: Utility scripts for processing or analyzing classification data.
    *   `analysis/`: R scripts and Quarto documents for data analysis.
    *   `docs/`: Project documentation website source.
*   **Key Task:** The current task is to add a "Night" button feature to the Electron app. See `AI/tasks.md` for other potential future tasks.

## Electron App Structure (`electron-app/src/`)

The renderer process code is modularized:

*   `renderer.js`: Main entry point for the renderer process, initializes modules.
*   `preload.js`: Exposes Node.js/Electron APIs securely to the renderer process (`window.electronAPI`).
*   `index.html`: The main HTML file for the UI.
*   `styles/styles.css`: CSS for styling the application.
*   `modules/`: Contains the core logic:
    *   `ui.js`: Handles DOM manipulation, button event listeners, and general UI updates. Orchestrates calls to other modules based on user interaction.
    *   `state.js`: Manages the application's global state (current image, classifications, selected tool, etc.).
    *   `classification.js`: Handles the logic for confirming, copying, and resetting image classifications (including grid cell data).
    *   `image-grid.js`: Manages loading images, creating the overlay grid, handling cell clicks/styling, and visual status updates.
    *   `file-system.js`: Interacts with the `preload.js` script to handle file system operations (selecting folders, reading/writing files, loading image lists/data).
    *   `notes.js`: Manages the notes dialog functionality.
    *   `shortcuts.js`: Defines and handles keyboard shortcuts.
    *   `zoom.js`: Handles image zoom functionality.
    *   `utils.js`: Contains helper functions (notifications, ID generation, etc.).

## "Night" Button Feature

*   **Requirement:** Add a "Night" button next to the "Confirm Image" button. See `AI/night_button_prompt.md` for the original request and addendum.
    *   **Macro Action:** Clicking the button should:
        1.  Execute the "Copy from Previous" action.
        2.  Execute the "Confirm Image" action, specifically marking this image as a "Night" image.
        3.  Navigate to the next image.
    *   **Data Flag:** Add an `isNight` boolean field to the `classifications.json` entry for each image. This should be `true` if confirmed via the "Night" button, `false` otherwise (including standard confirm, copy, reset, or initial state).
    *   **Reset Integration:** Clicking the "Reset Image" button should set `isNight` back to `false`.
    *   **Visual Indicator:** When an image is confirmed *and* marked as night, a visual indicator (e.g., a specific CSS class on the image wrapper like `status-night`) should be applied instead of the standard confirmation indicator (`status-confirmed`).

*   **Implementation Plan (Agreed Upon):**
    1.  **Add Button to HTML (`index.html`):** Insert `<button id="night-button">Night</button>`.
    2.  **Update Classification Logic (`classification.js`):** Modify `confirmImage`, `copyFromPrevious`, `resetImage` to handle the `isNight` flag correctly (accepting a parameter in `confirmImage`, setting explicitly to `false` in `copy`/`reset`).
    3.  **Implement Button Action (`ui.js`):** Create `nightButtonHandler` for the copy -> confirm(as night) -> next sequence. Modify `confirmImageHandler` to reload the image display after confirming/unconfirming to update the visual status.
    4.  **Update Initialization (`file-system.js`):** Add `isNight: false` to the default object in `initializeClassificationsIfNeeded`.
    5.  **Add Visual Indicator:**
        *   Modify `createImageWrapper` in `image-grid.js` to add `status-night` class if confirmed and `isNight`, and `status-confirmed` class if confirmed but not `isNight`.
        *   Add CSS rules in `styles.css` for `.status-night` and `.status-confirmed`.
    6.  **(Optional) Add Keyboard Shortcut:** Modify `shortcuts.js` and `ui.js`.

*   **Files to Modify:**
    *   `electron-app/src/renderer/index.html`
    *   `electron-app/src/renderer/modules/classification.js`
    *   `electron-app/src/renderer/modules/ui.js`
    *   `electron-app/src/renderer/modules/file-system.js`
    *   `electron-app/src/renderer/modules/image-grid.js`
    *   `electron-app/src/styles/styles.css`
    *   `electron-app/src/renderer/modules/shortcuts.js` (If shortcut is added)

*   **Current Status:** The plan is finalized. The next step is for the user to switch to ACT mode to begin implementation.


## Original prompt
I would like your help developing a new feature for my electron app. It should be a button on the bottom bar next to confirm image that is called "night". This button is essentially a macro which will execute the function copy from previous and then confirm the image and then skip to the next image. Essentially, it's automating a few keystrokes that the user has to do right now when they encounter a night photo. The expected behavior is that they're not actually labeling the photo. They're just carrying the previous information from the last good photo and quickly moving through all night images. There's another important aspect that this button should do as well, which is create a new entry in the configurations that JSON file. This entry should be called "Night" and if you click the "NIght" button it should return true and it should be false for all other cases. This will allow me to quickly filter out these records when I do my analysis. I can anticipate overshooting the night button by clicking too fast and accidentally labeling daytime photos as night. Clicking the reset image button should fix this issue by resetting the night JSON entry to false. I would like you to thoroughly review the existing code to see how all of this logic can be fit in. Do you have any questions for me?

Addendums
There should be a visual confirmation that an image is labeled as "Night". For example, in the top right corner, instead of saying "Confirmed", it can be a lighter blue and say "Night".