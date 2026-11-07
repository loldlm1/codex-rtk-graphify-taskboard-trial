import { createTask, removeTask, statuses, updateTask } from './tasks';
import type { Status, Task, TaskInput } from './tasks';
import { loadStatusView, loadTasks, saveStatusView, saveTasks } from './storage';
import type { StatusView, StorageAccess } from './storage';

function element<K extends keyof HTMLElementTagNameMap>(tag: K, className = '', text = ''): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

function statusSelect(): HTMLSelectElement {
  const select = element('select');
  for (const { value, label } of statuses) {
    const option = element('option', '', label);
    option.value = value;
    select.append(option);
  }
  return select;
}

export function mountTaskboard(root: HTMLElement, storage: StorageAccess = () => window.localStorage): void {
  const loaded = loadTasks(storage);
  let tasks = loaded.tasks;
  let view = loadStatusView(storage);
  let editingId: string | null = null;

  // This template is fixed markup. All task content is assigned with textContent/value.
  root.innerHTML = `
    <a class="skip-link" href="#task-title">Skip to new task</a>
    <div class="workspace">
      <header class="site-header">
        <a class="brand" href="./" aria-label="Small Hours home"><span class="brand-mark" aria-hidden="true">sh<span>✦</span></span><span>small hours<span class="brand-caption">A little space for your plans</span></span></a>
        <span class="device-note"><span aria-hidden="true">●</span> Just here, on your device</span>
      </header>
      <main>
        <section class="intro" aria-labelledby="page-title">
          <p class="eyebrow">YOUR WORK, A LITTLE LIGHTER</p>
          <h1 id="page-title">Make room for <br>good work.</h1>
          <p class="intro-copy">Big ideas. Small steps. A calm place to keep things moving.</p>
          <div class="intro-decoration" aria-hidden="true">✳</div>
        </section>
        <p id="storage-warning" class="notice" role="alert" hidden></p>
        <div class="board-layout">
          <aside class="composer" aria-labelledby="form-heading">
            <div class="section-kicker"><span aria-hidden="true">+</span> ONE SMALL STEP</div>
            <h2 id="form-heading">New task</h2>
            <p class="composer-copy">Get it out of your head and onto the board.</p>
            <form id="task-form">
              <label for="task-title">Task title <span aria-hidden="true">*</span></label>
              <input id="task-title" name="title" required maxlength="100" placeholder="What would you like to do?" aria-describedby="form-error">
              <label for="task-details">Details <span class="optional" aria-hidden="true">optional</span></label>
              <textarea id="task-details" name="details" rows="3" maxlength="500" placeholder="A little more context…"></textarea>
              <label for="task-status">Status</label>
              <div id="form-status"></div>
              <p id="form-error" class="form-error" aria-live="polite"></p>
              <button id="save-task" class="primary-button" type="submit"><span>Add task</span><span aria-hidden="true">↗</span></button>
              <button id="cancel-edit" class="cancel-button" type="button" hidden>Cancel editing</button>
            </form>
            <p class="composer-footnote">A little progress is still progress.</p>
          </aside>
          <section class="board" aria-labelledby="board-heading">
            <div class="board-heading"><div><p class="eyebrow">THE BIG PICTURE</p><h2 id="board-heading">Work in motion<span class="heading-dot">.</span></h2></div><span id="task-count" class="task-count"></span></div>
            <div id="board-stats" class="board-stats" aria-label="Task totals"></div>
            <div id="view-control" class="view-control"><label for="status-view">Status view</label></div>
            <p id="view-warning" class="notice" role="alert" hidden></p>
            <div id="task-list" class="task-list"></div>
            <div id="view-empty-state" class="empty-state" hidden><h3>No tasks in this view.</h3><p>Choose another status view or add a task to keep things moving.</p></div>
            <div id="empty-state" class="empty-state" hidden><span aria-hidden="true">✧</span><h3>A clear board. A fresh start.</h3><p>Add a task when you're ready for the next small step.</p></div>
          </section>
        </div>
        <p id="announcement" class="sr-only" role="status" aria-live="polite"></p>
      </main>
      <footer class="site-footer"><span>Make a little space. Do a little good.</span><span>SMALL HOURS / YOUR PERSONAL WORKSPACE</span></footer>
    </div>`;

  const get = <T extends HTMLElement>(selector: string) => root.querySelector<T>(selector)!;
  const form = get<HTMLFormElement>('#task-form');
  const title = get<HTMLInputElement>('#task-title');
  const details = get<HTMLTextAreaElement>('#task-details');
  const inputStatus = statusSelect();
  inputStatus.id = 'task-status';
  inputStatus.name = 'status';
  get('#form-status').append(inputStatus);
  const viewSelect = statusSelect();
  viewSelect.id = 'status-view';
  viewSelect.name = 'status-view';
  const allOption = element('option', '', 'All statuses');
  allOption.value = 'all';
  viewSelect.prepend(allOption);
  viewSelect.value = view;
  get('#view-control').append(viewSelect);
  viewSelect.addEventListener('change', () => {
    view = viewSelect.value as StatusView;
    const saved = saveStatusView(storage, view);
    const viewWarning = get('#view-warning');
    viewWarning.hidden = saved;
    viewWarning.textContent = saved ? '' : 'Your status view is available in this tab until you reload. Browser storage is unavailable, so it could not be saved.';
    render();
  });
  const warning = get('#storage-warning');
  warning.textContent = loaded.warning;
  warning.hidden = !loaded.warning;

  function resetForm(): void {
    editingId = null;
    form.reset();
    title.removeAttribute('aria-invalid');
    get('#form-error').textContent = '';
    get('#form-heading').textContent = 'New task';
    get('#save-task span').textContent = 'Add task';
    get('#cancel-edit').hidden = true;
  }

  function persist(message: string): void {
    const saved = saveTasks(storage, tasks);
    warning.hidden = saved;
    warning.textContent = saved ? '' : 'Your changes are available in this tab until you reload. Browser storage is unavailable, so they could not be saved.';
    get('#announcement').textContent = message;
  }

  function edit(task: Task): void {
    editingId = task.id;
    title.value = task.title;
    details.value = task.details;
    inputStatus.value = task.status;
    title.removeAttribute('aria-invalid');
    get('#form-error').textContent = '';
    get('#form-heading').textContent = 'Edit task';
    get('#save-task span').textContent = 'Save task';
    get('#cancel-edit').hidden = false;
    title.focus();
  }

  function render(): void {
    const visibleTasks = tasks.filter((task) => view === 'all' || task.status === view);
    get('#task-count').textContent = `${view === 'all' ? tasks.length : `${visibleTasks.length} of ${tasks.length}`} ${tasks.length === 1 ? 'task' : 'tasks'}`;
    const stats = get('#board-stats');
    stats.replaceChildren(...statuses.map(({ value, label }) => {
      const stat = element('span', `stat stat-${value}`);
      stat.append(element('span', 'stat-dot'), document.createTextNode(`${label} `), element('strong', '', String(tasks.filter((task) => task.status === value).length)));
      return stat;
    }));
    const list = get('#task-list');
    list.replaceChildren();
    get('#empty-state').hidden = tasks.length > 0;
    get('#view-empty-state').hidden = tasks.length === 0 || visibleTasks.length > 0;
    for (const task of visibleTasks) {
      const card = element('article', 'task-card');
      const heading = element('h3', '', task.title);
      heading.id = `task-${task.id}`;
      card.setAttribute('aria-labelledby', heading.id);
      const label = statuses.find(({ value }) => value === task.status)!.label;
      const badge = element('span', `status-badge badge-${task.status}`, label);
      card.append(badge, heading);
      if (task.details) card.append(element('p', 'task-details', task.details));
      const actions = element('div', 'task-actions');
      const editButton = element('button', 'text-button', 'Edit');
      editButton.type = 'button';
      editButton.addEventListener('click', () => edit(task));
      const deleteButton = element('button', 'text-button delete-button', 'Delete');
      deleteButton.type = 'button';
      deleteButton.addEventListener('click', () => {
        const index = visibleTasks.findIndex(({ id }) => id === task.id);
        tasks = removeTask(tasks, task.id);
        if (editingId === task.id) resetForm();
        persist(`“${task.title}” deleted.`);
        render();
        const editButtons = root.querySelectorAll<HTMLButtonElement>('.task-card .task-actions button:first-child');
        const next = editButtons[Math.min(index, editButtons.length - 1)];
        (next ?? title).focus();
      });
      actions.append(editButton, deleteButton);
      const move = statusSelect();
      move.value = task.status;
      move.setAttribute('aria-label', `Move ${task.title}`);
      move.addEventListener('change', () => {
        tasks = updateTask(tasks, task.id, { ...task, status: move.value as Status });
        persist(`“${task.title}” moved to ${statuses.find(({ value }) => value === move.value)!.label}.`);
        render();
        const movedSelect = root.ownerDocument.getElementById(`task-${task.id}`)?.closest('article')?.querySelector('select');
        (movedSelect ?? viewSelect).focus();
      });
      const footer = element('div', 'card-footer');
      footer.append(actions, move);
      card.append(footer);
      list.append(card);
    }
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const input: TaskInput = { title: title.value, details: details.value, status: inputStatus.value as Status };
    try {
      const wasEditing = editingId !== null;
      tasks = editingId ? updateTask(tasks, editingId, input) : [createTask(input, crypto.randomUUID()), ...tasks];
      persist(`“${input.title.trim()}” ${wasEditing ? 'saved' : 'created'}.`);
      resetForm();
      render();
      title.focus();
    } catch (error) {
      get('#form-error').textContent = (error as Error).message;
      title.setAttribute('aria-invalid', 'true');
      title.focus();
    }
  });
  get('#cancel-edit').addEventListener('click', () => { resetForm(); title.focus(); });
  render();
}
