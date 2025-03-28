// Removed: import { shell } from 'electron';
// Removed: import path from 'path';
import { 
    getState, 
    updateState, 
    getCurrentState, 
    CATEGORIES, 
    CLASSIFICATIONS 
} from './state.js';
import { promptForDeploymentFolder, loadImageList, saveClassifications, loadClassifications, initializeClassificationsIfNeeded } from './file-system.js';
import { showNotification, validateUsername } from './utils.js';
// Import functions from other modules that ui.js will call
import { loadImageByIndex, findNextUnclassified, updateImageColorMode } from './image-grid.js'; // Assuming these will be in image-grid.js
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
let documentationButton = null;

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
    documentationButton = document.getElementById('documentation-button');

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

    updateState({ imagesFolder: folderPath });
    // Use preload function to get basename
    deploymentIdElement.textContent = await window.electronAPI.getPathBasename(folderPath); 

    const imageFiles = await loadImageList(folderPath);
    updateState({ imageFiles: imageFiles, currentImageIndex: -1 }); // Reset index

    if (imageFiles.length > 0) {
        const classificationsLoaded = await loadClassifications(folderPath);
        if (!classificationsLoaded) {
            initializeClassificationsIfNeeded(imageFiles);
        }
        await findNextUnclassifiedHandler(); // Load the first unclassified image
    } else {
        handleNoImagesFound(); // Update UI for no images
    }
    updateProgress(); // Update progress after loading
}

function handleCategoryButtonClick(button) {
    const selectedTool = button.dataset.count;
    updateState({ selectedTool });
    updateActiveCategoryButton();
}

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
    confirmImage(currentImageFile, user); // Call function assumed to be in classification.js
    updateConfirmButtonState(currentImageFile); // Update button text/state
    updateProgress(); // Progress depends on confirmed count
    saveClassifications(getState().classifications); // Save changes
}

export function copyFromPreviousHandler() { // Add export
    const state = getCurrentState();
    if (state.currentImageIndex <= 0) {
        showNotification('No previous image available', 'error');
        return;
    }
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    const previousImageFile = state.imageFiles[state.currentImageIndex - 1];
    
    copyFromPrevious(currentImageFile, previousImageFile); // Call function assumed to be in classification.js
    // Reloading the grid/image display will be handled by loadImageByIndex or similar
    loadImageByIndex(state.currentImageIndex); // Reload current image to show copied classifications
    saveClassifications(getState().classifications); // Save changes
}

export function resetImageHandler() { // Add export
    const state = getCurrentState();
    const currentImageFile = state.imageFiles[state.currentImageIndex];
    if (!currentImageFile) return;

    resetImage(currentImageFile); // Call function assumed to be in classification.js
    loadImageByIndex(state.currentImageIndex); // Reload current image
    saveClassifications(getState().classifications); // Save changes
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
