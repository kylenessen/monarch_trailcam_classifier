// @ts-check
const { test, expect, _electron: electron } = require('@playwright/test');

test('basic electron test', async () => {
  // Launch the Electron app defined in package.json
  const electronApp = await electron.launch({ args: ['src/main/main.js'] });

  // Check that app started
  expect(electronApp.windows().length).toBeGreaterThan(0);
  
  // Close the app
  await electronApp.close();
});
