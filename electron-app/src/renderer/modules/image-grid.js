// Removed: import path from 'path';
import {
    getState,
    updateState,
    getCurrentState,
    setClassificationForCell,
    getClassificationForCell,
    getImageClassification,
    getGridConfig, // Added
    CLASSIFICATIONS,
    // GRID_CONFIG, // Removed
    DEFAULT_CELL_CLASSIFICATION
} from './state.js';
import { getImageData, saveClassifications } from './file-system.js';
import { showNotification, generateCellId } from './utils.js';
import {
    updateProgress,
    updateNavigationButtons,
    disableClassificationTools,
    updateConfirmButtonState,
    updateNotesButtonState,
    clearImageContainer
} from './ui.js'; // Import UI update functions

// Keep track of F key state locally within this module if only grid interaction uses it
let isFKeyPressed = false;

// --- Image Loading and Display ---

export async function loadImageByIndex(index) { // Already async, good.
    const state = getCurrentState();

    // Basic validation
    if (index < 0 || index >= state.imageFiles.length) {
        console.error('Invalid image index requested:', index);
        showNotification('Invalid image index.', 'error');
        return;
    }

    const imageFile = state.imageFiles[index];
    // Use preload API for path joining
    const imagePath = await window.electronAPI.pathJoin(state.imagesFolder, imageFile);

    try {
        const imageData = await getImageData(imagePath); // Get base64 data
        if (!imageData) {
            // Error handled within getImageData, just exit
            return;
        }

        // Update state *before* async UI operations
        updateState({ currentImageIndex: index });

        // Setup display
        await setupImageDisplay(imageFile, imageData);

        // Update UI elements after image is potentially displayed
        updateNavigationButtons();
        updateProgress();
        updateNotesButtonState(); // Update based on the new image's notes
        updateConfirmButtonState(imageFile); // Update confirm button based on new image's state

        // Check if the newly loaded image is confirmed and disable tools if necessary
        const classification = getImageClassification(imageFile);
        disableClassificationTools(classification?.confirmed || false);

    } catch (error) {
        console.error(`Error loading image at index ${index}:`, error);
        showNotification(`Error loading image: ${error.message}`, 'error');
        clearImageContainer(); // Clear the container on error
        updateState({ currentImageIndex: -1 }); // Reset index if load fails
        updateNavigationButtons();
        updateProgress();
    }
}

async function setupImageDisplay(imageFile, imageData) {
    const imageContainer = document.getElementById('image-container');
    if (!imageContainer) return;

    clearImageContainer(); // Clear previous content and disconnect observer

    const wrapper = createImageWrapper(imageFile);
    imageContainer.appendChild(wrapper);

    return new Promise((resolve, reject) => {
        const img = new Image();
        img.id = 'display-image';

        img.onload = () => {
            try {
                // Store original dimensions in state
                updateState({
                    originalImageWidth: img.naturalWidth,
                    originalImageHeight: img.naturalHeight
                });

                // Apply initial color mode
                updateImageColorMode(img);

                // Create the grid
                createGrid(wrapper, img.naturalWidth, img.naturalHeight);

                // Setup resize observer for the new image/wrapper
                setupResizeObserver(wrapper);

                resolve();
            } catch (error) {
                console.error("Error during image onload processing:", error);
                reject(error);
            }
        };

        img.onerror = () => {
            console.error(`Failed to load image: ${imageFile}`);
            wrapper.innerHTML = '<div class="error-message">Failed to load image</div>';
            reject(new Error(`Failed to load image: ${imageFile}`));
        };

        img.src = `data:image/jpeg;base64,${imageData}`;
        wrapper.appendChild(img);
    });
}

function createImageWrapper(imageFile) {
    const wrapper = document.createElement('div');
    wrapper.className = 'image-wrapper';
    const classification = getImageClassification(imageFile);

    // Add status class based on confirmed and isNight status
    if (classification?.confirmed) {
        if (classification.isNight) {
            wrapper.classList.add('status-night');
        } else {
            wrapper.classList.add('status-confirmed');
        }
    }
    // No class added if not confirmed

    return wrapper;
}

// --- Grid Creation and Interaction ---

function createGrid(wrapper, imageWidth, imageHeight) {
    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'grid-overlay';

    const state = getCurrentState();
    const { rows, columns } = getGridConfig(); // Get dynamic config

    // Ensure grid config is valid before creating grid
    if (!rows || !columns) {
        console.error("Cannot create grid: Grid configuration not set or invalid.", { rows, columns });
        showNotification("Error: Grid configuration is missing.", "error");
        // Optionally clear the wrapper or show an error message within it
        wrapper.innerHTML = '<div class="error-message">Grid configuration missing</div>';
        return; // Stop grid creation
    }

    const currentImageFile = state.imageFiles[state.currentImageIndex];
    const imageClassifications = getImageClassification(currentImageFile); // Get full classification object

    for (let r = 0; r < rows; r++) { // Use dynamic rows
        for (let c = 0; c < columns; c++) { // Use dynamic columns
            const cellId = generateCellId(r, c); // Use loop variables r, c
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.row = r; // Use loop variable r
            cell.dataset.col = c; // Use loop variable c
            cell.dataset.cellId = cellId; // Store cellId for easy access in handler

            // Set dimensions and position using percentages with dynamic columns/rows
            cell.style.width = `${(1 / columns) * 100}%`;
            cell.style.height = `${(1 / rows) * 100}%`;
            cell.style.left = `${(c / columns) * 100}%`;
            cell.style.top = `${(r / rows) * 100}%`;

            // Apply existing classification style
            // Ensure cells object exists before accessing
            const cellClassification = imageClassifications?.cells?.[cellId] || DEFAULT_CELL_CLASSIFICATION;
            applyCellStyle(cell, cellClassification);

            // Add event listeners
            cell.addEventListener('click', handleCellClick);
            cell.addEventListener('contextmenu', handleCellContextMenu);

            gridOverlay.appendChild(cell);
        }
    }
    wrapper.appendChild(gridOverlay);
}

function handleCellClick(event) {
    const cell = event.target;
    const cellId = cell.dataset.cellId;
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];

    if (!currentImageFile || state.isLocked || getImageClassification(currentImageFile)?.confirmed) {
        // If locked, confirmed, or no image, do nothing on normal click unless a modifier is pressed
        if (!event.ctrlKey && !event.metaKey && !isFKeyPressed) {
            return;
        }
    }

    // Check edit permissions only if trying to modify
    if ((event.ctrlKey || event.metaKey || isFKeyPressed) && !canEditImage(currentImageFile)) {
        showNotification('Please confirm all previous images before making annotations.', 'error');
        return;
    }

    // Get current cell classification or default if none exists
    const currentCellClassification = getClassificationForCell(currentImageFile, cellId)
        || { ...DEFAULT_CELL_CLASSIFICATION }; // Use a copy of default

    let classificationChanged = false;

    // Handle Ctrl/Cmd + Click for count classification
    if (event.ctrlKey || event.metaKey) {
        if (currentCellClassification.count !== state.selectedTool) {
            currentCellClassification.count = state.selectedTool;
            classificationChanged = true;
        }
    }

    // Handle F key + Click for sunlight classification
    if (isFKeyPressed) {
        currentCellClassification.directSun = !currentCellClassification.directSun;
        classificationChanged = true;
    }

    // Update state and UI only if a change occurred
    if (classificationChanged) {
        setClassificationForCell(currentImageFile, cellId, currentCellClassification);
        applyCellStyle(cell, currentCellClassification);
        saveClassifications(getState().classifications); // Save immediately after change
    }
}

function handleCellContextMenu(event) {
    event.preventDefault(); // Prevent default context menu

    const cell = event.target;
    const cellId = cell.dataset.cellId;
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];

    // Only allow reset if Ctrl/Cmd is pressed and image is editable
    if ((event.metaKey || event.ctrlKey) && currentImageFile && !state.isLocked && !getImageClassification(currentImageFile)?.confirmed) {
        if (!canEditImage(currentImageFile)) {
            showNotification('Please confirm all previous images before making annotations.', 'error');
            return;
        }

        const defaultClassification = { ...DEFAULT_CELL_CLASSIFICATION };
        setClassificationForCell(currentImageFile, cellId, defaultClassification);
        applyCellStyle(cell, defaultClassification);
        saveClassifications(getState().classifications); // Save immediately
    }
}

function applyCellStyle(cell, classification) {
    const countClass = CLASSIFICATIONS[classification.count];
    cell.style.backgroundColor = countClass ? countClass.color : 'transparent'; // Fallback

    // Apply sunlight style
    if (classification.directSun) {
        // Use a more visible style for direct sun
        cell.style.border = '2px solid yellow'; // Example: bright yellow border
        cell.style.boxSizing = 'border-box'; // Ensure border is included in element size
    } else {
        // Reset to default border
        cell.style.border = '1px solid rgba(255, 255, 255, 0.5)'; // Default subtle border
        cell.style.boxSizing = 'border-box';
    }
}

// --- Utility Functions for this Module ---

function setupResizeObserver(wrapper) {
    // Disconnect existing observer if any
    const existingObserver = getState().resizeObserver;
    if (existingObserver) {
        existingObserver.disconnect();
    }

    // Create and store a new observer
    const newObserver = new ResizeObserver((entries) => {
        // The observer itself doesn't need to *do* anything here for simple scaling,
        // but it's good practice to have it if complex resizing logic were needed.
        // We just need it attached to the wrapper.
    });

    newObserver.observe(wrapper);
    updateState({ resizeObserver: newObserver }); // Store the observer in state
}

export function updateImageColorMode(imgElement = null) {
    const img = imgElement || document.getElementById('display-image');
    if (!img) return;

    const state = getCurrentState();
    img.style.filter = state.isColorMode ? 'none' : 'grayscale(100%)';
}

export async function findNextUnclassified() {
    const state = getCurrentState();
    // Start searching from the current index + 1, wrapping around
    for (let i = 1; i <= state.imageFiles.length; i++) {
        const checkIndex = (state.currentImageIndex + i) % state.imageFiles.length;
        const imageName = state.imageFiles[checkIndex];
        const classification = getImageClassification(imageName);

        // Check if classification exists and if it's not confirmed
        if (!classification || !classification.confirmed) {
            await loadImageByIndex(checkIndex);
            return; // Found and loaded
        }
    }
    // If loop completes, all images are classified
    showNotification('All images have been classified!', 'info');
    // Optionally, load the first image again or stay on the last one
    if (state.imageFiles.length > 0 && state.currentImageIndex === -1) {
        await loadImageByIndex(0); // Load first image if none was loaded initially
    } else if (state.currentImageIndex !== -1) {
        // Stay on the current image, maybe disable "Next Unclassified" button
    }
}

// Check if the current image or previous images prevent editing
async function canEditImage(imageFile) { // Make async
    const state = getCurrentState();
    const classification = getImageClassification(imageFile);

    // Cannot edit if the image itself is confirmed
    if (classification?.confirmed) {
        // showNotification('This image is confirmed. Unlock it first to make changes.', 'warning');
        return false;
    }

    // Check if all *previous* images are confirmed
    const currentIndex = classification?.index ?? state.imageFiles.indexOf(imageFile);
    if (currentIndex === -1) return false; // Image not found in list?

    for (let i = 0; i < currentIndex; i++) {
        const prevImageFile = state.imageFiles[i];
        const prevClassification = getImageClassification(prevImageFile);
        if (!prevClassification || !prevClassification.confirmed) {
            // Found a previous unconfirmed image
            // const prevImageBaseName = await window.electronAPI.getPathBasename(prevImageFile); // Use preload API
            // showNotification(`Please confirm image ${i + 1} (${prevImageBaseName}) first.`, 'warning');
            return false;
        }
    }

    return true; // All previous images are confirmed
}


// --- Event Listeners for F key ---
// These need to be attached to the document in the main renderer.js or ui.js initialization

export function setupGridKeyListener() {
    document.addEventListener('keydown', handleGridKeyDown);
    document.addEventListener('keyup', handleGridKeyUp);
}

function handleGridKeyDown(e) {
    // Ignore if typing in input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    if (e.key.toLowerCase() === 'f') {
        isFKeyPressed = true;
    }
}

function handleGridKeyUp(e) {
    // Ignore if typing in input/textarea
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
    }
    if (e.key.toLowerCase() === 'f') {
        isFKeyPressed = false;
    }
}
