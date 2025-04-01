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

  // Locate elements specifically for Keyboard Shortcuts section
  // Find the container that has an h3 with text 'Keyboard Shortcuts'
  const helpContainer = window.locator('div.keyboard-shortcuts-help:has(h3:has-text("Keyboard Shortcuts"))');
  const shortcutsHeader = helpContainer.locator('.shortcuts-header'); // Header within the correct container
  const collapseIndicator = shortcutsHeader.locator('.collapse-indicator');

  // 1. Initial state: Should be collapsed
  await expect(helpContainer).toHaveClass(/collapsed/);
  await expect(collapseIndicator).toHaveText('+');

  // 2. Click to expand
  await shortcutsHeader.click();
  // Wait for the class to be removed first, then check the indicator text
  await expect(helpContainer, 'Help container should not have collapsed class after expand').not.toHaveClass(/collapsed/);
  await expect(collapseIndicator, 'Indicator should change to minus after expand').toHaveText('−');


  // 3. Click to collapse again
  await shortcutsHeader.click();
  await expect(helpContainer).toHaveClass(/collapsed/);
  await expect(collapseIndicator).toHaveText('+');

  // Close the app
  await electronApp.close();
});

// Add more tests here later, e.g., for folder selection, classification, etc.
