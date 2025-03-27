// Global state
let currentState = {
    deploymentFolder: null,
    imagesFolder: null,
    imageFiles: [],
    currentImageIndex: -1,
    classifications: {},
    selectedCell: null,
    selectedTool: '10-99', // Default tool
    classificationFile: null,
    originalImageWidth: null,
    originalImageHeight: null,
    resizeObserver: null,
    isLocked: false,
    isColorMode: false,  // Default to black and white
    notesDialog: {
        isVisible: false
    }
};

// Classification categories and their colors
export const CLASSIFICATIONS = {
    '0': { label: '0', color: 'transparent' },
    '1-9': { label: '1-9', color: 'rgba(255, 235, 59, 0.3)' },
    '10-99': { label: '10-99', color: 'rgba(255, 152, 0, 0.3)' },
    '100-999': { label: '100-999', color: 'rgba(244, 67, 54, 0.3)' },
    '1000+': { label: '1000+', color: 'rgba(156, 39, 176, 0.3)' }
};

// Grid configuration
export const GRID_CONFIG = {
    columns: 16,
    rows: 9
};

// Define the category order for cycling
export const CATEGORIES = ['0', '1-9', '10-99', '100-999', '1000+'];

// Default classification for each cell
export const DEFAULT_CELL_CLASSIFICATION = {
    count: '0',
    directSun: false
};

// --- State Accessors and Mutators ---

export function getState() {
    // Return a shallow copy to prevent direct modification of the state object outside of mutators
    return { ...currentState };
}

export function updateState(newState) {
    currentState = { ...currentState, ...newState };
}

export function getCurrentState() {
    return currentState;
}

export function setClassificationForCell(imageName, cellId, classification) {
    // Ensure classification entry exists with proper structure
    if (!currentState.classifications[imageName] || !currentState.classifications[imageName].cells) {
        currentState.classifications[imageName] = {
            confirmed: false,
            cells: {},
            index: currentState.imageFiles.indexOf(imageName) // Ensure index is set if creating new entry
        };
    }
    
    // Ensure cells object exists
    if (!currentState.classifications[imageName].cells) {
        currentState.classifications[imageName].cells = {};
    }

    currentState.classifications[imageName].cells[cellId] = classification;
}

export function getClassificationForCell(imageName, cellId) {
    return currentState.classifications[imageName]?.cells?.[cellId];
}

export function getImageClassification(imageName) {
    return currentState.classifications[imageName];
}

export function setImageClassification(imageName, classificationData) {
    currentState.classifications[imageName] = classificationData;
}

export function getAllClassifications() {
    return currentState.classifications;
}

export function setAllClassifications(classifications) {
    currentState.classifications = classifications;
}

export function getCurrentImageFile() {
    if (currentState.currentImageIndex >= 0 && currentState.currentImageIndex < currentState.imageFiles.length) {
        return currentState.imageFiles[currentState.currentImageIndex];
    }
    return null;
}

export function resetApplicationState() {
    currentState.deploymentFolder = null;
    currentState.imagesFolder = null;
    currentState.imageFiles = [];
    currentState.currentImageIndex = -1;
    currentState.classifications = {};
    currentState.selectedCell = null;
    currentState.selectedTool = '10-99'; // Reset to default tool
    currentState.classificationFile = null;
    currentState.originalImageWidth = null;
    currentState.originalImageHeight = null;
    if (currentState.resizeObserver) {
        currentState.resizeObserver.disconnect();
        currentState.resizeObserver = null;
    }
    currentState.isLocked = false;
    currentState.isColorMode = false;
    currentState.notesDialog = {
        isVisible: false
    };
}

// Helper to create default grid cells structure
export function createDefaultGridCells() {
    const cells = {};
    for (let row = 0; row < GRID_CONFIG.rows; row++) {
        for (let col = 0; col < GRID_CONFIG.columns; col++) {
            // Use a utility function (which we'll define later) if needed, or keep it simple
            const cellId = `cell_${row}_${col}`; 
            cells[cellId] = { ...DEFAULT_CELL_CLASSIFICATION }; // Ensure a copy
        }
    }
    return cells;
}
