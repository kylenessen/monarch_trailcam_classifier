const { test, expect, _electron: electron } = require('@playwright/test');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');

test('Example annotations can be opened, edited, saved and reopened', async () => {
  const folder = await fs.mkdtemp(path.join(os.tmpdir(), 'monarch-example-'));
  const example = path.resolve(__dirname, '../../examples/UDMH2');
  const config = path.join(folder, 'configurations.json');
  const imageName = 'UDMH2_20240105142001.JPG';
  let app;
  try {
    await fs.cp(example, folder, { recursive: true });
    const before = JSON.parse(await fs.readFile(config, 'utf8'));
    app = await electron.launch({ args: ['src/main/main.js'] });
    await app.evaluate(({ dialog }, folder) => {
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [folder] });
    }, folder);
    const page = await app.firstWindow();
    await page.locator('#deployment-section').click();
    await expect(page.locator('#display-image')).toBeVisible();
    await expect(page.locator('.grid-cell')).toHaveCount(18 * 32);
    await expect(page.locator('#total-images')).toHaveText('1');
    await expect(page.locator('#copy-previous')).toBeDisabled();
    await page.locator('#username-input').fill('TEST');
    await page.locator('#confirm-image').click();
    await expect.poll(async () => JSON.parse(await fs.readFile(config, 'utf8'))
      .classifications[imageName].confirmed).toBe(false);
    const saved = JSON.parse(await fs.readFile(config, 'utf8'));
    expect(saved.classifications[imageName].cells).toEqual(before.classifications[imageName].cells);
    await expect(page.locator('#copy-previous')).toBeDisabled();
    await app.close();
    app = await electron.launch({ args: ['src/main/main.js'] });
    await app.evaluate(({ dialog }, folder) => {
      dialog.showOpenDialog = async () => ({ canceled: false, filePaths: [folder] });
    }, folder);
    const reopened = await app.firstWindow();
    await reopened.locator('#deployment-section').click();
    await expect(reopened.locator('#display-image')).toBeVisible();
    await expect(reopened.locator('#confirm-image')).toHaveText('Confirm Image');
  } finally {
    if (app) await app.close();
    await fs.rm(folder, { recursive: true, force: true });
  }
});
