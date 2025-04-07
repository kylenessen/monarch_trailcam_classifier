import {
    getState,
    updateState,
    getCurrentState,
    getImageClassification,
    setImageClassification,
    createDefaultGridCells,
    getCurrentImageFile, // Added for undo
    DEFAULT_CELL_CLASSIFICATION
} from './state.js';
import { saveClassifications } from './file-system.js';
import { showNotification } from './utils.js';
import { disableClassificationTools } from './ui.js'; // Removed displayImageAndClassifications import
import { loadImageByIndex } from './image-grid.js'; // Added loadImageByIndex import for refresh
import { pushState, popState, clearHistory } from './history.js'; // Added history import

/**
 * Toggles the confirmation status of an image classification.
 * @param {string} imageFile - The filename of the image.
 * @param {string} user - The username/initials confirming the image.
 * @param {boolean} [markAsNight=false] - Whether to mark this confirmation as a 'Night' image.
 */
export function confirmImage(imageFile, user, markAsNight = false) {
    const classification = getImageClassification(imageFile) || {}; // Get current or empty object
    const isCurrentlyConfirmed = classification.confirmed || false;

    // Prepare updated classification data
    const updatedClassification = {
        ...classification, // Spread existing data (like cells, index, notes)
        confirmed: !isCurrentlyConfirmed, // Toggle status
        user: !isCurrentlyConfirmed ? user : (classification.user || null), // Add user only when confirming
        isNight: !isCurrentlyConfirmed ? markAsNight : false // Set isNight on confirm, explicitly reset to false on unconfirm
    };

    // Ensure cells exist if confirming a potentially new entry
    if (!updatedClassification.cells) {
        updatedClassification.cells = createDefaultGridCells();
    }
    // Ensure index exists
    if (typeof updatedClassification.index === 'undefined') {
        const state = getCurrentState();
        updatedClassification.index = state.imageFiles.indexOf(imageFile);
    }


    // Update the state
    setImageClassification(imageFile, updatedClassification);

    // Lock/unlock UI elements based on the new confirmation status
    disableClassificationTools(updatedClassification.confirmed);

    // Clear history if confirming
    if (updatedClassification.confirmed) {
        clearHistory(imageFile);
    }

    // Note: Saving is handled in the UI event handler after calling this function
    showNotification(`Image ${updatedClassification.confirmed ? 'confirmed' : 'unlocked'}`, 'success');
}

/**
 * Copies classifications from the previous confirmed image to the current image.
 * @param {string} currentImageFile - The filename of the current image.
 * @param {string} previousImageFile - The filename of the previous image.
 */
export function copyFromPrevious(currentImageFile, previousImageFile) {
    const state = getCurrentState();
    const currentClassification = getImageClassification(currentImageFile);
    const previousClassification = getImageClassification(previousImageFile);

    // --- Validation ---
    // Cannot copy if current image is confirmed
    if (currentClassification?.confirmed) {
        showNotification('Cannot copy to a confirmed image. Unlock it first.', 'error');
        return false;
    }
    // Cannot copy if previous image doesn't exist or isn't confirmed
    if (!previousClassification || !previousClassification.confirmed) {
        showNotification('Previous image must be confirmed before copying.', 'error');
        return false;
    }
    // Cannot copy if previous image has no cell data (shouldn't happen if confirmed, but check anyway)
    if (!previousClassification.cells) {
        showNotification('Previous image has no classification data to copy.', 'error');
        return false;
    }
    // Check edit permissions for the *current* image (redundant check maybe, but safe)
    // if (!canEditImage(currentImageFile)) { // canEditImage would need to be imported or moved to utils
    //     showNotification('Please confirm all previous images before making annotations.', 'error');
    //     return false;
    // }


    // --- Save current state before overwriting ---
    const cellsBeforeCopy = currentClassification?.cells;
    if (cellsBeforeCopy) {
        pushState(currentImageFile, cellsBeforeCopy);
    }

    // --- Perform Copy ---
    const updatedClassification = {
        ...(currentClassification || {}), // Keep existing index, notes, etc.
        cells: JSON.parse(JSON.stringify(previousClassification.cells)), // Deep copy cells
        confirmed: false, // Ensure current image remains unconfirmed
        user: null, // Clear user from copied data
        isNight: false // Explicitly set isNight to false when copying
    };

    // Ensure index exists if currentClassification was initially null/undefined
    if (typeof updatedClassification.index === 'undefined') {
        updatedClassification.index = state.imageFiles.indexOf(currentImageFile);
    }

    setImageClassification(currentImageFile, updatedClassification);

    showNotification('Classifications copied from previous image.', 'success');
    return true; // Indicate success
    // Note: Saving and reloading the image display are handled in the UI event handler
}

/**
 * Resets the classification for the current image to the default state.
 * @param {string} imageFile - The filename of the image to reset.
 */
export function resetImage(imageFile) {
    const currentClassification = getImageClassification(imageFile);

    // --- Validation ---
    if (currentClassification?.confirmed) {
        showNotification('Cannot reset a confirmed image. Unlock it first.', 'error');
        return false;
    }
    // Check edit permissions (redundant check maybe, but safe)
    // if (!canEditImage(imageFile)) { // canEditImage would need to be imported or moved to utils
    //     showNotification('Please confirm all previous images before making annotations.', 'error');
    //     return false;
    // }

    // --- Save current state before overwriting ---
    const cellsBeforeReset = currentClassification?.cells;
    if (cellsBeforeReset) {
        pushState(imageFile, cellsBeforeReset);
    }

    // --- Perform Reset ---
    const defaultCells = createDefaultGridCells();
    const resetClassification = {
        // Preserve index and potentially notes, reset others
        index: currentClassification?.index ?? getCurrentState().imageFiles.indexOf(imageFile), // Ensure index is present
        notes: currentClassification?.notes || '', // Keep existing notes
        cells: defaultCells,
        confirmed: false,
        user: null,
        isNight: false // Explicitly set isNight to false on reset
    };

    setImageClassification(imageFile, resetClassification);

    showNotification('Image classifications reset.', 'success');
    return true; // Indicate success
    // Note: Saving and reloading the image display are handled in the UI event handler
}

/**
 * Reverts the last classification change made to the current image from the history.
 */
export function undoLastChange() {
    const currentImage = getCurrentImageFile();
    if (!currentImage) {
        showNotification('No image selected to undo.', 'warning');
        return;
    }

    const currentClassification = getImageClassification(currentImage);
    if (currentClassification?.confirmed) {
        showNotification('Cannot undo changes on a confirmed image.', 'warning');
        return;
    }

    const previousCellsState = popState(currentImage);

    if (!previousCellsState) {
        showNotification('Nothing to undo for this image.', 'info');
        return;
    }

    // Restore the cells state, keeping other properties like index, notes, confirmed status
    const restoredClassification = {
        ...(currentClassification || {}), // Keep existing data (index, notes, confirmed=false, user=null etc.)
        cells: previousCellsState // Use the popped state
    };

    // Ensure index exists if currentClassification was initially null/undefined
    if (typeof restoredClassification.index === 'undefined') {
        const state = getCurrentState(); // Need state access if not already available
        restoredClassification.index = state.imageFiles.indexOf(currentImage);
    }

    // Update the main state
    setImageClassification(currentImage, restoredClassification);

    // Trigger UI refresh to show the restored state by reloading the image
    // loadImageByIndex handles redrawing the grid and updating UI states
    loadImageByIndex(restoredClassification.index);

    showNotification('Undo successful', 'success');

    // Note: Saving is handled separately by the auto-save mechanism or manual save trigger
}
