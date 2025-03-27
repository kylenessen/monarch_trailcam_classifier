import { ipcRenderer } from 'electron';
import path from 'path';
import fs from 'fs'; // Use Node.js fs directly in renderer
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
        const result = await ipcRenderer.invoke('select-folder');
        if (!result.success) {
            if (result.error) {
                throw new Error(result.error);
            }
            return null; // User cancelled selection
        }
        return result.folderPath;
    } catch (error) {
        console.error('Error in promptForDeploymentFolder:', error);
        showNotification(`Error selecting folder: ${error.message}`, 'error');
        return null;
    }
}

export async function loadImageList(folderPath) {
    try {
        const imageFilesResult = await ipcRenderer.invoke('load-images', folderPath);
        
        // Check if the result indicates an error
        if (typeof imageFilesResult === 'object' && imageFilesResult !== null && imageFilesResult.success === false && imageFilesResult.error) {
            throw new Error(imageFilesResult.error);
        }
        
        // Check if the result is an array (successful case)
        if (!Array.isArray(imageFilesResult)) {
             // Handle unexpected non-array result that isn't a structured error
             console.error('Unexpected result from load-images IPC:', imageFilesResult);
             throw new Error('Received unexpected data format when loading images.');
        }

        if (imageFilesResult.length === 0) {
            showNotification('No images found in selected folder', 'warning');
        }
        
        return imageFilesResult; // Should be the sorted array of filenames
    } catch (error) {
        console.error('Error loading image list:', error);
        showNotification(`Error loading images: ${error.message}`, 'error');
        return []; // Return empty array on error
    }
}

export async function getImageData(imagePath) {
    try {
        const imageDataResult = await ipcRenderer.invoke('get-image-data', imagePath);
        
        if (!imageDataResult?.success) {
            throw new Error(imageDataResult?.error || 'Failed to load image data');
        }
        return imageDataResult.data; // Base64 string
    } catch (error) {
        console.error('Error getting image data:', error);
        showNotification(`Error loading image ${path.basename(imagePath)}: ${error.message}`, 'error');
        return null;
    }
}

// --- Classification File Handling ---

function getClassificationFilePath(imagesFolder) {
    return path.join(imagesFolder, 'classifications.json');
}

export async function loadClassifications(imagesFolder) {
    const classificationFile = getClassificationFilePath(imagesFolder);
    updateState({ classificationFile }); // Store the path in state

    try {
        // Check if the file exists using Node's fs module
        if (fs.existsSync(classificationFile)) {
            const data = await fs.promises.readFile(classificationFile, 'utf8');
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
        // Use Node's fs module directly
        await fs.promises.writeFile(
            state.classificationFile,
            JSON.stringify(classifications, null, 2) // Pretty print JSON
        );
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
