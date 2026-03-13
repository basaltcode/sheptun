const { spawnSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const { app } = require('electron');

function getBackendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend');
  }
  return path.join(__dirname, '..', 'backend');
}

function getVenvDir() {
  return path.join(app.getPath('userData'), 'venv');
}

function getVenvPython() {
  const venvDir = getVenvDir();
  return process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');
}

function getVenvPip() {
  const venvDir = getVenvDir();
  return process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'pip.exe')
    : path.join(venvDir, 'bin', 'pip');
}

function findPython() {
  const candidates = process.platform === 'win32'
    ? ['python3', 'python', 'py']
    : ['python3', '/usr/bin/python3', '/usr/local/bin/python3', 'python'];

  for (const cmd of candidates) {
    try {
      const result = spawnSync(cmd, ['--version'], {
        timeout: 5000,
        encoding: 'utf-8',
      });
      if (result.status === 0) {
        const output = (result.stdout || result.stderr || '').trim();
        const match = output.match(/Python (\d+)\.(\d+)/);
        if (match && parseInt(match[1]) >= 3 && parseInt(match[2]) >= 8) {
          return cmd;
        }
      }
    } catch (e) {
      continue;
    }
  }
  return null;
}

function runCommand(cmd, args, cwd) {
  return new Promise((resolve, reject) => {
    const proc = spawn(cmd, args, {
      cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
    });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (d) => (stdout += d));
    proc.stderr.on('data', (d) => (stderr += d));
    proc.on('close', (code) => {
      if (code === 0) resolve(stdout);
      else reject(new Error(`Command failed (${code}): ${stderr}`));
    });
    proc.on('error', reject);
  });
}

async function ensureVenv(pythonCmd, onProgress) {
  const venvDir = getVenvDir();
  const markerFile = path.join(venvDir, '.deps-installed');

  if (fs.existsSync(markerFile)) {
    return;
  }

  if (!fs.existsSync(venvDir)) {
    if (onProgress) onProgress('Создание Python окружения...');
    await runCommand(pythonCmd, ['-m', 'venv', venvDir]);
  }

  if (onProgress) onProgress('Установка зависимостей (может занять несколько минут)...');

  const pip = getVenvPip();
  const reqPath = path.join(getBackendDir(), 'requirements.txt');
  await runCommand(pip, ['install', '-r', reqPath]);

  fs.writeFileSync(markerFile, new Date().toISOString());
}

module.exports = { findPython, ensureVenv, getVenvPython, getBackendDir };
