// @ts-check
const { test, expect, _electron: electron } = require('@playwright/test');
const path = require('path');

// __dirname is available directly in CommonJS
const mainProcessPath = path.join(__dirname, '../src/main/main.js');

test('Keyboard shortcuts help toggle', async () => {
  // Launch the Electron app
  const electronApp = await electron.launch({ args: [mainProcessPath] });

  // Wait for the first window to open
  const window = await electronApp.firstWindow();
  await window.waitForLoadState('domcontentloaded'); // Ensure DOM is ready

  // Locate elements
  const shortcutsHeader = window.locator('.shortcuts-header');
  const helpContainer = window.locator('.keyboard-shortcuts-help');
  const collapseIndicator = shortcutsHeader.locator('.collapse-indicator');

  // 1. Initial state: Should be collapsed
  await expect(helpContainer).toHaveClass(/collapsed/);
  await expect(collapseIndicator).toHaveText('+');

  // 2. Click to expand
  await shortcutsHeader.click();
  await expect(helpContainer).not.toHaveClass(/collapsed/);
  await expect(collapseIndicator).toHaveText('−'); // Using minus sign based on ui.js logic

  // 3. Click to collapse again
  await shortcutsHeader.click();
  await expect(helpContainer).toHaveClass(/collapsed/);
  await expect(collapseIndicator).toHaveText('+');

  // Close the app
  await electronApp.close();
});

// Add more tests here later, e.g., for folder selection, classification, etc.
