const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron'); // Added shell
const path = require('path');
const fs = require('fs').promises;

// Constants
const VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png'];

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1280,
        height: 900,
        webPreferences: {
            preload: path.join(__dirname, '../preload.js'), // Load preload script
            nodeIntegration: false, // Disable Node.js integration in renderer
            contextIsolation: true // Enable context isolation
        }
    });

    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
}

// IPC Handlers

// Handle request to open folder dialog
ipcMain.handle('select-folder', async () => {
    try {
        const result = await dialog.showOpenDialog(BrowserWindow.getFocusedWindow(), { // Added parent window
            properties: ['openDirectory']
        });

        if (!result.canceled && result.filePaths.length > 0) {
            return result.filePaths[0]; // Return only the path string on success
        }
        return null; // Return null if canceled or no path selected
    } catch (error) {
        console.error('Error selecting folder:', error);
        return null; // Return null on error
    }
});

// Handle request to get path basename
ipcMain.handle('get-path-basename', async (event, filePath) => {
    try {
        return path.basename(filePath);
    } catch (error) {
        console.error('Error getting path basename:', error);
        throw error;
    }
});

// Handle request to join path segments
ipcMain.handle('path-join', async (event, ...args) => {
    try {
        return path.join(...args);
    } catch (error) {
        console.error('Error joining path:', error);
        throw error;
    }
});

// Handle request to open external link
ipcMain.handle('open-external-link', async (event, url) => {
    try {
        await shell.openExternal(url);
        return { success: true };
    } catch (error) {
        console.error('Failed to open external link:', error);
        return { success: false, error: error.message };
    }
});


ipcMain.handle('load-images', async (event, folderPath) => {
    try {
        const files = await fs.readdir(folderPath);
        const imageFiles = [];

        for (const file of files) {
            const ext = path.extname(file).toLowerCase();
            if (VALID_IMAGE_EXTENSIONS.includes(ext)) {
                const fullPath = path.join(folderPath, file);
                try {
                    await fs.access(fullPath, fs.constants.R_OK);
                    imageFiles.push(file);
                } catch (err) {
                    console.error(`File ${fullPath} exists but is not readable:`, err);
                }
            }
        }
        
        return imageFiles.sort(); // Return array directly on success
    } catch (error) {
        console.error('Error loading images:', error);
        throw error; // Throw error to be caught by invoke in preload/renderer
    }
});

ipcMain.handle('get-image-data', async (event, imagePath) => {
    try {
        // No need to stat separately, readFile will throw if inaccessible
        const imageBuffer = await fs.readFile(imagePath);
        return imageBuffer.toString('base64'); // Return base64 string directly
    } catch (error) {
        console.error('Error loading image:', error);
        throw error; // Throw error
    }
});

// Handle request to check if a file exists
ipcMain.handle('check-file-exists', async (event, filePath) => {
    try {
        await fs.access(filePath, fs.constants.F_OK);
        return true;
    } catch (error) {
        // If error code is ENOENT (file not found), return false, otherwise rethrow
        if (error.code === 'ENOENT') {
            return false;
        }
        console.error('Error checking file existence:', error);
        throw error;
    }
});

// Handle request to read a file
ipcMain.handle('read-file', async (event, filePath) => {
    try {
        const content = await fs.readFile(filePath, 'utf8');
        return content;
    } catch (error) {
        console.error('Error reading file:', error);
        throw error;
    }
});

// Handle request to write a file
ipcMain.handle('write-file', async (event, filePath, content) => {
    try {
        await fs.writeFile(filePath, content, 'utf8');
        return { success: true };
    } catch (error) {
        console.error('Error writing file:', error);
        throw error;
    }
});


app.whenReady().then(() => {
    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
