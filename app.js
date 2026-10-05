/**
 * Клиент приложения «Заметки».
 *
 * Заметки живут в localStorage этого браузера: сеть для чтения и записи не нужна.
 * Service Worker нужен отдельно — он сохраняет саму страницу (HTML, CSS, JS, иконки),
 * чтобы приложение открывалось без подключения.
 */

const STORAGE_KEY = 'notes-pwa';

const noteForm = document.querySelector('#note-form');
const noteInput = document.querySelector('#note-input');
const notesList = document.querySelector('#notes-list');
const notesCount = document.querySelector('#notes-count');
const emptyState = document.querySelector('#empty-state');
const networkStatus = document.querySelector('#network-status');
const swStatus = document.querySelector('#sw-status');
const installButton = document.querySelector('#install-btn');
const fileWarning = document.querySelector('#file-warning');

let deferredInstallPrompt = null;

function loadNotes() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((note) => note && typeof note.text === 'string' && note.id);
  } catch {
    return [];
  }
}

function saveNotes(notes) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(notes));
}

function formatDate(timestamp) {
  return new Date(timestamp).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function renderNotes() {
  const notes = loadNotes();
  notesList.replaceChildren();

  notes.forEach((note) => {
    const item = document.createElement('li');
    item.className = 'task-item';

    const left = document.createElement('div');
    left.className = 'task-item__left';

    const textWrap = document.createElement('div');
    const text = document.createElement('p');
    text.className = 'task-item__text';
    text.textContent = note.text;

    const time = document.createElement('time');
    time.className = 'note-meta';
    time.dateTime = new Date(note.createdAt).toISOString();
    time.textContent = formatDate(note.createdAt);

    textWrap.append(text, time);
    left.append(textWrap);

    const actions = document.createElement('div');
    actions.className = 'task-item__actions';

    const removeButton = document.createElement('button');
    removeButton.className = 'button button--danger button--small';
    removeButton.type = 'button';
    removeButton.dataset.id = note.id;
    removeButton.textContent = 'Удалить';

    actions.append(removeButton);
    item.append(left, actions);
    notesList.append(item);
  });

  notesCount.textContent = `Всего заметок: ${notes.length}`;
  emptyState.hidden = notes.length > 0;
}

function addNote(text) {
  const notes = loadNotes();
  notes.unshift({
    id: crypto.randomUUID(),
    text,
    createdAt: Date.now(),
  });
  saveNotes(notes);
  renderNotes();
}

function removeNote(id) {
  saveNotes(loadNotes().filter((note) => note.id !== id));
  renderNotes();
}

function updateNetworkStatus() {
  const online = navigator.onLine;
  networkStatus.textContent = online ? 'В сети' : 'Офлайн';
  networkStatus.className = online ? 'badge badge--success' : 'badge badge--offline';
}

async function registerServiceWorker() {
  if (location.protocol === 'file:') {
    fileWarning.hidden = false;
    swStatus.textContent = 'Нужен локальный сервер';
    return;
  }

  if (!('serviceWorker' in navigator)) {
    swStatus.textContent = 'SW не поддерживается';
    return;
  }

  try {
    await navigator.serviceWorker.register('/sw.js');
    swStatus.textContent = 'SW зарегистрирован';
  } catch (error) {
    swStatus.textContent = 'SW не зарегистрирован';
    console.error(error);
  }
}

noteForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = noteInput.value.trim();
  if (!text) return;
  addNote(text);
  noteForm.reset();
  noteInput.focus();
});

notesList.addEventListener('click', (event) => {
  const button = event.target.closest('button[data-id]');
  if (!button) return;
  removeNote(button.dataset.id);
});

window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);

window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  installButton.hidden = false;
});

installButton.addEventListener('click', async () => {
  if (!deferredInstallPrompt) return;
  deferredInstallPrompt.prompt();
  await deferredInstallPrompt.userChoice;
  deferredInstallPrompt = null;
  installButton.hidden = true;
});

window.addEventListener('appinstalled', () => {
  installButton.hidden = true;
  deferredInstallPrompt = null;
});

updateNetworkStatus();
renderNotes();
registerServiceWorker();
