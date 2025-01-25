// Global variables
let currentImage = null;
let gridCells = [];
let currentClassification = {};
let isZooming = false;
let zoomLevel = 3; // 300% zoom

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
    selectedTool: '10-99',
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
    const defaultCells = createDefaultGridCells();
    const defaultClassifications = createDefaultClassifications(defaultCells);
    
    currentState.classifications = defaultClassifications;
    saveClassifications();
}

function createDefaultGridCells() {
    const cells = {};
    for (let row = 0; row < GRID_CONFIG.rows; row++) {
        for (let col = 0; col < GRID_CONFIG.columns; col++) {
            cells[generateCellId(row, col)] = {
                count: '0',
                directSun: false
            };
        }
    }
    return cells;
}

function createDefaultClassifications(defaultCells) {
    return currentState.imageFiles.reduce((classifications, image, index) => {
        classifications[image] = {
            confirmed: false,
            cells: { ...defaultCells },
            index: index
        };
        return classifications;
    }, {});
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
    // Initialize username from localStorage
    const usernameInput = document.getElementById('username-input');
    usernameInput.value = localStorage.getItem('monarchUsername') || '';
    usernameInput.addEventListener('input', () => {
        localStorage.setItem('monarchUsername', usernameInput.value.trim());
    });

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

    // Add zoom event listeners
    document.addEventListener('keydown', handleZoom);
    document.addEventListener('keyup', handleZoom);
    document.addEventListener('mousemove', updateZoomPosition);
}

function handleZoom(event) {
    const img = document.getElementById('display-image');
    const container = document.getElementById('image-container');
    const gridOverlay = document.querySelector('.grid-overlay');
    
    if (!img || event.key !== 'z') return;
    
    if (event.type === 'keydown' && !isZooming) {
        isZooming = true;
        img.classList.add('zoomed');
        gridOverlay?.classList.add('hidden');
        updateZoomPosition(event);
    } else if (event.type === 'keyup' && isZooming) {
        isZooming = false;
        img.classList.remove('zoomed');
        img.style.transform = 'none';
        gridOverlay?.classList.remove('hidden');
    }
}

function updateZoomPosition(event) {
    if (!isZooming) return;
    
    const img = document.getElementById('display-image');
    const container = document.getElementById('image-container');
    if (!img || !container) return;
    
    const rect = container.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;
    
    // Calculate the position as a percentage of the container
    const xPercent = (mouseX / rect.width) * 100;
    const yPercent = (mouseY / rect.height) * 100;
    
    // Apply the transform with the calculated origin
    img.style.transformOrigin = `${xPercent}% ${yPercent}%`;
    img.style.transform = `scale(${zoomLevel})`;
}

async function promptForDeploymentFolder() {
    try {
        const result = await ipcRenderer.invoke('select-folder');
        if (!result.success) {
            if (result.error) {
                throw new Error(result.error);
            }
            return; // User cancelled selection
        }

        const imageContainer = document.getElementById('image-container');
        const welcomeMessage = document.getElementById('welcome-message');
        const deploymentId = document.getElementById('deployment-id');

        // Hide welcome message if it exists
        if (welcomeMessage) {
            welcomeMessage.style.display = 'none';
        }

        // Clear previous state if exists
        if (currentState.imagesFolder) {
            resetApplicationState();
            clearImageContainer(imageContainer);
        }

        // Set new folder path
        currentState.imagesFolder = result.folderPath;

        // Load and process images
        const imageFiles = await ipcRenderer.invoke('load-images', result.folderPath);
        
        if (!imageFiles?.success && imageFiles?.error) {
            throw new Error(imageFiles.error);
        }

        if (imageFiles && imageFiles.length > 0) {
            currentState.imageFiles = imageFiles;
            
            if (deploymentId) {
                deploymentId.textContent = path.basename(result.folderPath);
            }

            await loadClassifications();
            await findNextUnclassified();
        } else {
            handleNoImagesFound(imageContainer, deploymentId);
        }

        updateProgress();
    } catch (error) {
        console.error('Error in promptForDeploymentFolder:', error);
        showNotification(`Error switching folders: ${error.message}`, 'error');
    }
}

function resetApplicationState() {
    currentState.imageFiles = [];
    currentState.currentImageIndex = -1;
    currentState.classifications = {};
    currentState.selectedCell = null;
    currentState.selectedTool = '10-99';
    currentState.classificationFile = null;
    currentState.originalImageWidth = null;
    currentState.originalImageHeight = null;
    currentState.isLocked = false;
    
    gridCells = [];
    currentImage = null;
    currentClassification = {};
}

function clearImageContainer(container) {
    while (container && container.firstChild) {
        container.removeChild(container.firstChild);
    }
}

function handleNoImagesFound(container, deploymentId) {
    showNotification('No images found in selected folder', 'error');
    
    if (deploymentId) {
        deploymentId.textContent = 'Click to select folder';
    }
    
    if (container) {
        container.innerHTML = `
            <div id="welcome-message">
                <h2>Welcome to Monarch Photo Classification</h2>
                <p>Select an image folder to begin</p>
            </div>
        `;
    }
}

function getImageClassifications(imageName) {
    return currentState.classifications[imageName] || {};
}

function setClassification(imageName, cellId, classification) {
    // Ensure classification entry exists with proper structure
    if (!currentState.classifications[imageName] || !currentState.classifications[imageName].cells) {
        currentState.classifications[imageName] = {
            confirmed: false,
            cells: {},
            index: currentState.imageFiles.indexOf(imageName)
        };
    }
    
    // Update classification and save
    currentState.classifications[imageName].cells[cellId] = classification;
    saveClassifications();
    updateProgress();
}

async function loadImageByIndex(index) {
    try {
        if (index < 0 || index >= currentState.imageFiles.length) {
            throw new Error('Invalid image index');
        }

        const imagePath = path.join(currentState.imagesFolder, currentState.imageFiles[index]);
        const imageData = await ipcRenderer.invoke('get-image-data', imagePath);
        
        if (!imageData?.success) {
            throw new Error(imageData?.error || 'Failed to load image data');
        }

        const currentImage = currentState.imageFiles[index];
        const imageContainer = document.getElementById('image-container');
        
        // Update state early to ensure consistent state
        currentState.currentImageIndex = index;
        
        await setupImageDisplay(currentImage, imageData.data, imageContainer);
        updateProgress();
        
    } catch (error) {
        console.error('Error loading image:', error);
        showNotification(error.message, 'error');
    }
}

function setupImageDisplay(currentImage, imageData, container) {
    return new Promise((resolve) => {
        const isConfirmed = currentState.classifications[currentImage]?.confirmed || false;
        disableClassificationTools(isConfirmed);
        
        // Clear and setup container
        container.innerHTML = '';
        const wrapper = createImageWrapper(currentImage);
        container.appendChild(wrapper);
        
        // Setup image
        const img = new Image();
        img.id = 'display-image';
        
        img.onload = () => {
            updateImageState(img, wrapper);
            resolve();
        };
        
        img.onerror = () => {
            container.innerHTML = '<div class="error-message">Failed to load image</div>';
            resolve();
        };
        
        img.src = `data:image/jpeg;base64,${imageData}`;
        wrapper.appendChild(img);
    });
}

function createImageWrapper(currentImage) {
    const wrapper = document.createElement('div');
    wrapper.className = 'image-wrapper';
    if (currentState.classifications[currentImage]?.confirmed) {
        wrapper.classList.add('confirmed');
    }
    return wrapper;
}

function updateImageState(img, wrapper) {
    currentState.originalImageWidth = img.naturalWidth;
    currentState.originalImageHeight = img.naturalHeight;
    
    updateImageColorMode();
    createGrid(wrapper, img.naturalWidth, img.naturalHeight);
    
    if (currentState.resizeObserver) {
        currentState.resizeObserver.disconnect();
    }
    setupResizeObserver(wrapper, img);
    
    updateNavigationButtons();
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
    
    // Only apply classification if Shift key is pressed
    if (event.shiftKey) {
        applyCurrentClassification(cell, cellId);
    }
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
        cell.style.border = '2px solid rgba(255, 235, 59, 0.8)';
        cell.style.margin = '-1px';
    } else {
        cell.style.border = '1px solid rgba(255, 255, 255, 0.5)';
        cell.style.margin = '0';
    }
}

function initializeUI() {
    progressBar = document.getElementById('progress-bar');
    currentImageSpan = document.getElementById('current-image');
    totalImagesSpan = document.getElementById('total-images');
    progressPercent = document.getElementById('progress-percent');
    
    // Set initial color toggle button text
    const colorToggleBtn = document.getElementById('color-toggle');
    colorToggleBtn.textContent = currentState.isColorMode ? 'Switch to B&W' : 'Switch to Color';
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

// Keyboard shortcut mappings
const KEYBOARD_SHORTCUTS = {
    'ArrowRight': () => navigateImage('next'),
    'd': () => navigateImage('next'),
    'D': () => navigateImage('next'),
    'ArrowLeft': () => navigateImage('previous'),
    'a': () => navigateImage('previous'),
    'A': () => navigateImage('previous'),
    'e': () => cycleCategory('next'),
    'E': () => cycleCategory('next'),
    'q': () => cycleCategory('previous'),
    'Q': () => cycleCategory('previous'),
    'ArrowUp': () => document.getElementById('confirm-image').click(),
    'w': () => document.getElementById('confirm-image').click(),
    'W': () => document.getElementById('confirm-image').click(),
    'ArrowDown': () => document.getElementById('copy-previous').click(),
    's': () => document.getElementById('copy-previous').click(),
    'S': () => document.getElementById('copy-previous').click(),
    'f': () => document.getElementById('sunlight-toggle').click(),
    'F': () => document.getElementById('sunlight-toggle').click(),
    'h': () => toggleShortcutsHelp(),
    'H': () => toggleShortcutsHelp()
};

function handleKeyboardShortcuts(event) {
    // Don't handle shortcuts if we're in an input field
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return;
    }

    const handler = KEYBOARD_SHORTCUTS[event.key];
    if (handler) {
        handler();
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
        currentState.classificationFile = path.join(currentState.imagesFolder, 'classifications.json');
        
        if (fs.existsSync(currentState.classificationFile)) {
            const data = await fs.promises.readFile(currentState.classificationFile, 'utf8');
            currentState.classifications = JSON.parse(data);
        } else {
            initializeClassifications();
        }
    } catch (error) {
        console.error('Error loading classifications:', error);
        showNotification('Failed to load classifications. Starting fresh.', 'error');
        currentState.classifications = {};
        initializeClassifications();
    }
}

async function saveClassifications() {
    try {
        if (!currentState.classificationFile) {
            throw new Error('No classification file path set');
        }
        
        await fs.promises.writeFile(
            currentState.classificationFile,
            JSON.stringify(currentState.classifications, null, 2)
        );
    } catch (error) {
        console.error('Error saving classifications:', error);
        showNotification('Failed to save classifications', 'error');
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

function validateUsername() {
    const username = document.getElementById('username-input').value.trim();
    if (!username) {
        showNotification('Please enter your initials before confirming images', 'error');
        return false;
    }
    if (!/^[a-zA-Z0-9-]{1,30}$/.test(username)) {
        showNotification('Initials can only contain letters, numbers, and hyphens', 'error');
        return false;
    }
    return true;
}

function confirmImage() {
    if (!validateUsername()) return;
    
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    
    if (!currentState.classifications[currentImage]) {
        currentState.classifications[currentImage] = {};
    }
    
    // Store username with classification
    currentState.classifications[currentImage].user = 
        document.getElementById('username-input').value.trim();
    
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

function initializeKeyboardShortcuts() {
    const shortcuts = [
        { key: 'D / →', action: 'Next image' },
        { key: 'A / ←', action: 'Previous image' },
        { key: 'E', action: 'Next category' },
        { key: 'Q', action: 'Previous category' },
        { key: 'W / ↑', action: 'Confirm image' },
        { key: 'S / ↓', action: 'Copy from previous' },
        { key: 'F', action: 'Toggle sunlight' },
        { key: 'Z', action: 'Hold to zoom (300%)' },
        { key: 'H', action: 'Toggle shortcuts help' }
    ];

    const shortcutsList = document.querySelector('.shortcuts-list');
    shortcuts.forEach(({ key, action }) => {
        const li = document.createElement('li');
        li.innerHTML = `<span class="shortcut-key">${key}</span> ${action}`;
        shortcutsList.appendChild(li);
    });

    // Add click handler for the shortcuts header
    document.querySelector('.shortcuts-header').addEventListener('click', toggleShortcutsHelp);
}

// Call this after window loads
window.addEventListener('load', () => {
    initializeKeyboardShortcuts();
});

function resetImage() {
    const currentImage = currentState.imageFiles[currentState.currentImageIndex];
    if (!currentImage) return;
    
    try {
        if (currentState.classifications[currentImage].confirmed) {
            throw new Error('Cannot reset confirmed images');
        }
        
        // Reset to default state while preserving the image's index
        const currentIndex = currentState.classifications[currentImage].index;
        currentState.classifications[currentImage] = {
            confirmed: false,
            cells: createDefaultGridCells(),
            index: currentIndex
        };
        
        loadImageByIndex(currentState.currentImageIndex);
        saveClassifications();
        showNotification('Image reset successfully', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
    }
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
