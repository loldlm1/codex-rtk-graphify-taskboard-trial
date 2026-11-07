import { isTask, seedTasks, statuses } from './tasks';
import type { Status, Task } from './tasks';
export const TASKS_KEY = 'small-hours.tasks.v1';
export const STATUS_VIEW_KEY = 'small-hours.status-view.v1';
export type StatusView = 'all' | Status;
export type StorageAccess = () => Pick<Storage, 'getItem' | 'setItem'>;

export function loadStatusView(storage: StorageAccess): StatusView {
  try {
    const raw = storage().getItem(STATUS_VIEW_KEY);
    const parsed: unknown = raw === null ? null : JSON.parse(raw);
    return parsed === 'all' || statuses.some(({ value }) => value === parsed) ? parsed as StatusView : 'all';
  } catch {
    return 'all';
  }
}

export function saveStatusView(storage: StorageAccess, view: StatusView): boolean {
  try {
    storage().setItem(STATUS_VIEW_KEY, JSON.stringify(view));
    return true;
  } catch {
    return false;
  }
}

export function loadTasks(storage: StorageAccess): { tasks: Task[]; warning: string } {
  try {
    const raw = storage().getItem(TASKS_KEY);
    if (raw === null) return { tasks: seedTasks(), warning: '' };
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.every(isTask) ||
        new Set(parsed.map((task) => task.id)).size !== parsed.length) throw new Error('Invalid tasks');
    return { tasks: parsed, warning: '' };
  } catch {
    return { tasks: seedTasks(), warning: 'We could not read your saved tasks. Showing the sample board. Changes stay in this tab if storage is unavailable.' };
  }
}

export function saveTasks(storage: StorageAccess, tasks: Task[]): boolean {
  try {
    storage().setItem(TASKS_KEY, JSON.stringify(tasks));
    return true;
  } catch {
    return false;
  }
}
