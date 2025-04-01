# Monarch Image Labeler - E2E Test Plan

This document outlines the manual checks and expected behaviors for End-to-End testing of the Monarch Image Labeler application.

---

## Feature: Application Launch & Basic UI

### Test Case: Initial State

*   **Title:** Verify initial UI elements on launch
*   Status: [ ] Not Implemented
*   **Preconditions:** None
*   **Steps:**
    1.  Launch the application.
*   **Expected Results:**
    *   The main application window appears.
    *   The "Select Image Directory" button is visible and enabled.
    *   The image grid area is initially empty or shows a placeholder message.
    *   The classification buttons (0, 1, 10s, 100s, Skip, Notes) are visible and potentially disabled until a directory is loaded.
    *   The "Keyboard Shortcuts" toggle button is visible and the shortcut list is initially hidden/minimized.
    *   The Notes section is visible but empty.

---

## Feature: Keyboard Shortcuts Toggle

### Test Case: Toggle Visibility

*   **Title:** Verify Keyboard Shortcuts visibility toggle
*   Status: [x] Implemented
*   **Preconditions:** Application is launched.
*   **Steps:**
    1.  Observe the "Keyboard Shortcuts" button/area.
    2.  Click the "Keyboard Shortcuts" button.
    3.  Observe the shortcuts list/area.
    4.  Click the "Keyboard Shortcuts" button again.
    5.  Observe the shortcuts list/area.
*   **Expected Results:**
    *   Initially, the shortcuts list is hidden/minimized.
    *   After the first click, the shortcuts list becomes visible and displays the correct shortcut information (e.g., "0: Zero", "1: Singles", "2: Dozens", "3: Hundreds", "S: Skip", "N: Notes", "->: Next Image", "<-: Previous Image").
    *   After the second click, the shortcuts list is hidden/minimized again.

---

## Feature: Image Directory Loading

### Test Case: Load Valid Directory

*   **Title:** Load a directory containing valid image files
*   Status: [ ] Not Implemented
*   **Preconditions:** Application is launched. A directory with JPG/PNG images exists.
*   **Steps:**
    1.  Click the "Select Image Directory" button.
    2.  In the native file dialog, navigate to and select the directory containing images.
    3.  Click "Open" or equivalent.
*   **Expected Results:**
    *   The file dialog closes.
    *   Thumbnails of the images from the selected directory appear in the image grid.
    *   The classification buttons become enabled.
    *   The first image in the directory is highlighted or selected by default.
    *   The main image display area shows the first image (if applicable).
    *   The status bar or title updates to show the directory path and image count.

### Test Case: Load Empty Directory

*   **Title:** Attempt to load an empty directory
*   Status: [ ] Not Implemented
*   **Preconditions:** Application is launched. An empty directory exists.
*   **Steps:**
    1.  Click the "Select Image Directory" button.
    2.  Select the empty directory.
    3.  Click "Open".
*   **Expected Results:**
    *   The image grid remains empty or shows a "No images found" message.
    *   Classification buttons might remain disabled or show appropriate state.
    *   Status bar updates to show the directory path and 0 images.

### Test Case: Load Directory with No Images

*   **Title:** Attempt to load a directory containing no image files (only other file types)
*   Status: [ ] Not Implemented
*   **Preconditions:** Application is launched. A directory with non-image files exists.
*   **Steps:**
    1.  Click the "Select Image Directory" button.
    2.  Select the directory with non-image files.
    3.  Click "Open".
*   **Expected Results:**
    *   The image grid remains empty or shows a "No images found" message.
    *   Classification buttons might remain disabled.
    *   Status bar updates to show the directory path and 0 images.

---

## Feature: Image Classification

### Test Case: Classify Image (e.g., 'Singles')

*   **Title:** Classify an image as 'Singles' using the button
*   Status: [ ] Not Implemented
*   **Preconditions:** An image directory is loaded. An image is selected/highlighted.
*   **Steps:**
    1.  Click the '1' (Singles) classification button.
*   **Expected Results:**
    *   The selected image thumbnail gets a visual indicator (border, checkmark) showing it's classified as 'Singles'.
    *   The application automatically advances to the next image in the grid.
    *   The classification data for the image is stored correctly (this might need verification by checking saved data later or internal state if possible).

### Test Case: Classify Image using Keyboard Shortcut (e.g., 'Dozens')

*   **Title:** Classify an image as 'Dozens' using the keyboard shortcut '2'
*   Status: [ ] Not Implemented
*   **Preconditions:** An image directory is loaded. An image is selected/highlighted.
*   **Steps:**
    1.  Press the '2' key on the keyboard.
*   **Expected Results:**
    *   The selected image thumbnail gets a visual indicator for 'Dozens'.
    *   The application automatically advances to the next image.
    *   Classification data is stored.

*(Add similar test cases for 0, 100s, Skip)*

---

## Feature: Image Navigation

### Test Case: Navigate Next/Previous using Buttons

*   **Title:** Navigate between images using Next/Previous buttons (if they exist)
*   Status: [ ] Not Implemented
*   **Preconditions:** An image directory with multiple images is loaded.
*   **Steps:**
    1.  Click the "Next Image" button.
    2.  Click the "Previous Image" button.
*   **Expected Results:**
    *   Clicking "Next" selects/highlights the next image in the grid.
    *   Clicking "Previous" selects/highlights the previous image.
    *   Navigation wraps around or stops at the ends as designed.

### Test Case: Navigate Next/Previous using Arrow Keys

*   **Title:** Navigate between images using Right/Left Arrow keys
*   Status: [ ] Not Implemented
*   **Preconditions:** An image directory with multiple images is loaded.
*   **Steps:**
    1.  Press the Right Arrow key.
    2.  Press the Left Arrow key.
*   **Expected Results:**
    *   Pressing Right Arrow selects/highlights the next image.
    *   Pressing Left Arrow selects/highlights the previous image.
    *   Navigation wraps/stops as designed.

---

## Feature: Notes

### Test Case: Add a Note to an Image

*   **Title:** Add and save a note for a specific image
*   Status: [ ] Not Implemented
*   **Preconditions:** An image directory is loaded. An image is selected.
*   **Steps:**
    1.  Click into the Notes text area or press the 'N' shortcut.
    2.  Type "Test note for this image".
    3.  Click outside the notes area or navigate to another image (verify how notes are saved - automatically or via button?).
    4.  Navigate back to the original image.
*   **Expected Results:**
    *   The Notes text area should contain "Test note for this image" when the image is re-selected.
    *   The note data is stored correctly.

*(Add more features and test cases as needed, e.g., Zoom, Data Saving/Exporting, Error Handling)*
