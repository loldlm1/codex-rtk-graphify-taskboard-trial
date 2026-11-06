import { expect, test } from '@playwright/test';

test('keyboard creation, edit, status, reload and delete remain usable', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('article')).toHaveCount(6);
  await page.getByLabel('Task title').focus();
  await page.keyboard.type('Make tea');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('textbox', { name: 'Details', exact: true })).toBeFocused();
  await page.keyboard.type('Use the blue pot.');
  await page.getByLabel('Task title').focus();
  await page.keyboard.press('Enter');
  const task = page.getByRole('article', { name: 'Make tea', exact: true });
  await expect(task).toBeVisible();
  await expect(page.getByLabel('Task title')).toBeFocused();
  await task.getByRole('button', { name: 'Edit', exact: true }).click();
  await expect(page.getByLabel('Task title')).toBeFocused();
  await page.getByLabel('Task title').fill('Brew tea');
  await page.keyboard.press('Enter');
  const revised = page.getByRole('article', { name: 'Brew tea', exact: true });
  await revised.getByRole('combobox', { name: 'Move Brew tea' }).selectOption('done');
  await expect(revised.getByRole('combobox')).toBeFocused();
  await page.reload();
  await expect(revised.getByRole('combobox')).toHaveValue('done');
  await expect(revised).toContainText('Use the blue pot.');
  await revised.getByRole('button', { name: 'Delete', exact: true }).focus();
  await page.keyboard.press('Enter');
  await expect(revised).toHaveCount(0);
  await expect(page.getByRole('status')).toContainText('deleted');
  await page.reload();
  await expect(revised).toHaveCount(0);
  expect(errors).toEqual([]);
});

test('validation, cancellation, literal content and empty-board recovery', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Task title').fill('   ');
  await page.getByRole('button', { name: 'Add task', exact: true }).click();
  await expect(page.getByLabel('Task title')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByText('Use a task title between 1 and 100 characters.')).toBeVisible();
  await page.getByRole('article').first().getByRole('button', { name: 'Edit', exact: true }).click();
  await page.getByRole('button', { name: 'Cancel editing' }).click();
  await expect(page.getByLabel('Task title')).toHaveValue('');
  await page.getByLabel('Task title').fill('<img src=x onerror=alert(1)>');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('article').first()).toContainText('<img src=x onerror=alert(1)>');
  await expect(page.locator('.task-card img')).toHaveCount(0);
  while (await page.getByRole('article').count()) {
    await page.getByRole('article').first().getByRole('button', { name: 'Delete', exact: true }).click();
  }
  await expect(page.getByText('A clear board. A fresh start.')).toBeVisible();
  await expect(page.getByLabel('Task title')).toBeFocused();
  await page.reload();
  await expect(page.getByRole('article')).toHaveCount(0);
  await page.evaluate(() => localStorage.setItem('small-hours.tasks.v1', '{'));
  await page.reload();
  await expect(page.getByRole('article')).toHaveCount(6);
  await expect(page.getByRole('alert')).toContainText('could not read');
});

test('blocked storage keeps the board usable with an honest warning', async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', { get() { throw new Error('Unavailable'); } });
  });
  await page.goto('/');
  await expect(page.getByRole('article')).toHaveCount(6);
  await page.getByLabel('Task title').fill('Session task');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('article', { name: 'Session task', exact: true })).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('until you reload');
});

test('desktop and mobile layouts keep controls visible without horizontal overflow', async ({ page }, testInfo) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Make room for good work.' })).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath('desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByLabel('Task title')).toBeVisible();
  await expect(page.getByRole('article')).toHaveCount(6);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByLabel('Task title').fill('A long task title '.repeat(5));
  await page.keyboard.press('Enter');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('mobile.png'), fullPage: true });
});
