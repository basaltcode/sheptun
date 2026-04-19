use std::collections::VecDeque;
use std::net::TcpListener;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU16, AtomicU32, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

use parking_lot::{Mutex, RwLock};
use tauri::{AppHandle, Manager};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

use crate::python;

const LOG_CAP: usize = 100;
const HEALTH_TIMEOUT: Duration = Duration::from_secs(180);
const HEALTH_INTERVAL: Duration = Duration::from_millis(500);

pub struct BackendState {
    pub port: AtomicU16,
    pid: AtomicU32,
    logs: RwLock<VecDeque<String>>,
    child: Mutex<Option<CommandChild>>,
}

impl BackendState {
    pub fn new() -> Self {
        Self {
            port: AtomicU16::new(0),
            pid: AtomicU32::new(0),
            logs: RwLock::new(VecDeque::with_capacity(LOG_CAP)),
            child: Mutex::new(None),
        }
    }

    pub fn push_log(&self, line: String) {
        let mut logs = self.logs.write();
        if logs.len() >= LOG_CAP {
            logs.pop_front();
        }
        logs.push_back(line);
    }

    pub fn logs_snapshot(&self) -> Vec<String> {
        self.logs.read().iter().cloned().collect()
    }

    pub fn kill(&self) {
        // Take the CommandChild if present and try its kill() first.
        if let Some(child) = self.child.lock().take() {
            let _ = child.kill();
        }
        // Fallback: SIGKILL the stored pid. Covers cases where the CommandChild
        // wrapper's kill is a no-op or the event receiver task has already
        // dropped its handle to the child.
        let pid = self.pid.swap(0, Ordering::SeqCst);
        if pid != 0 {
            #[cfg(unix)]
            unsafe {
                libc::kill(pid as i32, libc::SIGKILL);
            }
            #[cfg(windows)]
            {
                let _ = std::process::Command::new("taskkill")
                    .args(["/PID", &pid.to_string(), "/F", "/T"])
                    .status();
            }
        }
    }

    fn set_child(&self, child: CommandChild) {
        self.pid.store(child.pid(), Ordering::SeqCst);
        *self.child.lock() = Some(child);
    }
}

impl Drop for BackendState {
    fn drop(&mut self) {
        self.kill();
    }
}

fn pick_port() -> Result<u16, String> {
    let listener = TcpListener::bind("127.0.0.1:0")
        .map_err(|e| format!("failed to bind to 127.0.0.1:0: {e}"))?;
    let port = listener
        .local_addr()
        .map_err(|e| format!("failed to read local_addr: {e}"))?
        .port();
    drop(listener);
    Ok(port)
}

fn is_dev() -> bool {
    cfg!(debug_assertions)
}

fn bundled_backend_path(app: &AppHandle) -> Result<PathBuf, String> {
    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("resource_dir: {e}"))?;

    let triple = current_triple();
    #[cfg(windows)]
    let exe_name = format!("sheptun-backend-{triple}.exe");
    #[cfg(not(windows))]
    let exe_name = format!("sheptun-backend-{triple}");

    let candidate = resource_dir
        .join("resources")
        .join("backend")
        .join(&triple)
        .join(&exe_name);

    if candidate.exists() {
        return Ok(candidate);
    }

    // Fallback: some platforms flatten the resources dir
    let alt = resource_dir.join("backend").join(&triple).join(&exe_name);
    if alt.exists() {
        return Ok(alt);
    }

    Err(format!(
        "bundled backend binary not found at {} or {}",
        candidate.display(),
        alt.display()
    ))
}

fn current_triple() -> String {
    let arch = std::env::consts::ARCH;
    match std::env::consts::OS {
        "macos" => match arch {
            "aarch64" => "aarch64-apple-darwin".into(),
            _ => "x86_64-apple-darwin".into(),
        },
        "windows" => "x86_64-pc-windows-msvc".into(),
        "linux" => match arch {
            "aarch64" => "aarch64-unknown-linux-gnu".into(),
            _ => "x86_64-unknown-linux-gnu".into(),
        },
        other => format!("{arch}-unknown-{other}"),
    }
}

pub async fn spawn_and_wait(
    app: &AppHandle,
    state: Arc<BackendState>,
) -> Result<(), String> {
    let port = pick_port()?;
    state.port.store(port, Ordering::SeqCst);

    let (event_rx_handle, child) = if is_dev() {
        spawn_dev(app, port, &state).await?
    } else {
        spawn_prod(app, port, &state)?
    };

    state.set_child(child);

    // event pump task
    let logs_state = state.clone();
    tauri::async_runtime::spawn(async move {
        let mut rx = event_rx_handle;
        while let Some(event) = rx.recv().await {
            match event {
                CommandEvent::Stdout(bytes) | CommandEvent::Stderr(bytes) => {
                    let line = String::from_utf8_lossy(&bytes).to_string();
                    eprint!("[backend] {line}");
                    logs_state.push_log(line);
                }
                CommandEvent::Error(err) => {
                    let line = format!("[backend error] {err}\n");
                    eprint!("{line}");
                    logs_state.push_log(line);
                }
                CommandEvent::Terminated(payload) => {
                    let line = format!(
                        "[backend terminated] code={:?} signal={:?}\n",
                        payload.code, payload.signal
                    );
                    eprint!("{line}");
                    logs_state.push_log(line);
                    break;
                }
                _ => {}
            }
        }
    });

    wait_healthy(port).await
}

async fn spawn_dev(
    app: &AppHandle,
    port: u16,
    state: &Arc<BackendState>,
) -> Result<
    (
        tauri::async_runtime::Receiver<CommandEvent>,
        CommandChild,
    ),
    String,
> {
    let venv = python::ensure_dev_venv(app, |msg| {
        state.push_log(format!("[setup] {msg}\n"));
    })
    .await?;

    let backend_dir = python::dev_backend_dir();
    let python_bin = python::venv_python(&venv);

    let shell = app.shell();
    let cmd = shell
        .command(python_bin)
        .args([
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            &port.to_string(),
        ])
        .current_dir(backend_dir);

    cmd.spawn()
        .map_err(|e| format!("failed to spawn dev backend: {e}"))
}

fn spawn_prod(
    app: &AppHandle,
    port: u16,
    _state: &Arc<BackendState>,
) -> Result<
    (
        tauri::async_runtime::Receiver<CommandEvent>,
        CommandChild,
    ),
    String,
> {
    let binary = bundled_backend_path(app)?;
    let resource_dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("resource_dir: {e}"))?;

    let shell = app.shell();
    let cmd = shell
        .command(binary)
        .args([
            "--host",
            "127.0.0.1",
            "--port",
            &port.to_string(),
        ])
        .env("SHEPTUN_PORT", port.to_string())
        .env("SHEPTUN_RESOURCES_PATH", resource_dir.to_string_lossy().to_string());

    cmd.spawn()
        .map_err(|e| format!("failed to spawn bundled backend: {e}"))
}

async fn wait_healthy(port: u16) -> Result<(), String> {
    let url = format!("http://127.0.0.1:{port}/");
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|e| format!("reqwest client: {e}"))?;

    let start = Instant::now();
    loop {
        if start.elapsed() > HEALTH_TIMEOUT {
            return Err("Backend did not start in time".into());
        }

        match client.get(&url).send().await {
            Ok(resp) if resp.status().is_success() => return Ok(()),
            _ => tokio::time::sleep(HEALTH_INTERVAL).await,
        }
    }
}
