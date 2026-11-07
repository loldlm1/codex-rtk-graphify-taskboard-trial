import { beforeEach, describe, expect, it } from 'vitest';
import { mountTaskboard } from '../../src/app';
import { TASKS_KEY } from '../../src/storage';
import type { StorageAccess } from '../../src/storage';

const VIEW_KEY = 'small-hours.status-view.v1';
const tasks = [
  { id: 'a', title: 'Plan release', details: '', status: 'todo' },
  { id: 'b', title: 'Review copy', details: '', status: 'in-progress' },
  { id: 'c', title: 'Publish notes', details: '', status: 'done' },
  { id: 'd', title: 'Book room', details: '', status: 'todo' },
];

function control<T extends HTMLElement>(label: string): T {
  const explicit = Array.from(document.querySelectorAll('label')).find((node) => node.textContent === label);
  const node = explicit ? document.getElementById(explicit.htmlFor) : document.querySelector(`[aria-label="${label}"]`);
  if (!node) throw new Error(`Missing labeled control: ${label}`);
  return node as T;
}

function mount(storage?: StorageAccess): void {
  mountTaskboard(document.querySelector<HTMLElement>('#app')!, storage);
}

function change(label: string, value: string): HTMLSelectElement {
  const select = control<HTMLSelectElement>(label);
  select.focus();
  select.value = value;
  select.dispatchEvent(new Event('change', { bubbles: true }));
  return select;
}

function titles(): (string | null)[] {
  return Array.from(document.querySelectorAll('article h3'), (node) => node.textContent);
}

describe('saved status view through the DOM and storage boundary', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(TASKS_KEY, JSON.stringify(tasks));
    document.body.innerHTML = '<div id="app"></div>';
  });

  it('offers exact native choices, filters without changing saved tasks, and keeps view focus', () => {
    mount();
    const view = control<HTMLSelectElement>('Status view');
    expect(view.tagName).toBe('SELECT');
    expect(Array.from(view.options, ({ textContent, value }) => [textContent, value])).toEqual([
      ['All statuses', 'all'], ['To do', 'todo'], ['In progress', 'in-progress'], ['Done', 'done'],
    ]);
    for (const [value, expected] of [
      ['todo', ['Plan release', 'Book room']], ['in-progress', ['Review copy']],
      ['done', ['Publish notes']], ['all', tasks.map((task) => task.title)],
    ] as const) {
      change('Status view', value);
      expect(titles()).toEqual(expected);
      expect(document.activeElement).toBe(view);
    }
    expect(JSON.parse(localStorage.getItem(TASKS_KEY)!)).toEqual(tasks);
  });

  it.each(['all', 'todo', 'in-progress', 'done'])('restores the supported saved view %s', (value) => {
    localStorage.setItem(VIEW_KEY, JSON.stringify(value));
    mount();
    expect(control<HTMLSelectElement>('Status view').value).toBe(value);
    expect(titles()).toEqual(tasks.filter((task) => value === 'all' || task.status === value).map((task) => task.title));
  });

  it.each([null, '{', 'null', '{}', '[]', 'true', '1', '"obsolete"', '"TODO"'])('falls back safely for saved selection %s', (raw) => {
    if (raw !== null) localStorage.setItem(VIEW_KEY, raw);
    mount();
    expect(control<HTMLSelectElement>('Status view').value).toBe('all');
    expect(titles()).toEqual(tasks.map((task) => task.title));
    expect(JSON.parse(localStorage.getItem(TASKS_KEY)!)).toEqual(tasks);
  });

  it('saves the preference independently and restores it on a later mount', () => {
    mount();
    change('Status view', 'in-progress');
    expect(localStorage.getItem(VIEW_KEY)).toBe('"in-progress"');
    expect(document.querySelector('#task-count')?.textContent).toBe('1 of 4 tasks');
    mount();
    expect(control<HTMLSelectElement>('Status view').value).toBe('in-progress');
    expect(titles()).toEqual(['Review copy']);
  });

  it('recovers a preference read failure without affecting task data', () => {
    mount(() => ({
      getItem: (key) => { if (key === VIEW_KEY) throw new Error('Blocked preference'); return localStorage.getItem(key); },
      setItem: (key, value) => localStorage.setItem(key, value),
    }));
    expect(control<HTMLSelectElement>('Status view').value).toBe('all');
    expect(titles()).toEqual(tasks.map((task) => task.title));
    change('Status view', 'done');
    expect(titles()).toEqual(['Publish notes']);
  });

  it('keeps a failed preference write usable and explains its persistence separately from task writes', () => {
    mount(() => ({
      getItem: (key) => localStorage.getItem(key),
      setItem: (key, value) => { if (key === VIEW_KEY) throw new Error('Full preference'); localStorage.setItem(key, value); },
    }));
    change('Status view', 'todo');
    expect(titles()).toEqual(['Plan release', 'Book room']);
    expect(document.querySelector('#view-warning')?.textContent).toMatch(/until.*reload/i);
    change('Move Plan release', 'done');
    expect(titles()).toEqual(['Book room']);
    expect(control<HTMLSelectElement>('Status view').value).toBe('todo');
    expect(document.querySelector<HTMLElement>('#view-warning')?.hidden).toBe(false);
    expect(JSON.parse(localStorage.getItem(TASKS_KEY)!)[0].status).toBe('done');
    mount();
    expect(control<HTMLSelectElement>('Status view').value).toBe('all');
  });

  it('clears preference failure feedback after a successful retry', () => {
    let blocked = true;
    mount(() => ({
      getItem: (key) => localStorage.getItem(key),
      setItem: (key, value) => { if (key === VIEW_KEY && blocked) throw new Error('Full'); localStorage.setItem(key, value); },
    }));
    change('Status view', 'done');
    blocked = false;
    change('Status view', 'todo');
    expect(document.querySelector<HTMLElement>('#view-warning')?.hidden).toBe(true);
    expect(localStorage.getItem(VIEW_KEY)).toBe('"todo"');
  });

  it('restores focus after moving the final match out of view and keeps it saved', () => {
    mount();
    change('Status view', 'in-progress');
    change('Move Review copy', 'done');
    expect(titles()).toEqual([]);
    expect(document.body.textContent).toContain('No tasks in this view.');
    expect(document.activeElement).toBe(control('Status view'));
    change('Status view', 'done');
    expect(titles()).toEqual(['Review copy', 'Publish notes']);
  });

  it('restores deletion focus using the visible order even when hidden tasks come first', () => {
    mount();
    change('Status view', 'todo');
    const last = document.querySelectorAll('article')[1]!;
    last.querySelectorAll<HTMLButtonElement>('button')[1]!.click();
    expect(document.activeElement?.closest('article')?.getAttribute('aria-labelledby')).toBe('task-a');
    document.querySelectorAll<HTMLButtonElement>('article button')[1]!.click();
    expect(titles()).toEqual([]);
    expect(document.activeElement?.tagName).not.toBe('BODY');
    expect(document.querySelector<HTMLElement>('#view-empty-state')?.hidden).toBe(false);
    expect(document.querySelector<HTMLElement>('#empty-state')?.hidden).toBe(true);
  });

  it('keeps the existing all-board empty behavior under every selection', () => {
    localStorage.setItem(TASKS_KEY, '[]');
    mount();
    for (const value of ['all', 'todo']) {
      change('Status view', value);
      expect(document.querySelector<HTMLElement>('#empty-state')?.hidden).toBe(false);
      expect(document.querySelector<HTMLElement>('#view-empty-state')?.hidden).toBe(true);
    }
  });
});
