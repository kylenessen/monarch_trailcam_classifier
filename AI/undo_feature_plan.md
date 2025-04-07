# Undo Feature Implementation Plan

## Goal

Implement an "Undo" feature in the Monarch Trailcam Classifier Electron app to allow users to revert recent classification changes made to the currently viewed image, *before* it is confirmed.

## Feature Description

*   **Scope:** The undo functionality will operate only on the classification data (cell labels and direct sun status) of the **currently active image**.
*   **Ephemeral History:** The undo history will be stored **in-memory only** and will not be saved to the `classifications.json` file or persist after the application closes.
*   **Trigger:** Undo will revert the last action that modified the cell classifications of the current image, such as applying a label, using "Copy from Previous", or resetting the image.
*   **Confirmation Reset:** The undo history for an image will be **cleared** when the image is confirmed or when the user navigates to a different image.
*   **UI:** An "Undo" button will be added to the UI, enabled only when there is a valid action to undo for the current, unconfirmed image.

## Implementation Strategy: In-Memory History

1.  **History Store:** A dedicated JavaScript module (e.g., `history.js`) or additions to `state.js` will manage the undo history. It will use an object where keys are image filenames and values are arrays of past `cells` object states (snapshots).
    ```javascript
    // Example structure in history.js
    let historyStore = {}; // { "image1.jpg": [cellsStateSnapshot1, cellsStateSnapshot2], ... }
    const MAX_HISTORY_SIZE = 15; // Limit memory usage
    ```
2.  **Snapshotting:** Before any function modifies the `cells` data of the current, *unconfirmed* image (`copyFromPrevious`, `resetImage`, cell click/drag handlers), a deep copy of the *current* `cells` object will be pushed onto the history stack for that image using `JSON.parse(JSON.stringify(...))`. The history stack size will be capped.
3.  **Undo Action:**
    *   The "Undo" button click handler will call an `undoLastChange()` function.
    *   This function retrieves the current image name.
    *   It checks if the image is confirmed; if so, it does nothing.
    *   It pops the most recent state snapshot from the `historyStore` for the current image.
    *   If a snapshot exists, it updates the main application state (`currentState.classifications[currentImage].cells`) with the popped snapshot.
    *   It triggers a UI refresh to display the restored labels.
    *   It updates the enabled/disabled state of the Undo button.
4.  **History Clearing:** The history array for a specific image (`historyStore[imageName]`) will be cleared (set to `[]`) whenever:
    *   The `confirmImage` function is successfully executed for that image.
    *   The user navigates away from that image (e.g., in `loadImage`, `nextImage`, `prevImage` handlers, *before* loading the new image).
5.  **UI Integration:**
    *   An "Undo" button (`#undo-button`) will be added to `index.html`.
    *   Event listeners in `ui.js` or `renderer.js` will connect the button to the `undoLastChange` function.
    *   A function (`updateUndoButtonState`) will enable/disable the button based on whether the current image is unconfirmed and has history available (`history.hasHistory(currentImage)`). This function will be called after any history push, pop, clear, or image navigation/confirmation change.

## Code Structure Changes

*   **New Module:** `electron-app/src/renderer/modules/history.js` (Recommended) containing `pushState`, `popState`, `clearHistory`, `hasHistory`.
*   **Modifications:**
    *   `electron-app/src/renderer/modules/classification.js`: Add calls to `history.pushState` before modifying cells in `copyFromPrevious`, `resetImage`. Add call to `history.clearHistory` in `confirmImage`. Implement `undoLastChange` function (or call it from `history.js`).
    *   `electron-app/src/renderer/modules/ui.js` (or `renderer.js`): Add calls to `history.pushState` in cell interaction handlers. Add calls to `history.clearHistory` in image navigation functions. Add event listener for the Undo button. Implement and call `updateUndoButtonState`.
    *   `electron-app/src/renderer/index.html`: Add the `<button id="undo-button">`.
    *   Relevant modules will need to import functions from `history.js` and potentially state accessors (`getCurrentImageFile`, `getImageClassification`) from `state.js`.

## Exclusions

*   No changes to the `classifications.json` file format or saving mechanism.
*   Redo functionality is not included in this initial plan but could be added later by managing a separate redo history stack.
