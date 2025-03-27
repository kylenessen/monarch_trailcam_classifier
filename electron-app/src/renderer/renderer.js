// --- Module Imports ---
import { initializeUI } from './modules/ui.js';
import { initializeShortcuts } from './modules/shortcuts.js';
import { initializeZoom, resetZoomState } from './modules/zoom.js';
import { initializeNotes, resetNotesDialogState } from './modules/notes.js';
import { setupGridKeyListener, loadImageByIndex } from './modules/image-grid.js'; // Import loadImageByIndex if needed for initial load logic here
import { resetApplicationState } from './modules/state.js'; // Import reset state if needed

// --- Global Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded and parsed. Initializing application modules.');

    // Initialize core UI elements and general event listeners
    initializeUI();

    // Initialize specific feature modules
    initializeNotes();
    initializeZoom();
    
    // Initialize keyboard listeners
    initializeShortcuts(); // Handles general shortcuts
    setupGridKeyListener(); // Handles F-key listener specifically for the grid

    // Initial state setup (e.g., display welcome message or prompt for folder)
    // The initial folder prompt is now handled within initializeUI -> setupEventListeners -> handleFolderSelection
    
    console.log('Application initialization complete.');
});

// --- Global Event Listeners (if any remain absolutely necessary) ---
// Example: Resetting zoom/notes state when window loses focus? (Probably not needed)
// window.addEventListener('blur', () => {
//     resetZoomState();
//     resetNotesDialogState(); // Close notes dialog if window loses focus
// });

// --- Cleanup ---
// Optional: Add cleanup logic if needed when the window is about to close
// window.addEventListener('beforeunload', () => {
//     // Perform cleanup, e.g., ensure classifications are saved one last time
//     // Note: saveClassifications is called frequently already by modules
// });

// All specific logic (button clicks, image loading, grid interaction, state changes)
// is now handled within the imported modules. This file just orchestrates the setup.
