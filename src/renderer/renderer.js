// Global variables
let currentImage = null;
let gridCells = [];
let currentClassification = {};

// Progress bar elements
let progressBar = null;
let currentImageSpan = null;
let totalImagesSpan = null;
let progressPercent = null;

// Global state
let currentState = {
    deploymentFolder: null,
    imagesFolder: null,
    imageFiles: [],
    currentImageIndex: -1,
    classifications: {},
    selectedCell: null,
    selectedTool: '0',
    classificationFile: null,
    originalImageWidth: null,
    originalImageHeight: null,
    resizeObserver: null,
    isLocked: false,
    isColorMode: false  // Default to black and white
};

const { ipcRenderer } = require('electron');
const path = require('path');
const fs = require('fs');

// Classification categories and their colors
const CLASSIFICATIONS = {
    '0': { label: '0', color: 'transparent' },
    '1-9': { label: '1-9', color: 'rgba(255, 235, 59, 0.3)' },
    '10-99': { label: '10-99', color: 'rgba(255, 152, 0, 0.3)' },
    '100-999': { label: '100-999', color: 'rgba(244, 67, 54, 0.3)' },
    '1000+': { label: '1000+', color: 'rgba(156, 39, 176, 0.3)' }
};

// Grid configuration
const GRID_CONFIG = {
    columns: 16,
    rows: 9
};

// Define the category order for cycling
const CATEGORIES = ['0', '1-9', '10-99', '100-999', '1000+'];

// Default classification for each cell
const DEFAULT_CELL_CLASSIFICATION = {
    count: '0',
    directSun: false
};

// Initialize classifications for all images
function initializeClassifications() {
    console.log('Initializing classifications for images:', currentState.imageFiles);
    const defaultClassifications = {};
    
    // Create default grid cells with count of 0
    const gridCells = {};
    for (let row = 0; row < GRID_CONFIG.rows; row++) {
        for (let col = 0; col < GRID_CONFIG.columns; col++) {
            const cellId = generateCellId(row, col);
            gridCells[cellId] = {
                count: 0,
                directSun: false
            };
        }
    }
    
    // Initialize each image with default classifications
    currentState.imageFiles.forEach((image, index) => {
        defaultClassifications[image] = {
            confirmed: false,
            cells: { ...gridCells },
            index: index
        };
    });
    
    console.log('Created default classifications:', defaultClassifications);
    
    // Set the classifications and save to file
    currentState.classifications = defaultClassifications;
    saveClassifications();
}

function canEditImage(imageFile) {
    // If the current image is confirmed, prevent edits
    if (currentState.classifications[imageFile].confirmed) {
        showNotification('This image is confirmed. Unconfirm it first to make changes.', 'error');
        return false;
    }

    const currentIndex = currentState.classifications[imageFile].index;
    
    // Check if all previous images are confirmed
    for (let i = 0; i < currentIndex; i++) {
        const prevImage = currentState.imageFiles[i];
        if (!currentState.classifications[prevImage].confirmed) {
            return false;
        }
    }
    return true;
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeUI();
    setupEventListeners();
    initializeProgressBar();
});

// Initialize progress bar elements
function initializeProgressBar() {
    progressBar = document.getElementById('progress-bar');
    currentImageSpan = document.getElementById('current-image');
    totalImagesSpan = document.getElementById('total-images');
    progressPercent = document.getElementById('progress-percent');
}

// Update progress bar
function updateProgress() {
    if (!currentState.imageFiles.length) {
        currentImageSpan.textContent = '0';
        totalImagesSpan.textContent = '0';
        progressBar.style.width = '0%';
        progressPercent.textContent = '0%';
        return;
    }

    const total = currentState.imageFiles.length;
    const current = currentState.currentImageIndex + 1;
    
    // Count only images that have been confirmed
    const classified = Object.values(currentState.classifications).filter(classification => 
        classification && classification.confirmed === true
    ).length;
    
    currentImageSpan.textContent = current;
    totalImagesSpan.textContent = total;
    
    const progress = (classified / total) * 100;
    const roundedProgress = Math.round(progress);
    progressBar.style.width = `${progress}%`;
    progressPercent.textContent = `${roundedProgress}%`;
}

function setupEventListeners() {
    // Add keyboard event listener
    document.addEventListener('keydown', handleKeyboardShortcuts);

    // Classification buttons
    document.querySelectorAll('.count-btn').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            document.querySelectorAll('.count-btn').forEach(btn => 
                btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            currentState.selectedTool = button.dataset.count;
            
            // No longer automatically apply to selected cell
        });
    });

    // Sunlight toggle
    document.getElementById('sunlight-toggle').addEventListener('click', (event) => {
        event.target.classList.toggle('active');
        
        // No longer automatically apply to selected cell
    });

    // Navigation buttons
    document.getElementById('prev-image').addEventListener('click', () => {
        navigateImage('previous');
    });

    document.getElementById('next-image').addEventListener('click', () => {
        navigateImage('next');
    });

    document.getElementById('next-unclassified').addEventListener('click', () => {
        findNextUnclassified();
    });

    // Confirm Image button
    document.getElementById('confirm-image').addEventListener('click', () => {
        confirmImage();
    });

    // Copy from Previous button
    document.getElementById('copy-previous').addEventListener('click', () => {
        copyFromPrevious();
    });

    // Reset button
    document.getElementById('reset-image').addEventListener('click', resetImage);

    // Add folder selection handler
    document.getElementById('deployment-section').addEventListener('click', async (event) => {
        event.preventDefault();
        event.stopPropagation();
        await promptForDeploymentFolder();
    });

    // Color toggle button
    document.getElementById('color-toggle').addEventListener('click', () => {
        currentState.isColorMode = !currentState.isColorMode;
        updateImageColorMode();
        const button = document.getElementById('color-toggle');
        button.textContent = currentState.isColorMode ? 'Switch to B&W' : 'Switch to Color';
    });

    // Other actions
}

async function promptForDeploymentFolder() {
    try {
        console.log('Starting folder selection...');
        const result = await ipcRenderer.invoke('select-folder');
        console.log('Folder selection result:', result);
        
        if (result.success) {
            console.log('Successfully selected folder:', result.folderPath);
            
            // Clear the image container first
            const imageContainer = document.getElementById('image-container');
            const welcomeMessage = document.getElementById('welcome-message');
            
            // Safely hide welcome message if it exists
            if (welcomeMessage) {
                welcomeMessage.style.display = 'none';
            }
            
            // Clear current state if we had a previous folder
            if (currentState.imagesFolder) {
                console.log('Clearing previous folder state...');
                // Reset all state variables
                currentState.imageFiles = [];
                currentState.currentImageIndex = -1;
                currentState.classifications = {};
                currentState.selectedCell = null;
                currentState.selectedTool = '0';
                currentState.classificationFile = null;
                currentState.originalImageWidth = null;
                currentState.originalImageHeight = null;
                currentState.isLocked = false;
                
                // Clear the image container
                while (imageContainer && imageContainer.firstChild) {
                    imageContainer.removeChild(imageContainer.firstChild);
                }
                
                // Reset grid cells
                gridCells = [];
                currentImage = null;
                currentClassification = {};
                console.log('State cleared successfully');
            }
            
            // Store the selected folder path
            currentState.imagesFolder = result.folderPath;
            console.log('Set new folder path:', currentState.imagesFolder);
            
            try {
                console.log('Loading images from folder...');
                const imageFiles = await ipcRenderer.invoke('load-images', result.folderPath);
                console.log('Loaded image files:', imageFiles);
                
                if (imageFiles && imageFiles.length > 0) {
                    currentState.imageFiles = imageFiles;
                    console.log('Updated image files in state');
                    
                    // Update UI with deployment info
                    const deploymentId = document.getElementById('deployment-id');
                    if (deploymentId) {
                        deploymentId.textContent = path.basename(result.folderPath);
                    }
                    
                    try {
                        console.log('Loading classifications...');
                        await loadClassifications();
                        console.log('Classifications loaded');
                        
                        console.log('Finding next unclassified image...');
                        await findNextUnclassified();
                        console.log('Found and loaded next unclassified image');
                    } catch (error) {
                        console.error('Error in classification/image loading:', error);
                        throw error;
                    }
                } else {
                    console.log('No images found in folder');
                    showNotification('No images found in selected folder', 'error');
                    
                    if (deploymentId) {
                        deploymentId.textContent = 'Click to select folder';
                    }
                    
                    // Show welcome message again if no images found
                    if (imageContainer) {
                        imageContainer.innerHTML = `
                            <div id="welcome-message">
                                <h2>Welcome to Monarch Photo Classification</h2>
                                <p>Select an image folder to begin</p>
                            </div>
                        `;
                    }
                }
            } catch (error) {
                console.error('Error loading images:', error);
                throw error;
            }
            
            // Update progress indicators
            updateProgress();
            console.log('Progress updated');
        } else {
            console.log('Folder selection was cancelled or failed');
            if (result.error) {
                console.error('Folder selection error:', result.error);
            }
        }
    } catch (error) {
        console.error('Error in promptForDeploymentFolder:', error);
        showNotification(`Error switching folders: ${error.message}`, 'error');
    }
}

function getImageClassifications(imageName) {
    return currentState.classifications[imageName] || {};
}

function setClassification(imageName, cellId, classification) {
    console.log('Setting classification for', imageName, cellId, classification);
    
    // Initialize the image entry if it doesn't exist
    if (!currentState.classifications[imageName]) {
        currentState.classifications[imageName] = {
            confirmed: false,
            cells: {},
            index: currentState.imageFiles.indexOf(imageName)
        };
    }
    
    // Initialize the cells object if it doesn't exist
    if (!currentState.classifications[imageName].cells) {
        currentState.classifications[imageName].cells = {};
    }
    
    // Update the cell classification
    currentState.classifications[imageName].cells[cellId] = classification;
    
    console.log('Updated classifications:', currentState.classifications[imageName]);
    saveClassifications();
    updateProgress();
}

async function loadImageByIndex(index) {
    console.log('Loading image at index:', index);
    console.log('Current state:', {
        imagesFolder: currentState.imagesFolder,
        totalImages: currentState.imageFiles.length,
        currentIndex: currentState.currentImageIndex
    });

    if (index < 0 || index >= currentState.imageFiles.length) {
        console.error('Invalid image index');
        return;
    }

    const imagePath = path.join(currentState.imagesFolder, currentState.imageFiles[index]);
    console.log('Full image path:', imagePath);
    
    const imageData = await ipcRenderer.invoke('get-image-data', imagePath);
    console.log('Received image data:', imageData ? 'yes' : 'no');
    
    if (imageData) {
        const currentImage = currentState.imageFiles[index];
        console.log('Loading image:', currentImage);
        
        // Only disable tools if the image is confirmed
        disableClassificationTools(currentState.classifications[currentImage].confirmed);
        
        const imageContainer = document.getElementById('image-container');
        
        // Clear existing content
        imageContainer.innerHTML = '';
        
        // Create wrapper for image and grid
        const wrapper = document.createElement('div');
        wrapper.className = 'image-wrapper';
        imageContainer.appendChild(wrapper);
        
        // Create and load new image
        const img = new Image();
        img.id = 'display-image';
        
        // Set up image load handler before setting src
        img.onload = () => {
            // Store original dimensions
            currentState.originalImageWidth = img.naturalWidth;
            currentState.originalImageHeight = img.naturalHeight;
            
            // Apply current color mode
            updateImageColorMode();
            
            // Create grid after image loads
            createGrid(wrapper, img.naturalWidth, img.naturalHeight);
            
            // Set up resize observer
            if (currentState.resizeObserver) {
                currentState.resizeObserver.disconnect();
            }
            setupResizeObserver(wrapper, img);
            
            // Update navigation buttons
            updateNavigationButtons();
            updateProgress();
        };
        
        // Add error handler
        img.onerror = () => {
            console.error('Failed to load image:', imagePath);
            imageContainer.innerHTML = '<div class="error-message">Failed to load image</div>';
        };
        
        // Set image source and append to wrapper
        img.src = `data:image/jpeg;base64,${imageData}`;
        wrapper.appendChild(img);
        
        // Update state and navigation
        currentState.currentImageIndex = index;
    }
    updateProgress();
}

function setupResizeObserver(wrapper, img) {
    if (currentState.resizeObserver) {
        currentState.resizeObserver.disconnect();
    }

    currentState.resizeObserver = new ResizeObserver((entries) => {
        // Only used for monitoring, no active resizing needed
    });

    currentState.resizeObserver.observe(wrapper);
}

function createGrid(wrapper, imageWidth, imageHeight) {
    // Remove existing grid if it exists
    const existingGrid = wrapper.querySelector('.grid-overlay');
    if (existingGrid) {
        wrapper.removeChild(existingGrid);
    }

    const gridOverlay = document.createElement('div');
    gridOverlay.className = 'grid-overlay';
    
    // Calculate cell dimensions based on image size and grid configuration
    const cellWidth = imageWidth / GRID_CONFIG.columns;
    const cellHeight = imageHeight / GRID_CONFIG.rows;
    
    // Get classifications for current image
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    const imageClassifications = getImageClassifications(currentImage);
    
    // Create grid cells
    for (let row = 0; row < GRID_CONFIG.rows; row++) {
        for (let col = 0; col < GRID_CONFIG.columns; col++) {
            const cellId = generateCellId(row, col);
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.row = row;
            cell.dataset.col = col;
            cell.dataset.cellId = cellId;
            
            // Set cell dimensions as percentages
            cell.style.width = `${(1 / GRID_CONFIG.columns) * 100}%`;
            cell.style.height = `${(1 / GRID_CONFIG.rows) * 100}%`;
            cell.style.left = `${(col / GRID_CONFIG.columns) * 100}%`;
            cell.style.top = `${(row / GRID_CONFIG.rows) * 100}%`;
            
            // Apply existing classifications
            const cellClassification = imageClassifications.cells[cellId];
            if (cellClassification) {
                applyCellStyle(cell, cellClassification);
            }
            
            // Add click handler
            cell.addEventListener('click', (e) => handleCellClick(e, cellId));
            
            gridOverlay.appendChild(cell);
        }
    }
    
    wrapper.appendChild(gridOverlay);
}

function updateNavigationButtons() {
    const prevButton = document.getElementById('prev-image');
    const nextButton = document.getElementById('next-image');
    
    prevButton.disabled = currentState.currentImageIndex <= 0;
    nextButton.disabled = currentState.currentImageIndex >= currentState.imageFiles.length - 1;
}

function handleCellClick(event, cellId) {
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    
    // Check if we can edit this image
    if (!canEditImage(currentImage)) {
        showNotification('Please confirm all previous images before making annotations', 'error');
        return;
    }
    
    // Don't allow modifications if image is locked or confirmed
    if (currentState.isLocked || currentState.classifications[currentImage].confirmed) {
        return;
    }
    
    // Remove previous selection
    if (currentState.selectedCell) {
        document.querySelector(`[data-cell-id="${currentState.selectedCell}"]`)
            ?.classList.remove('selected');
    }
    
    const cell = event.target;
    cell.classList.add('selected');
    currentState.selectedCell = cellId;
    
    // Apply current classification immediately
    applyCurrentClassification(cell, cellId);
}

function applyCurrentClassification(cell, cellId) {
    const classification = {
        count: currentState.selectedTool,
        directSun: document.getElementById('sunlight-toggle').classList.contains('active')
    };
    
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    setClassification(currentImage, cellId, classification);
    applyCellStyle(cell, classification);
}

function applyCellStyle(cell, classification) {
    // Apply count classification
    const countClass = CLASSIFICATIONS[classification.count];
    cell.style.backgroundColor = countClass.color;
    
    // Apply sunlight classification
    if (classification.directSun) {
        cell.style.borderColor = 'rgba(255, 235, 59, 0.8)';
        cell.style.borderWidth = '2px';
    } else {
        cell.style.borderColor = 'rgba(255, 255, 255, 0.5)';
        cell.style.borderWidth = '1px';
    }
}

function initializeUI() {
    // TODO: Implement initial UI setup
    // - Create grid overlay
    // - Load first image
    // - Set up classification tools
}

function cycleCategory(direction) {
    const currentIndex = CATEGORIES.indexOf(currentState.selectedTool);
    if (currentIndex === -1) return;

    let newIndex;
    if (direction === 'next') {
        newIndex = (currentIndex + 1) % CATEGORIES.length;
    } else {
        newIndex = (currentIndex - 1 + CATEGORIES.length) % CATEGORIES.length;
    }

    // Update the selected tool
    currentState.selectedTool = CATEGORIES[newIndex];

    // Update UI
    document.querySelectorAll('.count-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.count === currentState.selectedTool) {
            btn.classList.add('active');
        }
    });
}

function navigateImage(direction) {
    if (direction === 'next' && currentState.currentImageIndex < currentState.imageFiles.length - 1) {
        loadImageByIndex(currentState.currentImageIndex + 1);
    } else if (direction === 'previous' && currentState.currentImageIndex > 0) {
        loadImageByIndex(currentState.currentImageIndex - 1);
    }
}

function handleKeyboardShortcuts(event) {
    // Don't handle shortcuts if we're in an input field
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }

    switch (event.key) {
        // Navigation
        case 'ArrowRight':
        case 'd':
        case 'D':
            navigateImage('next');
            break;

        case 'ArrowLeft':
        case 'a':
        case 'A':
            navigateImage('previous');
            break;

        // Category cycling
        case 'e':
        case 'E':
            cycleCategory('next');
            break;

        case 'q':
        case 'Q':
            cycleCategory('previous');
            break;

        // Confirm image
        case 'ArrowUp':
        case 'w':
        case 'W':
            document.getElementById('confirm-image').click();
            break;

        // Copy from previous
        case 'ArrowDown':
        case 's':
        case 'S':
            document.getElementById('copy-previous').click();
            break;

        // Toggle sunlight
        case 'f':
        case 'F':
            document.getElementById('sunlight-toggle').click();
            break;

        // Toggle shortcuts help
        case 'h':
        case 'H':
            toggleShortcutsHelp();
            break;
    }
}

function toggleShortcutsHelp() {
    const helpContainer = document.querySelector('.keyboard-shortcuts-help');
    const indicator = document.querySelector('.collapse-indicator');
    if (helpContainer) {
        helpContainer.classList.toggle('collapsed');
        if (indicator) {
            indicator.innerHTML = helpContainer.classList.contains('collapsed') ? '+' : '−';
        }
    }
}

async function loadClassifications() {
    try {
        // Set up the classifications file path
        currentState.classificationFile = path.join(currentState.imagesFolder, 'classifications.json');
        console.log('Classification file path:', currentState.classificationFile);
        
        // Check if classifications file exists
        if (fs.existsSync(currentState.classificationFile)) {
            console.log('Found existing classifications file');
            const data = await fs.promises.readFile(currentState.classificationFile, 'utf8');
            currentState.classifications = JSON.parse(data);
            console.log('Loaded existing classifications');
        } else {
            console.log('No classifications file found, creating new one');
            initializeClassifications();
        }
    } catch (error) {
        console.error('Error loading classifications:', error);
        currentState.classifications = {};
    }
}

async function saveClassifications() {
    try {
        console.log('Attempting to save to:', currentState.classificationFile);
        console.log('Current classifications:', currentState.classifications);
        
        await fs.promises.writeFile(
            currentState.classificationFile,
            JSON.stringify(currentState.classifications, null, 2)
        );
        console.log('Successfully saved classifications');
    } catch (error) {
        console.error('Error saving classifications:', error);
    }
}

function generateCellId(row, col) {
    return `cell_${row}_${col}`;
}

function disableClassificationTools(disabled) {
    // Disable/enable count buttons
    document.querySelectorAll('.count-btn').forEach(btn => {
        btn.disabled = disabled;
    });
    
    // Disable/enable sunlight toggle
    document.getElementById('sunlight-toggle').disabled = disabled;
    
    // Update current state
    currentState.isLocked = disabled;
}

function confirmImage() {
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    
    if (!currentState.classifications[currentImage]) {
        currentState.classifications[currentImage] = {};
    }
    
    const isConfirmed = currentState.classifications[currentImage].confirmed;
    currentState.classifications[currentImage].confirmed = !isConfirmed;
    
    // Update UI
    const wrapper = document.querySelector('.image-wrapper');
    if (!isConfirmed) {
        wrapper.classList.add('confirmed');
        document.getElementById('confirm-image').textContent = 'Unlock Image';
        disableClassificationTools(true);
    } else {
        wrapper.classList.remove('confirmed');
        document.getElementById('confirm-image').textContent = 'Confirm Image';
        disableClassificationTools(false);
    }
    
    // Save to file
    saveClassifications();
}

function copyFromPrevious() {
    // Check if we have a previous image
    if (currentState.currentImageIndex <= 0) {
        showNotification('No previous image available', 'error');
        return;
    }

    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    
    // Check if we can edit this image
    if (!canEditImage(currentImage)) {
        showNotification('Please unlock image to make edits', 'error');
        return;
    }

    // Get previous image data
    const previousImage = currentState.imageFiles[currentState.currentImageIndex - 1];
    const previousImageData = currentState.classifications[previousImage];

    if (!previousImageData || !previousImageData.confirmed) {
        showNotification('Previous image must be confirmed before copying', 'error');
        return;
    }

    // Copy classifications (excluding the confirmed status and maintaining the index)
    const currentIndex = currentState.classifications[currentImage].index;
    currentState.classifications[currentImage] = {
        ...currentState.classifications[currentImage],
        cells: JSON.parse(JSON.stringify(previousImageData.cells)), // Deep copy to prevent reference issues
        confirmed: false
    };

    // Save to file
    saveClassifications();

    // Reload the grid to show new classifications
    const wrapper = document.querySelector('.image-wrapper');
    const img = document.querySelector('#display-image');
    if (wrapper && img) {
        createGrid(wrapper, img.naturalWidth, img.naturalHeight);
    }

    showNotification('Classifications copied from previous image', 'success');
}

function showNotification(message, type = 'info') {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Remove after delay
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function addKeyboardShortcutsHelp() {
    const shortcuts = [
        { key: 'D / →', action: 'Next image' },
        { key: 'A / ←', action: 'Previous image' },
        { key: 'E', action: 'Next category' },
        { key: 'Q', action: 'Previous category' },
        { key: 'W / ↑', action: 'Confirm image' },
        { key: 'S / ↓', action: 'Copy from previous' },
        { key: 'F', action: 'Toggle sunlight' },
        { key: 'H', action: 'Toggle shortcuts help' }
    ];

    const helpContainer = document.createElement('div');
    helpContainer.className = 'keyboard-shortcuts-help';
    
    const helpHeader = document.createElement('div');
    helpHeader.className = 'shortcuts-header';
    helpHeader.addEventListener('click', toggleShortcutsHelp);
    
    const helpTitle = document.createElement('h3');
    helpTitle.textContent = 'Keyboard Shortcuts';
    
    const collapseIndicator = document.createElement('span');
    collapseIndicator.className = 'collapse-indicator';
    collapseIndicator.innerHTML = '−';
    
    helpHeader.appendChild(helpTitle);
    helpHeader.appendChild(collapseIndicator);
    helpContainer.appendChild(helpHeader);

    const shortcutsList = document.createElement('ul');
    shortcutsList.className = 'shortcuts-list';
    shortcuts.forEach(({ key, action }) => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="shortcut-key">${key}</span> ${action}`;
        shortcutsList.appendChild(li);
    });
    
    helpContainer.appendChild(shortcutsList);
    document.body.appendChild(helpContainer);
}

// Call this after window loads
window.addEventListener('load', () => {
    addKeyboardShortcutsHelp();
});

function resetImage() {
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    if (!currentImage) return;
    
    // Check if the image is confirmed - if so, don't allow reset
    if (currentState.classifications[currentImage].confirmed) {
        showNotification('Cannot reset confirmed images', 'error');
        return;
    }
    
    // Create default grid cells
    const defaultCells = {};
    for (let row = 0; row < GRID_CONFIG.rows; row++) {
        for (let col = 0; col < GRID_CONFIG.columns; col++) {
            const cellId = generateCellId(row, col);
            defaultCells[cellId] = {
                count: '0',
                directSun: false
            };
        }
    }
    
    // Update the classifications
    currentState.classifications[currentImage] = {
        ...currentState.classifications[currentImage],
        cells: defaultCells,
        confirmed: false
    };
    
    // Update the UI
    loadImageByIndex(currentState.currentImageIndex);
    saveClassifications();
}

function findNextUnclassified() {
    for (let i = 0; i < currentState.imageFiles.length; i++) {
        const imageName = currentState.imageFiles[i];
        if (!currentState.classifications[imageName].confirmed) {
            loadImageByIndex(i);
            return;
        }
    }
    showNotification('All images have been classified!', 'info');
}

function updateImageColorMode() {
    const img = document.querySelector('#image-container img');
    if (!img) return;
    
    if (currentState.isColorMode) {
        img.style.filter = 'none';
    } else {
        img.style.filter = 'grayscale(100%)';
    }
}
