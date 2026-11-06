import { beforeEach, describe, expect, it } from 'vitest';
import { loadStatusView, saveStatusView, TASKS_KEY } from '../../src/storage';

const VIEW_KEY = 'small-hours.status-view.v1';
const storage = () => localStorage;

describe('status view preference boundary', () => {
  beforeEach(() => localStorage.clear());

  it.each(['all', 'todo', 'in-progress', 'done'] as const)('round-trips %s separately from task data', (view) => {
    localStorage.setItem(TASKS_KEY, 'existing task bytes');
    expect(saveStatusView(storage, view)).toBe(true);
    expect(localStorage.getItem(VIEW_KEY)).toBe(JSON.stringify(view));
    expect(loadStatusView(storage)).toBe(view);
    expect(localStorage.getItem(TASKS_KEY)).toBe('existing task bytes');
  });

  it.each([null, '{', 'null', '{}', '[]', '1', 'true', '"obsolete"', '""', '" todo "'])('falls back for missing or invalid preference %s', (raw) => {
    if (raw !== null) localStorage.setItem(VIEW_KEY, raw);
    expect(loadStatusView(storage)).toBe('all');
    expect(localStorage.getItem(VIEW_KEY)).toBe(raw);
  });

  it('handles access, read and write failures without throwing', () => {
    const blocked = () => { throw new Error('Blocked'); };
    expect(loadStatusView(blocked)).toBe('all');
    expect(saveStatusView(blocked, 'done')).toBe(false);
    expect(loadStatusView(() => ({ getItem: () => { throw new Error('Unreadable'); }, setItem: () => {} }))).toBe('all');
    expect(saveStatusView(() => ({ getItem: () => null, setItem: () => { throw new Error('Full'); } }), 'todo')).toBe(false);
  });
});
