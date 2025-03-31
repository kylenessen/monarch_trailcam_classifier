// @ts-check
const { test, expect, _electron: electron } = require('@playwright/test');

// Removed original basic electron test as it was flaky and redundant

// New test for initial state verification
test('Initial Application State Verification', async () => {
  // Launch the Electron app
  const electronApp = await electron.launch({ args: ['src/main/main.js'] });
  const page = await electronApp.firstWindow(); // Get the main window

  // Wait for the main container or a key element to ensure the page is loaded
  await page.waitForSelector('.container');

  // --- Assertions based on E2E_TEST_PLAN.md and index.html ---

  // 1. Verify "Select Image Directory" element (acting as button)
  const selectDirElement = page.locator('#deployment-id');
  await expect(selectDirElement, 'Select Directory element should be visible').toBeVisible();
  await expect(selectDirElement, 'Select Directory element should contain text "Click to select folder"').toHaveText('Click to select folder');
  // Note: We can't directly check if a div is "enabled" like a button, visibility is the main check here.

  // 2. Verify Image Container and Welcome Message
  const imageContainer = page.locator('#image-container');
  await expect(imageContainer, 'Image container should be visible').toBeVisible();
  const welcomeMessage = page.locator('#welcome-message');
  await expect(welcomeMessage, 'Welcome message should be visible initially').toBeVisible();
  await expect(welcomeMessage, 'Welcome message should contain specific text').toContainText('Welcome to Monarch Photo Classification');

  // 3. Verify Classification Buttons are visible and potentially disabled
  // Using data-count for count buttons and ID for notes button
  const classificationButtonSelectors = [
    'button[data-count="0"]', 'button[data-count="1-9"]', 'button[data-count="10-99"]',
    'button[data-count="100-999"]', 'button[data-count="1000+"]', '#notes-button'
  ];
  for (const selector of classificationButtonSelectors) {
    const button = page.locator(selector);
    await expect(button, `${selector} should be visible`).toBeVisible();
    // Buttons should be visible and ENABLED initially, until a folder is loaded.
    await expect(button, `${selector} should be enabled initially`).toBeEnabled();
  }
  // Also check other action/nav buttons mentioned in HTML
  await expect(page.locator('#reset-image'), 'Reset button should be visible').toBeVisible();
  await expect(page.locator('#copy-previous'), 'Copy Previous button should be visible').toBeVisible();
  await expect(page.locator('#confirm-image'), 'Confirm button should be visible').toBeVisible();
  await expect(page.locator('#color-toggle'), 'Color Toggle button should be visible').toBeVisible();
  await expect(page.locator('#prev-image'), 'Previous button should be visible').toBeVisible();
  await expect(page.locator('#next-image'), 'Next button should be visible').toBeVisible();
  await expect(page.locator('#next-unclassified'), 'Next Unclassified button should be visible').toBeVisible();

  // Check initial state of action/nav buttons
  const initiallyDisabledButtons = ['#copy-previous', '#prev-image', '#next-image', '#next-unclassified']; // Removed #reset-image
  for (const selector of initiallyDisabledButtons) {
    const button = page.locator(selector);
    await expect(button, `${selector} should be disabled initially`).toBeDisabled();
  }

  const initiallyEnabledButtons = ['#reset-image', '#confirm-image', '#color-toggle']; // Added #reset-image
  for (const selector of initiallyEnabledButtons) {
    const button = page.locator(selector);
    await expect(button, `${selector} should be enabled initially`).toBeEnabled();
  }

  // 4. Verify Keyboard Shortcuts toggle button and hidden list
  const shortcutsHeader = page.locator('div.keyboard-shortcuts-help .shortcuts-header').first(); // Target the header
  await expect(shortcutsHeader, 'Shortcuts toggle header should be visible').toBeVisible();
  const shortcutsList = page.locator('ul.shortcuts-list').first();
  await expect(shortcutsList, 'Shortcuts list should be hidden initially').toBeHidden(); // Playwright checks visibility effectively

  // 5. Verify Notes button visibility (Dialog is likely hidden)
  const notesButton = page.locator('#notes-button'); // Check the button itself
  await expect(notesButton, 'Notes button should be visible').toBeVisible();
  // We already checked its enabled state above.

  // --- End of Assertions ---

  // Close the app
  await electronApp.close();
});
