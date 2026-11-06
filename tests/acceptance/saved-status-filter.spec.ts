import { expect, test } from '@playwright/test';

// Frozen future-feature acceptance. This suite is intentionally RED on starter v1.
const key = 'small-hours.status-view.v1';
const tasks = [
  { id: 'a', title: 'Plan release', details: 'Choose the date.', status: 'todo' },
  { id: 'b', title: 'Review copy', details: '', status: 'in-progress' },
  { id: 'c', title: 'Publish notes', details: '', status: 'done' },
];

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.evaluate((fixture) => localStorage.setItem('small-hours.tasks.v1', JSON.stringify(fixture)), tasks);
  await page.reload();
});

test('one labeled status view shows exactly the matching tasks, including All', async ({ page }) => {
  const view = page.getByRole('combobox', { name: 'Status view', exact: true });
  await expect(view).toHaveCount(1);
  await expect(view).toHaveValue('all');
  await expect(view.locator('option')).toHaveText(['All statuses', 'To do', 'In progress', 'Done']);
  for (const [status, title] of [['todo', 'Plan release'], ['in-progress', 'Review copy'], ['done', 'Publish notes']]) {
    await view.selectOption(status!);
    await expect(page.getByRole('article')).toHaveCount(1);
    await expect(page.getByRole('article').first()).toHaveAccessibleName(title!);
  }
  await view.selectOption('all');
  await expect(page.getByRole('article')).toHaveCount(3);
});

test('selection survives a reload and does not overwrite tasks', async ({ page }) => {
  const view = page.getByRole('combobox', { name: 'Status view', exact: true });
  await view.selectOption('in-progress');
  await page.reload();
  await expect(view).toHaveValue('in-progress');
  await expect(page.getByRole('article')).toHaveCount(1);
  await expect(page.getByRole('article').first()).toHaveAccessibleName('Review copy');
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('small-hours.tasks.v1')!))).toEqual(tasks);
  await view.selectOption('all');
  await page.reload();
  await expect(view).toHaveValue('all');
  await expect(page.getByRole('article')).toHaveCount(3);
});

test('missing, malformed and unknown saved views fall back to All safely', async ({ page }) => {
  for (const value of [null, '{', 'null', '{}', '"obsolete"']) {
    await page.evaluate(({ key, value }) => value === null ? localStorage.removeItem(key) : localStorage.setItem(key, value), { key, value });
    await page.reload();
    await expect(page.getByRole('combobox', { name: 'Status view', exact: true })).toHaveValue('all');
    await expect(page.getByRole('article')).toHaveCount(3);
  }
});

test('CRUD and status changes respect the selected view without losing hidden tasks', async ({ page }) => {
  const view = page.getByRole('combobox', { name: 'Status view', exact: true });
  await view.selectOption('todo');
  await page.getByLabel('Task title').fill('Book room');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('article')).toHaveCount(2);
  const created = page.getByRole('article', { name: 'Book room', exact: true });
  await created.getByRole('button', { name: 'Edit', exact: true }).click();
  await page.getByLabel('Task title').fill('Book studio');
  await page.keyboard.press('Enter');
  const revised = page.getByRole('article', { name: 'Book studio', exact: true });
  await expect(revised).toBeVisible();
  await revised.getByRole('combobox', { name: 'Move Book studio' }).selectOption('done');
  await expect(revised).toHaveCount(0);
  await expect(page.locator(':focus')).toBeVisible();
  expect(await page.locator(':focus').evaluate((node) => /^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(node.tagName))).toBe(true);
  await page.getByRole('combobox', { name: 'Status', exact: true }).selectOption('done');
  await page.getByLabel('Task title').fill('Send invitations');
  await page.keyboard.press('Enter');
  await expect(page.getByRole('article')).toHaveCount(1);
  await expect(view).toHaveValue('todo');
  await page.getByRole('article', { name: 'Plan release', exact: true }).getByRole('button', { name: 'Delete', exact: true }).click();
  await expect(page.getByRole('article')).toHaveCount(0);
  await expect(page.getByText('No tasks in this view.')).toBeVisible();
  await expect(page.locator(':focus')).toBeVisible();
  expect(await page.locator(':focus').evaluate((node) => /^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(node.tagName))).toBe(true);
  await view.selectOption('done');
  await expect(revised).toBeVisible();
  await expect(page.getByRole('article')).toHaveCount(3);
  await view.selectOption('all');
  await page.reload();
  await expect(page.getByRole('article')).toHaveCount(4);
});

test('keyboard selection, focus, mobile layout and unavailable storage stay usable', async ({ page }) => {
  const view = page.getByRole('combobox', { name: 'Status view', exact: true });
  await view.focus();
  await page.keyboard.press('Home');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(view).toHaveValue('todo');
  await expect(view).toBeFocused();
  await page.keyboard.press('Tab');
  expect(await page.evaluate(() => document.activeElement?.tagName)).not.toBe('BODY');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(view).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.addInitScript(() => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = function (key, value) {
      if (key === 'small-hours.status-view.v1') throw new Error('Unavailable');
      return original.call(this, key, value);
    };
    const read = Storage.prototype.getItem;
    Storage.prototype.getItem = function (key) {
      if (key === 'small-hours.status-view.v1') throw new Error('Unavailable');
      return read.call(this, key);
    };
  });
  await page.reload();
  await expect(view).toHaveValue('all');
  await view.selectOption('done');
  await expect(page.getByRole('article')).toHaveCount(1);
  await expect(page.getByRole('article').first()).toHaveAccessibleName('Publish notes');
});
