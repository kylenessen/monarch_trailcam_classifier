# Refactoring Plan Overview

This document outlines how to break down a large `renderer.js` file (over 1000 lines) into smaller, maintainable modules for an Electron-based photo labeling app. We will refactor incrementally to preserve functionality and ensure easy debugging along the way.

---

## Key Functional Areas

1. **Global State & Configs**  
   - Holds shared data (`currentState`), constants, and configurations (`CLASSIFICATIONS`, `GRID_CONFIG`, `CATEGORIES`).

2. **Classification Logic**  
   - Functions for creating default grid cells, confirming images, copying classifications from a previous image, resetting images, etc.

3. **File & IPC Management**  
   - Loads images, saves/loads classification data, and handles IPC calls with the Electron main process.

4. **Image Display & Grid Overlay**  
   - Responsible for displaying images, creating the grid overlay, handling cell clicks, and updating cell styles.

5. **UI & DOM Manipulation**  
   - Initializes the user interface, sets up event listeners, manages the progress bar, shows notifications, and handles notes dialogs.

6. **Keyboard Shortcuts**  
   - Manages the key-to-action mappings (e.g., next image, previous image, confirm).

---

## Proposed File Structure

```
renderer/
  ├─ index.js            // Main entry point for renderer process
  ├─ state.js            // Shared state, constants, and configs
  ├─ classification.js   // All classification-related logic
  ├─ fileManager.js      // File I/O and IPC communications
  ├─ imageManager.js     // Image display, grid overlay, zoom handling
  ├─ ui.js               // UI initialization, event listeners, dialogs
  └─ shortcuts.js        // Keyboard shortcut mappings and handlers
```

- **`index.js`**: Minimal startup code that imports and calls `initUI()`, `initShortcuts()`, etc.  
- **`state.js`**: Exports global `currentState`, constants, and any helper methods that mutate them.  
- **`classification.js`**: Defines how to set and modify classifications (create, confirm, copy, reset).  
- **`fileManager.js`**: Centralizes all file reads/writes and IPC calls.  
- **`imageManager.js`**: Loads images, builds the grid overlay, handles clicks, zoom, and color mode.  
- **`ui.js`**: Manages UI elements, progress bar updates, notifications, notes dialog, and user prompts.  
- **`shortcuts.js`**: Groups keyboard shortcut mappings; calls methods from the other modules.

---

## Incremental Refactoring Steps

1. **Commit Current State**: Create a safe fallback before refactoring.  
2. **Extract State & Config**: Move `currentState` and constants to `state.js`; test and commit.  
3. **Extract Classification**: Migrate classification functions to `classification.js`; test and commit.  
4. **Extract File Logic**: Move IPC and file I/O to `fileManager.js`; test and commit.  
5. **Extract Image Management**: Move display/overlay logic to `imageManager.js`; test and commit.  
6. **Extract UI Code**: Move event listeners, progress bar, notes dialog, notifications, etc., to `ui.js`; test and commit.  
7. **Extract Shortcuts**: Put keyboard mappings/handlers into `shortcuts.js`; test and commit.  
8. **Clean Up**: Remove unused code, confirm everything is functional, and finalize the structure.
