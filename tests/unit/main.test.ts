import { expect, it } from 'vitest';

it('boots the actual application entry point', async () => {
  localStorage.clear();
  document.body.innerHTML = '<div id="app"></div>';
  await import('../../src/main');
  expect(document.querySelector('h1')?.textContent).toContain('Make room for');
  expect(document.querySelectorAll('article')).toHaveLength(6);
});
