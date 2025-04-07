// Manages the undo history for image classifications (in-memory only)

import { updateUndoButtonState } from './ui.js'; // We'll import this later, assuming it exists in ui.js

let historyStore = {}; // { "imageName": [cellsSnapshot1, cellsSnapshot2], ... }
const MAX_HISTORY_SIZE = 15; // Max number of undo steps per image

/**
 * Pushes a snapshot of the current cells state onto the history stack for an image.
 * Should only be called for unconfirmed images.
 * @param {string} imageName - The filename of the image.
 * @param {object} cellsState - The current state of the image's cells object.
 */
export function pushState(imageName, cellsState) {
    if (!imageName || !cellsState) {
        console.error("pushState called with invalid imageName or cellsState");
        return;
    }

    if (!historyStore[imageName]) {
        historyStore[imageName] = [];
    }

    // Create a deep copy to avoid mutations
    const snapshot = JSON.parse(JSON.stringify(cellsState));

    // Avoid pushing identical consecutive states (optional optimization)
    const lastState = historyStore[imageName][historyStore[imageName].length - 1];
    if (lastState && JSON.stringify(lastState) === JSON.stringify(snapshot)) {
        // console.log("Skipping pushState: state identical to previous.");
        return;
    }


    historyStore[imageName].push(snapshot);

    // Limit history size
    if (historyStore[imageName].length > MAX_HISTORY_SIZE) {
        historyStore[imageName].shift(); // Remove the oldest state
    }

    // Update the UI button state after modifying history
    updateUndoButtonState();
}

/**
 * Pops the most recent state snapshot from the history stack for an image.
 * @param {string} imageName - The filename of the image.
 * @returns {object | null} The previous cells state snapshot, or null if history is empty.
 */
export function popState(imageName) {
    if (!imageName || !historyStore[imageName] || historyStore[imageName].length === 0) {
        return null;
    }

    const previousState = historyStore[imageName].pop();

    // Update the UI button state after modifying history
    updateUndoButtonState();

    return previousState;
}

/**
 * Clears the undo history for a specific image.
 * @param {string} imageName - The filename of the image.
 */
export function clearHistory(imageName) {
    if (historyStore[imageName]) {
        historyStore[imageName] = [];
    }
    // Update the UI button state after clearing history
    updateUndoButtonState();
}

/**
 * Checks if there is any undo history available for a specific image.
 * @param {string} imageName - The filename of the image.
 * @returns {boolean} True if history exists, false otherwise.
 */
export function hasHistory(imageName) {
    return !!(historyStore[imageName] && historyStore[imageName].length > 0);
}
