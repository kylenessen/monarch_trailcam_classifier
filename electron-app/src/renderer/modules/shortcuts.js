import { 
    cycleCategory, 
    navigateImageHandler, 
    findNextUnclassifiedHandler, 
    confirmImageHandler, 
    copyFromPreviousHandler,
    resetImageHandler, // Added reset handler import
    toggleShortcutsHelp // Assuming this UI function is exported from ui.js
} from './ui.js'; 
import { toggleNotesDialog } from './notes.js'; // Assuming this is in notes.js

// Define keyboard shortcuts mapping
// Note: Zoom ('Space') and F-key ('f' for sunlight) are handled separately 
// in image-grid.js and zoom.js because they involve holding keys or direct interaction
// with the grid/image area.
const KEYBOARD_SHORTCUTS = {
    // Navigation
    'ArrowRight': () => navigateImageHandler('next'),
    'd': () => navigateImageHandler('next'),
    'D': () => navigateImageHandler('next'), // Allow Shift+D
    'ArrowLeft': () => navigateImageHandler('previous'),
    'a': () => navigateImageHandler('previous'),
    'A': () => navigateImageHandler('previous'), // Allow Shift+A

    // Category Cycling
    'e': () => cycleCategory('next'),
    'E': () => cycleCategory('next'), // Allow Shift+E
    'q': () => cycleCategory('previous'),
    'Q': () => cycleCategory('previous'), // Allow Shift+Q

    // Actions
    'ArrowUp': () => confirmImageHandler(),
    'w': () => confirmImageHandler(),
    'W': () => confirmImageHandler(), // Allow Shift+W
    'ArrowDown': () => copyFromPreviousHandler(),
    's': () => copyFromPreviousHandler(),
    'S': () => copyFromPreviousHandler(), // Allow Shift+S
    
    // Notes
    'n': () => toggleNotesDialog(),
    'N': () => toggleNotesDialog(), // Allow Shift+N

    // Help
    'h': () => toggleShortcutsHelp(),
    'H': () => toggleShortcutsHelp(), // Allow Shift+H
    
    // Reset (Optional - can add if needed, maybe 'r'?)
    // 'r': () => resetImageHandler(), 
    // 'R': () => resetImageHandler(),
};

/**
 * Handles keydown events for shortcuts.
 * @param {KeyboardEvent} event - The keyboard event.
 */
function handleKeyboardShortcuts(event) {
    // Ignore shortcuts if focus is on an input field or textarea
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }

    // Ignore if modifier keys like Ctrl, Alt, Meta are pressed (unless part of the shortcut definition, which isn't the case here)
    // This prevents conflicts with browser/OS shortcuts. Allow Shift key.
    if (event.ctrlKey || event.altKey || event.metaKey) {
        return;
    }

    const handler = KEYBOARD_SHORTCUTS[event.key];
    if (handler) {
        event.preventDefault(); // Prevent default browser action for handled keys (like arrow keys scrolling)
        handler();
    }
}

/**
 * Initializes the keyboard shortcut listener.
 */
export function initializeShortcuts() {
    document.addEventListener('keydown', handleKeyboardShortcuts);
    console.log('Keyboard shortcuts initialized.');
}
