// Removed: import { shell } from 'electron';
// Removed: import path from 'path';
import {
    getState,
    updateState,
    getCurrentState,
    setGridConfig, // Added
    setAllClassifications, // Added
    CATEGORIES,
    CLASSIFICATIONS
} from './state.js';
// Updated import: loadOrInitializeConfiguration handles both loading and init prompt trigger
import { promptForDeploymentFolder, loadImageList, saveClassifications, loadOrInitializeConfiguration } from './file-system.js';
import { showNotification, validateUsername } from './utils.js';
// Import functions from other modules that ui.js will call
import { loadImageByIndex, findNextUnclassified, updateImageColorMode } from './image-grid.js';
import { confirmImage, copyFromPrevious, resetImage } from './classification.js'; // Assuming these will be in classification.js
import { toggleNotesDialog } from './notes.js'; // Assuming this will be in notes.js

// --- DOM Element References ---
let progressBar = null;
let currentImageSpan = null;
let totalImagesSpan = null;
let progressPercent = null;
let deploymentIdElement = null;
let usernameInputElement = null;
let imageContainerElement = null;
let welcomeMessageElement = null;
let prevButton = null;
let nextButton = null;
let nextUnclassifiedButton = null;
let confirmButton = null;
let copyButton = null;
let resetButton = null;
let colorToggleButton = null;
let notesButton = null;
let nightButton = null;
let documentationButton = null;
// Add references for grid resolution dialog elements
let gridResolutionDialog = null;
let gridResolutionForm = null;
let gridRowsInput = null;
// Note: Buttons are referenced within the prompt function's scope

// --- Initialization ---

export function initializeUI() {
    // Cache DOM elements
    progressBar = document.getElementById('progress-bar');
    currentImageSpan = document.getElementById('current-image');
    totalImagesSpan = document.getElementById('total-images');
    progressPercent = document.getElementById('progress-percent');
    deploymentIdElement = document.getElementById('deployment-id');
    usernameInputElement = document.getElementById('username-input');
    imageContainerElement = document.getElementById('image-container');
    welcomeMessageElement = document.getElementById('welcome-message');
    prevButton = document.getElementById('prev-image');
    nextButton = document.getElementById('next-image');
    nextUnclassifiedButton = document.getElementById('next-unclassified');
    confirmButton = document.getElementById('confirm-image');
    copyButton = document.getElementById('copy-previous');
    resetButton = document.getElementById('reset-image');
    colorToggleButton = document.getElementById('color-toggle');
    notesButton = document.getElementById('notes-button');
    nightButton = document.getElementById('night-button');
    documentationButton = document.getElementById('documentation-button');
    // Cache grid resolution dialog elements
    gridResolutionDialog = document.getElementById('grid-resolution-dialog');
    gridResolutionForm = document.getElementById('grid-resolution-form');
    gridRowsInput = document.getElementById('grid-rows-input');
    // Buttons are handled within the prompt function

    // Initialize username from localStorage
    usernameInputElement.value = localStorage.getItem('monarchUsername') || '';
    usernameInputElement.addEventListener('input', () => {
        localStorage.setItem('monarchUsername', usernameInputElement.value.trim());
        // Re-validate if confirming image requires username
    });

    // Set initial state for buttons etc.
    updateNavigationButtons();
    updateProgress();
    updateColorToggleButton();
    updateActiveCategoryButton();
    initializeKeyboardShortcutsHelp(); // Setup the shortcuts display

    // Setup general event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Folder selection
    document.getElementById('deployment-section').addEventListener('click', handleFolderSelection);

    // Classification tool buttons
    document.querySelectorAll('.count-btn').forEach(button => {
        button.addEventListener('click', () => handleCategoryButtonClick(button));
    });

    // Navigation buttons
    prevButton.addEventListener('click', () => navigateImageHandler('previous'));
    nextButton.addEventListener('click', () => navigateImageHandler('next'));
    nextUnclassifiedButton.addEventListener('click', findNextUnclassifiedHandler);

    // Action buttons
    confirmButton.addEventListener('click', confirmImageHandler);
    copyButton.addEventListener('click', copyFromPreviousHandler);
    resetButton.addEventListener('click', resetImageHandler);
    nightButton.addEventListener('click', nightButtonHandler); // Add listener for night button
    colorToggleButton.addEventListener('click', toggleColorModeHandler);
    notesButton.addEventListener('click', toggleNotesDialog); // Directly call from notes module

    // Documentation button
    documentationButton.addEventListener('click', openDocumentation);

    // Help toggle
    document.querySelector('.shortcuts-header').addEventListener('click', toggleShortcutsHelp);
}

// --- Event Handlers ---

async function handleFolderSelection(event) {
    event.preventDefault();
    event.stopPropagation();

    const folderPath = await promptForDeploymentFolder();
    if (!folderPath) return; // User cancelled or error occurred

    // Hide welcome message
    if (welcomeMessageElement) {
        welcomeMessageElement.style.display = 'none';
    }
    // Clear previous image/grid if any
    clearImageContainer();

    // Assume the selected folder is the deployment folder containing configurations.json
    // and potentially an 'images' subfolder (or images are directly inside).
    // For now, assume images are directly in the selected folder.
    // TODO: Clarify if images are always in a subfolder named 'images'. If so, adjust path logic.
    const deploymentFolder = folderPath;
    const imagesFolder = folderPath; // Assuming images are directly in the deployment folder for now

    updateState({ deploymentFolder: deploymentFolder, imagesFolder: imagesFolder }); // Set both
    deploymentIdElement.textContent = await window.electronAPI.getPathBasename(deploymentFolder);

    // --- Core Loading Sequence ---
    // 1. Load or Initialize Configuration (This might prompt the user)
    const configLoaded = await loadOrInitializeConfiguration(deploymentFolder, imagesFolder);

    if (configLoaded) {
        // 2. If config succeeded, THEN load the image list
        const loadedImageFiles = await loadImageList(imagesFolder);
        updateState({ imageFiles: loadedImageFiles, currentImageIndex: -1 }); // Update state with actual images

        if (loadedImageFiles.length > 0) {
            // 3. If images exist, load the first unclassified one
            // Grid config should be set by loadOrInitializeConfiguration at this point
            if (getState().currentGridConfig.rows && getState().currentGridConfig.columns) {
                await findNextUnclassifiedHandler(); // Load the first unclassified image
            } else {
                console.error("Configuration loaded/created, but grid config not set in state.");
                showNotification("Error: Grid configuration missing after load/init.", "error");
                handleNoImagesFound(); // Reset UI
            }
        } else {
            // Config loaded/created, but no images found in the folder
            handleNoImagesFound();
        }
    } else {
        // Handle configuration loading/creation failure or cancellation by user
        handleNoImagesFound(); // Reset UI as if no folder was loaded
        deploymentIdElement.textContent = 'Click to select folder'; // Reset folder display
        // Ensure state is fully reset
        updateState({
            deploymentFolder: null, // Reset deployment folder
            imagesFolder: null,
            imageFiles: [],
            currentImageIndex: -1,
            classifications: {},
            classificationFile: null, // Also reset file path
            currentGridConfig: { rows: null, columns: null }
        });
    }

    updateProgress(); // Update progress after loading attempt
}

function handleCategoryButtonClick(button) {
    const selectedTool = button.dataset.count;
    updateState({ selectedTool });
    updateActiveCategoryButton();
}


// --- Grid Resolution Prompt ---

/**
 * Displays a modal dialog to get the desired grid rows from the user.
 * Calculates columns based on a fixed 16:9 aspect ratio, updates state,
 * and saves the initial configurations.json.
 * @returns {Promise<boolean>} - True if configuration was successfully created, false on cancel/error.
 */
export function promptForGridResolution() { // Removed initialImageDimensions parameter
    return new Promise((resolve) => {
        if (!gridResolutionDialog || !gridResolutionForm || !gridRowsInput) {
            console.error('Grid resolution dialog elements not found.');
            return resolve(false); // Cannot proceed
        }

        // Removed unused confirmButton declaration
        const cancelButton = gridResolutionDialog.querySelector('#cancel-grid-resolution');

        // --- Event Handlers for the Dialog ---
        const handleConfirm = async (event) => {
            event.preventDefault(); // Prevent default form submission
            const userRows = parseInt(gridRowsInput.value, 10);

            // Validation
            if (isNaN(userRows) || userRows < 1) {
                showNotification('Please enter a valid number of rows (1 or more).', 'warning');
                return;
            }

            // Calculate columns using fixed 16:9 aspect ratio
            const aspectRatio = 16 / 9;
            const calculatedColumns = Math.max(1, Math.round(userRows * aspectRatio));

            console.log(`Calculated grid (16:9 ratio): ${userRows} rows, ${calculatedColumns} columns`);

            // Update state
            setGridConfig(userRows, calculatedColumns);
            setAllClassifications({}); // Initialize classifications as empty

            // Create and save the initial configurations.json file
            const configFilePath = getState().classificationFile; // Get path set by loadOrInitializeConfiguration
            if (!configFilePath) {
                console.error("Configuration file path not set in state before saving.");
                showNotification("Error: Cannot determine where to save configuration.", "error");
                cleanupAndResolve(false); // Indicate failure
                return;
            }

            const dataToSave = {
                rows: userRows,
                columns: calculatedColumns,
                classifications: {} // Start with empty classifications
            };

            try {
                const result = await window.electronAPI.writeFile(
                    configFilePath,
                    JSON.stringify(dataToSave, null, 2)
                );
                if (!result || !result.success) {
                    throw new Error(result?.error || 'Unknown error writing configuration file');
                }
                console.log('Initial configurations.json saved successfully.');
                cleanupAndResolve(true); // Indicate success
            } catch (error) {
                console.error('Error saving initial configuration:', error);
                showNotification(`Failed to save configuration file: ${error.message}`, 'error');
                cleanupAndResolve(false); // Indicate failure
            }
        };

        const handleCancel = () => {
            console.log('Grid resolution cancelled by user.');
            cleanupAndResolve(false); // Indicate cancellation
        };

        const cleanupAndResolve = (success) => {
            gridResolutionForm.removeEventListener('submit', handleConfirm);
            cancelButton.removeEventListener('click', handleCancel);
            gridResolutionDialog.close();
            resolve(success);
        };

        // --- Attach Listeners and Show Dialog ---
        gridResolutionForm.addEventListener('submit', handleConfirm);
        cancelButton.addEventListener('click', handleCancel);

        // Reset input to default just before showing
        gridRowsInput.value = '9';
        gridResolutionDialog.showModal();
    });
}


// --- Original Event Handlers (navigate, findNext, confirm, copy, reset, etc.) ---
// (Keep the existing handlers below this new section)

export function navigateImageHandler(direction) { // Add export
    const state = getCurrentState();
    let newIndex = state.currentImageIndex;

    if (direction === 'next' && state.currentImageIndex < state.imageFiles.length - 1) {
        newIndex++;
    } else if (direction === 'previous' && state.currentImageIndex > 0) {
        newIndex--;
    }

    if (newIndex !== state.currentImageIndex) {
        loadImageByIndex(newIndex); // Call function assumed to be in image-grid.js
    }
}

export async function findNextUnclassifiedHandler() { // Add export
    await findNextUnclassified(); // Call function assumed to be in image-grid.js
}

export function confirmImageHandler() { // Add export
    if (!validateUsername()) return;
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    if (!currentImageFile) return;

    const user = usernameInputElement.value.trim();
    // Call confirmImage from classification.js, passing false for markAsNight
    confirmImage(currentImageFile, user, false);
    saveClassifications(getState().classifications); // Save changes
    // Reload the image display to update the visual status (confirmed/unlocked)
    loadImageByIndex(state.currentImageIndex);
    // No need to call updateConfirmButtonState or updateProgress here, 
    // as loadImageByIndex will trigger them.
}

export function copyFromPreviousHandler() { // Add export
    const state = getCurrentState();
    if (state.currentImageIndex <= 0) {
        showNotification('No previous image available', 'error');
        return;
    }
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    const previousImageFile = state.imageFiles[state.currentImageIndex - 1];
    // Call copyFromPrevious from classification.js
    const success = copyFromPrevious(currentImageFile, previousImageFile);
    if (success) {
        // Reloading the grid/image display will be handled by loadImageByIndex or similar
        loadImageByIndex(state.currentImageIndex); // Reload current image to show copied classifications
        saveClassifications(getState().classifications); // Save changes
    }
    return success; // Return success status for the night button handler
}

export function resetImageHandler() { // Add export
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    if (!currentImageFile) return;

    // Call resetImage from classification.js
    const success = resetImage(currentImageFile);
    if (success) {
        loadImageByIndex(state.currentImageIndex); // Reload current image
        saveClassifications(getState().classifications); // Save changes
    }
}

// --- Night Button Handler ---
async function nightButtonHandler() {
    if (!validateUsername()) return;
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    if (!currentImageFile) return;

    // 1. Attempt to copy from previous
    const copySuccess = copyFromPreviousHandler(); // This now returns true/false
    if (!copySuccess) {
        // Error notification handled within copyFromPreviousHandler or copyFromPrevious
        return;
    }

    // 2. Confirm the image, marking it as night
    const user = usernameInputElement.value.trim();
    // Directly call confirmImage from classification.js, setting markAsNight to true
    confirmImage(currentImageFile, user, true);
    saveClassifications(getState().classifications); // Save after confirm

    // 3. Navigate to the next image (don't reload current, just navigate)
    // Use a slight delay to allow the user to see the confirmation briefly if needed,
    // or navigate immediately. Let's navigate immediately for speed.
    navigateImageHandler('next');

    // Optional: Add a specific notification for the night action sequence
    // showNotification('Night image processed.', 'success'); 
    // Note: confirmImage already shows a notification, might be redundant.
}


function toggleColorModeHandler() {
    const state = getCurrentState();
    updateState({ isColorMode: !state.isColorMode });
    updateImageColorMode(); // Assumed in image-grid.js
    updateColorToggleButton();
}

async function openDocumentation() {
    // Use preload function to open external link
    const result = await window.electronAPI.openExternalLink('https://kylenessen.github.io/monarch_trailcam_classifier/');
    if (!result || !result.success) {
        showNotification('Failed to open documentation', 'error');
        console.error('Error opening external link:', result?.error);
    }
}

// --- UI Update Functions ---

export function updateProgress() {
    const state = getCurrentState();
    if (!progressBar || !currentImageSpan || !totalImagesSpan || !progressPercent) return; // Ensure elements are cached

    const total = state.imageFiles.length;
    const current = total === 0 ? 0 : state.currentImageIndex + 1;

    const classifiedCount = Object.values(state.classifications).filter(c => c && c.confirmed === true).length;

    currentImageSpan.textContent = current;
    totalImagesSpan.textContent = total;

    const progress = total === 0 ? 0 : (classifiedCount / total) * 100;
    const roundedProgress = Math.round(progress);

    progressBar.style.width = `${progress}%`;
    progressPercent.textContent = `${roundedProgress}%`;
}

export function updateNavigationButtons() {
    const state = getCurrentState();
    if (!prevButton || !nextButton) return; // Ensure elements are cached

    prevButton.disabled = state.currentImageIndex <= 0;
    nextButton.disabled = state.currentImageIndex >= state.imageFiles.length - 1;
    // nextUnclassifiedButton state might depend on whether all are classified
}

export function disableClassificationTools(disabled) {
    // Disable/enable count buttons
    document.querySelectorAll('.count-btn').forEach(btn => {
        btn.disabled = disabled;
    });
    // Disable/enable action buttons that modify classifications
    if (copyButton) copyButton.disabled = disabled;
    if (resetButton) resetButton.disabled = disabled;

    updateState({ isLocked: disabled }); // Update global lock state
}

export function updateConfirmButtonState(imageFile) {
    if (!confirmButton) return; // Ensure element is cached

    const classification = getState().classifications[imageFile];
    const isConfirmed = classification?.confirmed || false;

    confirmButton.textContent = isConfirmed ? 'Unlock Image' : 'Confirm Image';
    // Potentially change button style as well
}

function updateActiveCategoryButton() {
    const state = getCurrentState();
    document.querySelectorAll('.count-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.count === state.selectedTool);
    });
}

function updateColorToggleButton() {
    if (!colorToggleButton) return; // Ensure element is cached
    const state = getCurrentState();
    colorToggleButton.textContent = state.isColorMode ? 'Switch to B&W' : 'Switch to Color';
}

export function updateNotesButtonState() {
    if (!notesButton) return; // Ensure element is cached
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    const hasNotes = currentImageFile &&
        state.classifications[currentImageFile]?.notes &&
        state.classifications[currentImageFile].notes.trim() !== '';
    notesButton.classList.toggle('has-notes', hasNotes);
}

export function handleNoImagesFound() {
    showNotification('No images found in selected folder', 'error');
    if (deploymentIdElement) {
        deploymentIdElement.textContent = 'Click to select folder';
    }
    clearImageContainer();
    if (imageContainerElement) {
        imageContainerElement.innerHTML = `
            <div id="welcome-message">
                <h2>Welcome to Monarch Photo Classification</h2>
                <p>Select an image folder to begin</p>
            </div>
        `;
        welcomeMessageElement = document.getElementById('welcome-message'); // Re-cache if recreated
    }
    updateProgress(); // Reset progress
    updateNavigationButtons(); // Disable nav buttons
}

export function clearImageContainer() {
    if (imageContainerElement) {
        // Remove grid, image, etc.
        while (imageContainerElement.firstChild) {
            imageContainerElement.removeChild(imageContainerElement.firstChild);
        }
    }
    // Disconnect observer if it exists
    const observer = getState().resizeObserver;
    if (observer) {
        observer.disconnect();
        updateState({ resizeObserver: null });
    }
}

// --- Keyboard Shortcuts Help ---

function initializeKeyboardShortcutsHelp() {
    const shortcuts = [
        { key: 'D / →', action: 'Next image' },
        { key: 'A / ←', action: 'Previous image' },
        { key: 'E', action: 'Next category' },
        { key: 'Q', action: 'Previous category' },
        { key: 'W / ↑', action: 'Confirm/Unlock image' },
        { key: 'S / ↓', action: 'Copy from previous' },
        { key: 'N', action: 'Toggle notes' },
        { key: 'Hold F + Click', action: 'Toggle sunlight for cell' },
        { key: 'Hold ⌘/Ctrl + Click', action: 'Set count for cell' },
        { key: 'Hold ⌘/Ctrl + Right Click', action: 'Set cell to 0' },
        { key: 'Space', action: 'Hold to zoom (300%)' },
        { key: 'H', action: 'Toggle shortcuts help' }
    ];

    const shortcutsList = document.querySelector('.shortcuts-list');
    if (!shortcutsList) return; // Element might not exist yet if called too early

    shortcutsList.innerHTML = ''; // Clear existing items if any
    shortcuts.forEach(({ key, action }) => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="shortcut-key">${key}</span> ${action}`;
        shortcutsList.appendChild(li);
    });
}

export function toggleShortcutsHelp() { // Add export
    const helpContainer = document.querySelector('.keyboard-shortcuts-help');
    const indicator = document.querySelector('.shortcuts-header .collapse-indicator'); // More specific selector
    if (helpContainer) {
        helpContainer.classList.toggle('collapsed');
        if (indicator) {
            indicator.textContent = helpContainer.classList.contains('collapsed') ? '+' : '−';
        }
    }
}

// --- Category Cycling ---
// Already exported, no change needed here.
export function cycleCategory(direction) {
    const state = getCurrentState();
    const currentIndex = CATEGORIES.indexOf(state.selectedTool);
    if (currentIndex === -1) return; // Should not happen

    let newIndex;
    if (direction === 'next') {
        newIndex = (currentIndex + 1) % CATEGORIES.length;
    } else { // 'previous'
        newIndex = (currentIndex - 1 + CATEGORIES.length) % CATEGORIES.length;
    }

    updateState({ selectedTool: CATEGORIES[newIndex] });
    updateActiveCategoryButton();
}
