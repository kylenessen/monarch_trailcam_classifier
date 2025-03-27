const { contextBridge, ipcRenderer } = require('electron');
// Removed: const path = require('path'); 

console.log('Preload script loaded.');

contextBridge.exposeInMainWorld('electronAPI', {
  // Function to request folder selection from the main process
  selectFolder: () => ipcRenderer.invoke('select-folder'),

  // Function to request opening an external link from the main process
  openExternalLink: (url) => ipcRenderer.invoke('open-external-link', url),

  // --- Path Operations via IPC ---
  getPathBasename: (filePath) => ipcRenderer.invoke('get-path-basename', filePath),
  pathJoin: (...args) => ipcRenderer.invoke('path-join', ...args),

  // --- File System Operations via IPC ---
  loadImages: (folderPath) => ipcRenderer.invoke('load-images', folderPath),
  getImageData: (imagePath) => ipcRenderer.invoke('get-image-data', imagePath),
  checkFileExists: (filePath) => ipcRenderer.invoke('check-file-exists', filePath),
  readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
  writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
});

console.log('electronAPI exposed on window object.');
