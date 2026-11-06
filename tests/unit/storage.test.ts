import { beforeEach, describe, expect, it } from 'vitest';
import { loadTasks, saveTasks, TASKS_KEY } from '../../src/storage';
import { seedTasks } from '../../src/tasks';

describe('task persistence', () => {
  beforeEach(() => localStorage.clear());
  const storage = () => localStorage;

  it('seeds a new board, round-trips edits, and preserves an empty saved board', () => {
    expect(loadTasks(storage)).toEqual({ tasks: seedTasks(), warning: '' });
    const tasks = seedTasks().slice(0, 2);
    expect(saveTasks(storage, tasks)).toBe(true);
    expect(loadTasks(storage)).toEqual({ tasks, warning: '' });
    expect(saveTasks(storage, [])).toBe(true);
    expect(loadTasks(storage).tasks).toEqual([]);
  });

  it.each(['{', 'null', '{}', '[{"id":"bad"}]'])('recovers malformed task storage %s', (raw) => {
    localStorage.setItem(TASKS_KEY, raw);
    expect(loadTasks(storage).tasks).toEqual(seedTasks());
    expect(loadTasks(storage).warning).toMatch(/could not read/i);
  });

  it('rejects duplicate identities instead of rendering ambiguous controls', () => {
    const task = seedTasks()[0]!;
    localStorage.setItem(TASKS_KEY, JSON.stringify([task, task]));
    expect(loadTasks(storage).warning).not.toBe('');
  });

  it('handles blocked storage access and failed writes', () => {
    const blocked = () => { throw new Error('Blocked'); };
    expect(loadTasks(blocked).tasks).toEqual(seedTasks());
    expect(loadTasks(blocked).warning).toMatch(/could not read/i);
    expect(saveTasks(blocked, [])).toBe(false);
    expect(saveTasks(() => ({ getItem: () => null, setItem: () => { throw new Error('Full'); } }), [])).toBe(false);
  });
});
