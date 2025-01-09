const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs').promises;

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

// Handle folder selection
ipcMain.handle('select-folder', async () => {
    try {
        console.log('Opening folder selection dialog');
        const result = await dialog.showOpenDialog({
            properties: ['openDirectory']
        });
        console.log('Dialog result:', result);

        if (!result.canceled) {
            const folderPath = result.filePaths[0];
            console.log('Selected folder:', folderPath);
            return {
                success: true,
                folderPath: folderPath
            };
        }
        console.log('Dialog was canceled');
        return { success: false };
    } catch (error) {
        console.error('Error in select-folder:', error);
        return { success: false, error: error.message };
    }
});

// Handle loading images from selected folder
ipcMain.handle('load-images', async (event, folderPath) => {
    try {
        console.log('Loading images from:', folderPath);
        const files = await fs.readdir(folderPath);
        console.log('Found files:', files);
        
        const imageFiles = [];
        for (const file of files) {
            const ext = path.extname(file).toLowerCase();
            if (['.jpg', '.jpeg', '.png'].includes(ext)) {
                const fullPath = path.join(folderPath, file);
                try {
                    await fs.access(fullPath, fs.constants.R_OK);
                    imageFiles.push(file);
                } catch (err) {
                    console.error(`File ${fullPath} exists but is not readable:`, err);
                }
            }
        }
        
        console.log('Filtered image files:', imageFiles);
        return imageFiles.sort();
    } catch (error) {
        console.error('Error loading images:', error);
        throw error; // Propagate error to renderer
    }
});

// Handle getting image data
ipcMain.handle('get-image-data', async (event, imagePath) => {
    try {
        console.log('Loading image data from:', imagePath);
        const stats = await fs.stat(imagePath);
        console.log('File stats:', stats);
        
        const imageBuffer = await fs.readFile(imagePath);
        console.log('Successfully read image buffer of size:', imageBuffer.length);
        return imageBuffer.toString('base64');
    } catch (error) {
        console.error('Error loading image:', error);
        return null;
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
