let _backendUrl = null;

export async function getBackendUrl() {
  if (_backendUrl) return _backendUrl;

  if (window.electronAPI) {
    _backendUrl = await window.electronAPI.getBackendUrl();
  } else {
    _backendUrl = 'http://localhost:8000';
  }

  return _backendUrl;
}

export async function apiUrl(path) {
  const base = await getBackendUrl();
  return `${base}${path}`;
}
