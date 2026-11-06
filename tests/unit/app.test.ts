import { beforeEach, describe, expect, it } from 'vitest';
import { mountTaskboard } from '../../src/app';
import { TASKS_KEY } from '../../src/storage';

function field<T extends HTMLElement>(selector: string): T {
  const result = document.querySelector<T>(selector);
  if (!result) throw new Error(`Missing control: ${selector}`);
  return result;
}
function submit(title: string, details = '') {
  field<HTMLInputElement>('#task-title').value = title;
  field<HTMLTextAreaElement>('#task-details').value = details;
  field<HTMLFormElement>('#task-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}

describe('taskboard DOM boundary', () => {
  beforeEach(() => {
    localStorage.clear();
    document.body.innerHTML = '<div id="app"></div>';
  });

  it('creates, edits, moves, reloads and deletes a task through labeled controls', () => {
    mountTaskboard(field('#app'));
    expect(document.querySelectorAll('.task-card')).toHaveLength(6);
    submit('  Make tea  ', 'Water the mint.');
    expect(document.querySelectorAll('.task-card')).toHaveLength(7);
    expect(field('#announcement').textContent).toMatch(/created/i);
    expect(document.activeElement?.id).toBe('task-title');
    const created = Array.from(document.querySelectorAll<HTMLElement>('.task-card')).find((card) => card.textContent?.includes('Make tea'))!;
    created.querySelector<HTMLButtonElement>('button')!.click();
    expect(field<HTMLInputElement>('#task-title').value).toBe('Make tea');
    expect(document.activeElement?.id).toBe('task-title');
    submit('Brew tea', 'Use the blue pot.');
    const edited = Array.from(document.querySelectorAll<HTMLElement>('.task-card')).find((card) => card.textContent?.includes('Brew tea'))!;
    const select = edited.querySelector('select')!;
    select.value = 'done';
    select.dispatchEvent(new Event('change', { bubbles: true }));
    expect(document.activeElement?.getAttribute('aria-label')).toBe('Move Brew tea');
    mountTaskboard(field('#app'));
    const restored = Array.from(document.querySelectorAll<HTMLElement>('.task-card')).find((card) => card.textContent?.includes('Brew tea'))!;
    expect(restored.querySelector('select')!.value).toBe('done');
    restored.querySelectorAll<HTMLButtonElement>('button')[1]!.click();
    expect(field('#task-list').textContent).not.toContain('Brew tea');
    expect(field('#announcement').textContent).toMatch(/deleted/i);
    expect(document.activeElement?.tagName).toBe('BUTTON');
  });

  it('shows validation, supports cancel, and renders user content as text', () => {
    mountTaskboard(field('#app'));
    submit('  ');
    expect(field('#form-error').textContent).toMatch(/title/i);
    expect(field('#task-title').getAttribute('aria-invalid')).toBe('true');
    document.querySelector<HTMLButtonElement>('.task-card button')!.click();
    field<HTMLButtonElement>('#cancel-edit').click();
    expect(field<HTMLInputElement>('#task-title').value).toBe('');
    expect(field('#form-heading').textContent).toBe('New task');
    submit('<img src=x onerror=alert(1)>', '<script>alert(1)</script>');
    expect(document.querySelectorAll('.task-card img, .task-card script')).toHaveLength(0);
    expect(document.querySelector('.task-card')?.textContent).toContain('<img src=x onerror=alert(1)>');
    submit('x'.repeat(101));
    expect(field('#form-error').textContent).toMatch(/title/i);
  });

  it('renders empty state, resets editing when that task is deleted, and keeps focus reachable', () => {
    localStorage.setItem(TASKS_KEY, JSON.stringify([{ id: 'one', title: 'Only task', details: '', status: 'todo' }]));
    mountTaskboard(field('#app'));
    document.querySelector<HTMLButtonElement>('.task-card button')!.click();
    document.querySelectorAll<HTMLButtonElement>('.task-card button')[1]!.click();
    expect(field('#empty-state').textContent).toMatch(/clear board/i);
    expect(field('#form-heading').textContent).toBe('New task');
    expect(document.activeElement?.id).toBe('task-title');
    mountTaskboard(field('#app'));
    expect(document.querySelectorAll('.task-card')).toHaveLength(0);
  });

  it('explains damaged or unavailable storage and keeps session edits usable', () => {
    localStorage.setItem(TASKS_KEY, '{');
    mountTaskboard(field('#app'));
    expect(field('#storage-warning').textContent).toMatch(/could not read/i);
    mountTaskboard(field('#app'), () => { throw new Error('Blocked'); });
    submit('Session task');
    expect(document.body.textContent).toContain('Session task');
    expect(field('#storage-warning').textContent).toMatch(/until.*reload/i);
  });

  it('keeps focus on the moved task when task titles repeat', () => {
    localStorage.setItem(TASKS_KEY, JSON.stringify([
      { id: 'first', title: 'Same title', details: '', status: 'todo' },
      { id: 'second', title: 'Same title', details: '', status: 'todo' },
    ]));
    mountTaskboard(field('#app'));
    const second = document.querySelectorAll<HTMLSelectElement>('.task-card select')[1]!;
    second.value = 'done';
    second.dispatchEvent(new Event('change', { bubbles: true }));
    expect(document.activeElement?.closest('article')?.querySelector('h3')?.id).toBe('task-second');
  });
});
