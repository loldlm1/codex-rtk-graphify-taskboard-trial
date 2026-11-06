import { beforeEach, describe, expect, it } from 'vitest';
import { mountTaskboard } from '../../src/app';
import { TASKS_KEY } from '../../src/storage';
import type { Task } from '../../src/tasks';

const VIEW_KEY = 'small-hours.status-view.v1';
const fixture: Task[] = [
  { id: 'hidden', title: 'Done already', details: '', status: 'done' },
  { id: 'first', title: 'First step', details: '', status: 'todo' },
  { id: 'middle', title: 'Middle step', details: '', status: 'todo' },
  { id: 'last', title: 'Last step', details: '', status: 'todo' },
];

function field<T extends HTMLElement>(selector: string): T {
  const control = document.querySelector<T>(selector);
  if (!control) throw new Error(`Missing control: ${selector}`);
  return control;
}

function change(select: HTMLSelectElement, value: string): void {
  select.value = value;
  select.dispatchEvent(new Event('change', { bubbles: true }));
}

function view(value: string): HTMLSelectElement {
  const select = field<HTMLSelectElement>('#status-view');
  select.focus();
  change(select, value);
  return select;
}

function card(id: string): HTMLElement {
  return field(`#task-${id}`).closest('article')!;
}

function submit(title: string, status: string): void {
  field<HTMLInputElement>('#task-title').value = title;
  field<HTMLSelectElement>('#task-status').value = status;
  field<HTMLFormElement>('#task-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
}

describe('saved status views through the DOM', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(TASKS_KEY, JSON.stringify(fixture));
    document.body.innerHTML = '<div id="app"></div>';
  });

  it('labels one native view, filters without task writes, retains focus and restores the preference', () => {
    mountTaskboard(field('#app'));
    const select = field<HTMLSelectElement>('#status-view');
    expect(document.querySelector('label[for="status-view"]')?.textContent).toBe('Status view');
    expect(Array.from(select.options, (option) => [option.text, option.value])).toEqual([
      ['All statuses', 'all'], ['To do', 'todo'], ['In progress', 'in-progress'], ['Done', 'done'],
    ]);
    expect(select.value).toBe('all');
    expect(view('done')).toBe(document.activeElement);
    expect(document.querySelectorAll('article')).toHaveLength(1);
    expect(card('hidden').textContent).toContain('Done already');
    expect(localStorage.getItem(TASKS_KEY)).toBe(JSON.stringify(fixture));
    mountTaskboard(field('#app'));
    expect(field<HTMLSelectElement>('#status-view').value).toBe('done');
    expect(document.querySelectorAll('article')).toHaveLength(1);
    view('all');
    expect(document.querySelectorAll('article')).toHaveLength(4);
  });

  it('distinguishes an empty view from the existing empty-board state', () => {
    mountTaskboard(field('#app'));
    view('in-progress');
    expect(field('#empty-view').hidden).toBe(false);
    expect(field('#empty-view').textContent).toBe('No tasks in this view.');
    expect(field('#empty-state').hidden).toBe(true);
    localStorage.setItem(TASKS_KEY, '[]');
    mountTaskboard(field('#app'));
    expect(field('#empty-view').hidden).toBe(true);
    expect(field('#empty-state').hidden).toBe(false);
  });

  it.each([
    ['first', 'middle'], ['middle', 'last'], ['last', 'middle'],
  ])('deleting %s focuses the visible neighbor %s despite hidden tasks', (removed, next) => {
    mountTaskboard(field('#app'));
    view('todo');
    const button = card(removed!).querySelectorAll<HTMLButtonElement>('button')[1]!;
    button.focus();
    button.click();
    expect(document.activeElement).toBe(card(next!).querySelector('button'));
    expect(document.querySelectorAll('article')).toHaveLength(2);
  });

  it('returns focus to the view when a focused moved card leaves it, and preserves the task', () => {
    mountTaskboard(field('#app'));
    const select = view('todo');
    const move = card('middle').querySelector('select')!;
    move.focus();
    change(move, 'done');
    expect(document.activeElement).toBe(select);
    expect(document.getElementById('task-middle')).toBeNull();
    view('done');
    expect(card('middle').querySelector('select')!.value).toBe('done');
    expect(JSON.parse(localStorage.getItem(TASKS_KEY)!) as Task[]).toHaveLength(4);
  });

  it('keeps editing and nonmatching creation usable without revealing hidden cards', () => {
    mountTaskboard(field('#app'));
    view('todo');
    card('first').querySelector<HTMLButtonElement>('button')!.click();
    submit('Revised step', 'done');
    expect(document.getElementById('task-first')).toBeNull();
    expect(document.activeElement?.id).toBe('task-title');
    submit('Another finished task', 'done');
    expect(document.querySelectorAll('article')).toHaveLength(2);
    expect(field<HTMLSelectElement>('#status-view').value).toBe('todo');
    view('done');
    expect(card('first').textContent).toContain('Revised step');
    expect(field('#task-list').textContent).toContain('Another finished task');
  });

  it('keeps the chosen view and task operations usable after a preference write failure', () => {
    let failWrite = true;
    mountTaskboard(field('#app'), () => ({
      getItem: (key) => localStorage.getItem(key),
      setItem: (key, value) => {
        if (key === VIEW_KEY && failWrite) throw new Error('Preference unavailable');
        localStorage.setItem(key, value);
      },
    }));
    view('done');
    expect(document.querySelectorAll('article')).toHaveLength(1);
    expect(field('#view-warning').hidden).toBe(false);
    expect(field('#view-warning').textContent).toMatch(/could not be saved/i);
    submit('Still works', 'done');
    expect(field('#task-list').textContent).toContain('Still works');
    expect(field('#view-warning').hidden).toBe(false);
    failWrite = false;
    view('todo');
    expect(field('#view-warning').hidden).toBe(true);
    expect(localStorage.getItem(VIEW_KEY)).toBe('"todo"');
  });
});
