// Removed: import { ipcRenderer } from 'electron';
// Removed: import path from 'path';
// Removed: import fs from 'fs'; 
import { 
    updateState, 
    getCurrentState, 
    setAllClassifications, 
    createDefaultGridCells 
} from './state.js';
import { showNotification } from './utils.js'; // Assuming utils.js will have showNotification

// --- Folder and Image Loading ---

export async function promptForDeploymentFolder() {
    try {
        // Use preload API
        const folderPath = await window.electronAPI.selectFolder(); 
        // selectFolder now returns path string or null
        if (!folderPath) {
            console.log('Folder selection cancelled or failed.');
            return null; 
        }
        return folderPath;
    } catch (error) {
        console.error('Error in promptForDeploymentFolder:', error);
        showNotification(`Error selecting folder: ${error.message}`, 'error');
        return null;
    }
}

export async function loadImageList(folderPath) {
    try {
        // Use preload API
        const imageFiles = await window.electronAPI.loadImages(folderPath); 
        // loadImages now returns array or throws error

        if (imageFiles.length === 0) {
            showNotification('No images found in selected folder', 'warning');
        }
        
        return imageFiles; // Should be the sorted array of filenames
    } catch (error) {
        console.error('Error loading image list:', error);
        showNotification(`Error loading images: ${error.message}`, 'error');
        return []; // Return empty array on error
    }
}

export async function getImageData(imagePath) {
    try {
        // Use preload API
        const base64Data = await window.electronAPI.getImageData(imagePath); 
        // getImageData now returns base64 string or throws error
        return base64Data;
    } catch (error) {
        const imageName = await window.electronAPI.getPathBasename(imagePath); // Get basename via preload
        console.error(`Error getting image data for ${imageName}:`, error);
        showNotification(`Error loading image ${imageName}: ${error.message}`, 'error');
        return null;
    }
}

// --- Classification File Handling ---

async function getClassificationFilePath(imagesFolder) {
    // Use preload API for path joining
    return await window.electronAPI.pathJoin(imagesFolder, 'classifications.json');
}

export async function loadClassifications(imagesFolder) {
    const classificationFile = await getClassificationFilePath(imagesFolder);
    updateState({ classificationFile }); // Store the path in state

    try {
        // Use preload API to check existence and read
        const exists = await window.electronAPI.checkFileExists(classificationFile);
        if (exists) {
            const data = await window.electronAPI.readFile(classificationFile);
            const loadedClassifications = JSON.parse(data);
            setAllClassifications(loadedClassifications);
            console.log('Classifications loaded successfully.');
            return true;
        } else {
            console.log('No classification file found. Initializing new classifications.');
            return false; // Indicate that initialization is needed
        }
    } catch (error) {
        console.error('Error loading classifications:', error);
        showNotification('Failed to load classifications. Starting fresh.', 'error');
        setAllClassifications({}); // Reset classifications in state on error
        return false; // Indicate that initialization is needed
    }
}

export async function saveClassifications(classifications) {
    const state = getCurrentState();
    if (!state.classificationFile) {
        console.error('Cannot save classifications: classification file path not set in state.');
        showNotification('Error: Classification file path not set.', 'error');
        return;
    }

    try {
        // Use preload API to write file
        const result = await window.electronAPI.writeFile(
            state.classificationFile,
            JSON.stringify(classifications, null, 2) // Pretty print JSON
        );
        if (!result || !result.success) {
             throw new Error(result?.error || 'Unknown error writing file');
        }
        // console.log('Classifications saved successfully.'); // Optional: for debugging
    } catch (error) {
        console.error('Error saving classifications:', error);
        showNotification('Failed to save classifications', 'error');
    }
}

// Helper function to initialize classifications if file doesn't exist
export function initializeClassificationsIfNeeded(imageFiles) {
    const defaultCells = createDefaultGridCells();
    const initialClassifications = imageFiles.reduce((classifications, image, index) => {
        classifications[image] = {
            confirmed: false,
            cells: { ...JSON.parse(JSON.stringify(defaultCells)) }, // Deep copy
            index: index,
            notes: '' // Add notes field
        };
        return classifications;
    }, {});
    setAllClassifications(initialClassifications);
    saveClassifications(initialClassifications); // Save the initial structure
    console.log('Initialized and saved new classifications structure.');
}
