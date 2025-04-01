// Removed: import { ipcRenderer } from 'electron';
// Removed: import path from 'path';
// Removed: import fs from 'fs';
import {
    updateState, // Keep only one
    getCurrentState,
    setAllClassifications,
    // createDefaultGridCells, // No longer needed here
    setGridConfig,
    getGridConfig
} from './state.js';
import { showNotification } from './utils.js';
import { promptForGridResolution } from './ui.js'; // Import the new UI prompt function (will be created later)

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

// --- Configuration and Classification File Handling ---

// Gets the path to configurations.json within the deployment folder
async function getConfigurationFilePath(deploymentFolder) {
    // Use preload API for path joining
    return await window.electronAPI.pathJoin(deploymentFolder, 'configurations.json');
}

/**
 * Loads configuration (grid size) and classifications from configurations.json.
 * If the file doesn't exist, it prompts the user for grid settings and creates the file.
 * @param {string} deploymentFolder - The main folder selected by the user.
 * @param {string} imagesFolder - The path to the subfolder containing images.
 * @returns {Promise<boolean>} - True if configuration was loaded/created successfully, false otherwise.
 */
export async function loadOrInitializeConfiguration(deploymentFolder, imagesFolder) {
    const configFilePath = await getConfigurationFilePath(deploymentFolder);
    updateState({ classificationFile: configFilePath }); // Store path for saving later

    try {
        const exists = await window.electronAPI.checkFileExists(configFilePath);

        if (exists) {
            // --- Load Existing Configuration ---
            console.log('Loading existing configurations.json...');
            const fileContent = await window.electronAPI.readFile(configFilePath);
            const parsedData = JSON.parse(fileContent);

            // Validate structure
            if (typeof parsedData.rows !== 'number' || typeof parsedData.columns !== 'number' || typeof parsedData.classifications !== 'object') {
                console.error('Invalid configurations.json structure.', parsedData);
                showNotification('Error: configurations.json has an invalid format.', 'error');
                return false; // Indicate failure
            }

            // Set state from loaded file
            setGridConfig(parsedData.rows, parsedData.columns);
            setAllClassifications(parsedData.classifications);
            console.log(`Configuration loaded: ${parsedData.rows} rows, ${parsedData.columns} columns.`);
            return true; // Indicate success

        } else {
            // --- Initialize New Configuration ---
            console.log('No configurations.json found. Initializing new configuration...');

            // No need to get image dimensions if aspect ratio is fixed 16:9

            // Prompt user for rows and create file (logic is in ui.js)
            // promptForGridResolution will now use the fixed 16:9 ratio internally.
            const creationSuccess = await promptForGridResolution(); // Call without dimensions

            if (creationSuccess) {
                console.log('New configuration created and saved.');
                // Classifications state is already initialized to {} by prompt handler
                return true; // Indicate success
            } else {
                console.log('Configuration creation cancelled or failed.');
                return false; // Indicate failure or cancellation
            }
        }
    } catch (error) {
        console.error('Error loading or initializing configuration:', error);
        showNotification(`Error processing configuration: ${error.message}`, 'error');
        setAllClassifications({}); // Reset state on error
        setGridConfig(null, null); // Reset grid config
        return false; // Indicate failure
    }
}

/**
 * Saves the current classifications state (including grid config) to configurations.json.
 */
export async function saveClassifications() {
    const state = getCurrentState();
    if (!state.classificationFile) {
        console.error('Cannot save classifications: configuration file path not set.');
        // No notification here, might be too noisy during normal operation
        return;
    }

    // Construct the data object in the new format
    const dataToSave = {
        rows: state.currentGridConfig.rows,
        columns: state.currentGridConfig.columns,
        classifications: state.classifications // The actual image classifications
    };

    try {
        // Use preload API to write file
        const result = await window.electronAPI.writeFile(
            state.classificationFile,
            JSON.stringify(dataToSave, null, 2) // Pretty print JSON
        );
        if (!result || !result.success) {
            throw new Error(result?.error || 'Unknown error writing file');
        }
        // console.log('Configuration saved successfully.'); // Optional: for debugging
    } catch (error) {
        console.error('Error saving configuration:', error);
        showNotification('Failed to save configuration', 'error');
    }
}

// Removed initializeClassificationsIfNeeded function as its logic is integrated elsewhere.
