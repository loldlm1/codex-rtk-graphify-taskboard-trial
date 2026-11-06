import { describe, expect, it } from 'vitest';
import { createTask, updateTask, removeTask, isTask, seedTasks } from '../../src/tasks';

describe('task operations', () => {
  const input = { title: '  Plan the garden  ', details: '  Sketch the beds.  ', status: 'todo' as const };

  it('creates normalized tasks and preserves the supplied identity', () => {
    expect(createTask(input, 'new')).toEqual({ id: 'new', title: 'Plan the garden', details: 'Sketch the beds.', status: 'todo' });
  });

  it.each(['', '   ', 'x'.repeat(101)])('rejects an invalid title %j', (title) => {
    expect(() => createTask({ ...input, title }, 'new')).toThrow(/title/i);
  });

  it('rejects oversized details and unknown statuses', () => {
    expect(() => createTask({ ...input, details: 'x'.repeat(501) }, 'new')).toThrow(/details/i);
    expect(() => createTask({ ...input, status: 'unknown' as 'todo' }, 'new')).toThrow(/status/i);
  });

  it('edits only the chosen task without mutating the original list', () => {
    const tasks = seedTasks();
    const first = tasks[0]!;
    const edited = updateTask(tasks, first.id, { title: 'Revised plan', details: '', status: 'done' });
    expect(edited[0]).toEqual({ id: first.id, title: 'Revised plan', details: '', status: 'done' });
    expect(edited.slice(1)).toEqual(tasks.slice(1));
    expect(tasks[0]).toEqual(first);
  });

  it('removes one task, permits an empty board, and rejects stale identities', () => {
    const task = createTask(input, 'only');
    expect(removeTask([task], task.id)).toEqual([]);
    expect(() => updateTask([], 'missing', input)).toThrow(/no longer/i);
    expect(() => removeTask([], 'missing')).toThrow(/no longer/i);
  });

  it('recognizes only valid persisted tasks and returns fresh seed data', () => {
    for (const invalid of [null, 2, {}, { id: '', ...input }, { id: 'a', ...input, title: null }, { id: 'a', ...input, details: null }, { id: 'a', ...input, status: 'bad' }]) {
      expect(isTask(invalid)).toBe(false);
    }
    const first = seedTasks();
    expect(first.length).toBe(6);
    expect(first.every(isTask)).toBe(true);
    expect(new Set(first.map((task) => task.status))).toEqual(new Set(['todo', 'in-progress', 'done']));
    first[0]!.title = 'Changed';
    expect(seedTasks()[0]!.title).not.toBe('Changed');
  });
});
