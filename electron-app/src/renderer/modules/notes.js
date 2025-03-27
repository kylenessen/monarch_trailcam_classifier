import { getState, updateState, getCurrentState, getCurrentImageFile, setImageClassification, getImageClassification } from './state.js';
import { saveClassifications } from './file-system.js';
import { updateNotesButtonState } from './ui.js'; // To update button appearance

// --- DOM Element References ---
let notesDialog = null;
let notesContent = null;
let closeNotesButton = null;

// --- Initialization ---

/**
 * Initializes the notes dialog functionality and event listeners.
 */
export function initializeNotes() {
    notesDialog = document.getElementById('notes-dialog');
    notesContent = document.getElementById('notes-content');
    closeNotesButton = document.getElementById('close-notes');

    if (!notesDialog || !notesContent || !closeNotesButton) {
        console.error('Notes initialization failed: one or more elements not found.');
        return;
    }

    // Event listeners (Note: The main toggle is handled by the notes button in ui.js)
    closeNotesButton.addEventListener('click', closeNotesDialog);
    notesContent.addEventListener('input', handleNotesChange);
    
    // Add listener to close dialog on Escape key press when it's visible
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && getState().notesDialog.isVisible) {
            closeNotesDialog();
        }
    });

    console.log('Notes functionality initialized.');
}

// --- Dialog Management ---

/**
 * Toggles the visibility of the notes dialog.
 */
export function toggleNotesDialog() {
    if (!notesDialog || !notesContent) return;

    const state = getCurrentState();
    const isVisible = state.notesDialog.isVisible;

    if (!isVisible) {
        // Show dialog
        updateState({ notesDialog: { isVisible: true } });
        notesDialog.classList.add('show');

        // Load existing notes for the current image
        const currentImage = getCurrentImageFile();
        if (currentImage) {
            const classification = getImageClassification(currentImage);
            notesContent.value = classification?.notes || '';
        } else {
            notesContent.value = ''; // Clear if no image selected
        }
        
        notesContent.focus(); // Focus the textarea
    } else {
        // Hide dialog
        closeNotesDialog();
    }
}

/**
 * Closes the notes dialog.
 */
export function closeNotesDialog() {
    if (!notesDialog) return;
    
    updateState({ notesDialog: { isVisible: false } });
    notesDialog.classList.remove('show');
}

// --- Notes Content Handling ---

/**
 * Handles changes in the notes textarea content.
 * @param {Event} event - The input event object.
 */
function handleNotesChange(event) {
    const currentImage = getCurrentImageFile();
    if (!currentImage) return; // No image selected, do nothing

    const newNotes = event.target.value;
    
    // Get current classification, ensure it exists
    let classification = getImageClassification(currentImage);
    if (!classification) {
         // If no classification exists yet, create a basic one
         const state = getCurrentState();
         classification = {
             confirmed: false,
             cells: {}, // Or createDefaultGridCells() if needed immediately
             index: state.imageFiles.indexOf(currentImage),
             notes: ''
         };
    }

    // Update the notes in the classification object
    const updatedClassification = {
        ...classification,
        notes: newNotes
    };

    // Update the state
    setImageClassification(currentImage, updatedClassification);

    // Update the notes button appearance (e.g., highlight if notes exist)
    updateNotesButtonState();

    // Auto-save the classifications
    saveClassifications(getState().classifications);
}

/**
 * Resets the notes dialog state, typically when changing images.
 */
export function resetNotesDialogState() {
    if (notesDialog && notesDialog.classList.contains('show')) {
        closeNotesDialog();
    }
    if (notesContent) {
        notesContent.value = ''; // Clear content visually
    }
}
