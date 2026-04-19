let _backendUrl = null;

function isTauri() {
  return typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__;
}

export async function getBackendUrl() {
  if (_backendUrl) return _backendUrl;

  if (isTauri()) {
    const { invoke } = await import('@tauri-apps/api/core');
    _backendUrl = await invoke('get_backend_url');
  } else {
    _backendUrl = 'http://localhost:8000';
  }

  return _backendUrl;
}

export async function apiUrl(path) {
  const base = await getBackendUrl();
  return `${base}${path}`;
}
