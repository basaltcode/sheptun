const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const { findFreePort } = require('./portFinder');
const { findPython, ensureVenv, getVenvPython, getBackendDir } = require('./pythonManager');

let mainWindow;
let backendProcess;
let backendPort;

const isDev = !app.isPackaged;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Whisper Транскрибация',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'frontend', 'dist', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function waitForBackend(port, timeoutMs = 30000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    function check() {
      if (Date.now() - start > timeoutMs) {
        return reject(new Error('Backend did not start in time'));
      }
      const req = http.get(`http://127.0.0.1:${port}/docs`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          setTimeout(check, 500);
        }
      });
      req.on('error', () => setTimeout(check, 500));
      req.setTimeout(2000, () => {
        req.destroy();
        setTimeout(check, 500);
      });
    }
    check();
  });
}

async function startBackend() {
  backendPort = await findFreePort();

  const pythonCmd = findPython();
  if (!pythonCmd) {
    dialog.showErrorBox(
      'Python не найден',
      'Для работы приложения необходим Python 3.8+.\n\n' +
      'Установите Python:\n' +
      '- macOS: brew install python3\n' +
      '- Windows: https://python.org/downloads\n' +
      '- Linux: sudo apt install python3 python3-venv'
    );
    app.quit();
    return;
  }

  try {
    await ensureVenv(pythonCmd, (msg) => {
      if (mainWindow) {
        mainWindow.setTitle(`Whisper — ${msg}`);
      }
    });
  } catch (err) {
    dialog.showErrorBox(
      'Ошибка установки зависимостей',
      `Не удалось установить Python-зависимости:\n${err.message}`
    );
    app.quit();
    return;
  }

  const venvPython = getVenvPython();
  const backendDir = getBackendDir();

  backendProcess = spawn(venvPython, [
    '-m', 'uvicorn', 'main:app',
    '--host', '127.0.0.1',
    '--port', String(backendPort),
  ], {
    cwd: backendDir,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[backend] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[backend] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`Backend exited with code ${code}`);
    backendProcess = null;
  });

  try {
    await waitForBackend(backendPort);
  } catch (err) {
    dialog.showErrorBox(
      'Ошибка запуска бэкенда',
      'Не удалось запустить серверную часть приложения.\nПопробуйте перезапустить.'
    );
    app.quit();
  }
}

function killBackend() {
  if (!backendProcess) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(backendProcess.pid), '/f', '/t']);
  } else {
    backendProcess.kill('SIGTERM');
  }
  backendProcess = null;
}

ipcMain.handle('get-backend-url', () => {
  return `http://127.0.0.1:${backendPort}`;
});

app.whenReady().then(async () => {
  createWindow();
  await startBackend();

  if (mainWindow) {
    mainWindow.setTitle('Whisper Транскрибация');
    if (!isDev) {
      mainWindow.reload();
    }
  }
});

app.on('window-all-closed', () => {
  killBackend();
  app.quit();
});

app.on('before-quit', () => {
  killBackend();
});
