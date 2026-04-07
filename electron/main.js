const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');
const { findFreePort } = require('./portFinder');

let mainWindow;
let backendProcess;
let backendPort;

const isDev = !app.isPackaged;

function getBackendPath() {
  if (isDev) {
    // In dev mode, use Python directly
    return null;
  }

  const platform = process.platform;
  const binaryName = platform === 'win32' ? 'sheptun-backend.exe' : 'sheptun-backend';
  return path.join(process.resourcesPath, 'backend', binaryName);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: 'Sheptun',
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

function waitForBackend(port, timeoutMs = 60000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    function check() {
      if (Date.now() - start > timeoutMs) {
        return reject(new Error('Backend did not start in time'));
      }
      const req = http.get(`http://127.0.0.1:${port}/`, (res) => {
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

  const backendBinary = getBackendPath();

  if (isDev) {
    // Dev mode: use pythonManager
    const { findPython, ensureVenv, getVenvPython, getBackendDir } = require('./pythonManager');

    const pythonCmd = findPython();
    if (!pythonCmd) {
      dialog.showErrorBox(
        'Python не найден',
        'Для режима разработки необходим Python 3.8+.'
      );
      app.quit();
      return;
    }

    try {
      await ensureVenv(pythonCmd, (msg) => {
        if (mainWindow) mainWindow.setTitle(`Sheptun — ${msg}`);
      });
    } catch (err) {
      dialog.showErrorBox('Ошибка установки зависимостей', err.message);
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
  } else {
    // Production: use bundled binary
    if (!fs.existsSync(backendBinary)) {
      dialog.showErrorBox(
        'Ошибка',
        `Файл бэкенда не найден: ${backendBinary}`
      );
      app.quit();
      return;
    }

    backendProcess = spawn(backendBinary, [
      '--host', '127.0.0.1',
      '--port', String(backendPort),
    ], {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, SHEPTUN_PORT: String(backendPort) },
    });
  }

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
      'Ошибка запуска',
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
    mainWindow.setTitle('Sheptun');
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
