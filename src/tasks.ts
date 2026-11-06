export type Status = 'todo' | 'in-progress' | 'done';
export interface TaskInput { title: string; details: string; status: Status }
export interface Task extends TaskInput { id: string }

export const statuses: { value: Status; label: string }[] = [
  { value: 'todo', label: 'To do' },
  { value: 'in-progress', label: 'In progress' },
  { value: 'done', label: 'Done' },
];

function validate(input: TaskInput): void {
  if (!input.title.trim() || input.title.trim().length > 100) {
    throw new Error('Use a task title between 1 and 100 characters.');
  }
  if (input.details.trim().length > 500) throw new Error('Keep details to 500 characters or fewer.');
  if (!statuses.some(({ value }) => value === input.status)) throw new Error('Choose a valid status.');
}

export function createTask(input: TaskInput, id: string): Task {
  validate(input);
  return { id, title: input.title.trim(), details: input.details.trim(), status: input.status };
}

export function updateTask(tasks: Task[], id: string, input: TaskInput): Task[] {
  if (!tasks.some((task) => task.id === id)) throw new Error('This task is no longer on the board.');
  const updated = createTask(input, id);
  return tasks.map((task) => task.id === id ? updated : task);
}

export function removeTask(tasks: Task[], id: string): Task[] {
  if (!tasks.some((task) => task.id === id)) throw new Error('This task is no longer on the board.');
  return tasks.filter((task) => task.id !== id);
}

export function isTask(value: unknown): value is Task {
  if (typeof value !== 'object' || value === null) return false;
  const task = value as Record<string, unknown>;
  if (typeof task.id !== 'string' || !task.id.trim() ||
      typeof task.title !== 'string' || typeof task.details !== 'string') return false;
  try {
    validate(task as unknown as TaskInput);
    return true;
  } catch {
    return false;
  }
}

export function seedTasks(): Task[] {
  return [
    { id: 'sketch', title: 'Sketch the first ideas', details: 'A notebook, a quiet hour, and a little room to explore.', status: 'todo' },
    { id: 'inspiration', title: 'Gather some inspiration', details: 'Save a few references for the next chapter.', status: 'todo' },
    { id: 'prototype', title: 'Build the prototype', details: 'Turn the most promising idea into something you can try.', status: 'in-progress' },
    { id: 'review', title: 'Review the little details', details: 'Check the copy, spacing, and finishing touches.', status: 'in-progress' },
    { id: 'brief', title: 'Write the project brief', details: 'A clear starting point for the work ahead.', status: 'done' },
    { id: 'workspace', title: 'Set up the workspace', details: 'Everything in its place. Ready when you are.', status: 'done' },
  ];
}
