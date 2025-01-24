const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;

// Constants
const VALID_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png'];

function createWindow() {
    const mainWindow = new BrowserWindow({
        width: 1280,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
}

// IPC Handlers
ipcMain.handle('select-folder', async () => {
    try {
        const result = await dialog.showOpenDialog({
            properties: ['openDirectory']
        });

        if (!result.canceled) {
            return {
                success: true,
                folderPath: result.filePaths[0]
            };
        }
        return { success: false };
    } catch (error) {
        console.error('Error in select-folder:', error);
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
        
        return imageFiles.sort();
    } catch (error) {
        console.error('Error loading images:', error);
        return { success: false, error: error.message };
    }
});

ipcMain.handle('get-image-data', async (event, imagePath) => {
    try {
        await fs.stat(imagePath); // Check if file exists and is accessible
        const imageBuffer = await fs.readFile(imagePath);
        return {
            success: true,
            data: imageBuffer.toString('base64')
        };
    } catch (error) {
        console.error('Error loading image:', error);
        return { success: false, error: error.message };
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
