use std::path::{Path, PathBuf};
use std::process::Command;

use tauri::{AppHandle, Manager};

fn dev_project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("src-tauri parent")
        .to_path_buf()
}

pub fn dev_backend_dir() -> PathBuf {
    dev_project_root().join("backend")
}

pub fn venv_python(venv: &Path) -> PathBuf {
    if cfg!(windows) {
        venv.join("Scripts").join("python.exe")
    } else {
        venv.join("bin").join("python")
    }
}

fn venv_pip(venv: &Path) -> PathBuf {
    if cfg!(windows) {
        venv.join("Scripts").join("pip.exe")
    } else {
        venv.join("bin").join("pip")
    }
}

fn find_system_python() -> Option<String> {
    // openai-whisper==20231117 fails to build on Python >=3.13 (setup.py imports
    // pkg_resources, which is no longer auto-injected). Prefer specific 3.9–3.12
    // interpreters first; only fall back to generic names if their version checks out.
    let pinned: &[&str] = &[
        "python3.12",
        "python3.11",
        "python3.10",
        "python3.9",
        "/opt/homebrew/bin/python3.12",
        "/opt/homebrew/bin/python3.11",
        "/opt/homebrew/bin/python3.10",
        "/opt/homebrew/bin/python3.9",
        "/usr/local/bin/python3.12",
        "/usr/local/bin/python3.11",
        "/usr/local/bin/python3.10",
        "/usr/local/bin/python3.9",
    ];
    let generic: &[&str] = if cfg!(windows) {
        &["python3", "python", "py"]
    } else {
        &["python3", "/usr/bin/python3", "/usr/local/bin/python3", "python"]
    };

    for cmd in pinned.iter().chain(generic.iter()) {
        let output = Command::new(cmd).arg("--version").output();
        if let Ok(out) = output {
            if out.status.success() {
                let text = format!(
                    "{}{}",
                    String::from_utf8_lossy(&out.stdout),
                    String::from_utf8_lossy(&out.stderr)
                );
                if let Some((major, minor)) = parse_python_version(&text) {
                    if major == 3 && (9..=12).contains(&minor) {
                        return Some(cmd.to_string());
                    }
                }
            }
        }
    }
    None
}

fn parse_python_version(text: &str) -> Option<(u32, u32)> {
    let rest = text.trim().strip_prefix("Python ")?;
    let mut parts = rest.split('.');
    let major: u32 = parts.next()?.parse().ok()?;
    let minor_raw = parts.next()?;
    let minor: u32 = minor_raw
        .chars()
        .take_while(|c| c.is_ascii_digit())
        .collect::<String>()
        .parse()
        .ok()?;
    Some((major, minor))
}

pub async fn ensure_dev_venv<F>(app: &AppHandle, mut progress: F) -> Result<PathBuf, String>
where
    F: FnMut(&str) + Send,
{
    let data_dir = app
        .path()
        .app_data_dir()
        .map_err(|e| format!("app_data_dir: {e}"))?;
    std::fs::create_dir_all(&data_dir).map_err(|e| format!("create data dir: {e}"))?;

    let venv = data_dir.join("venv");
    let marker = venv.join(".deps-installed");

    if marker.exists() {
        return Ok(venv);
    }

    let python_cmd = find_system_python().ok_or_else(|| {
        "Python 3.8+ не найден в системе. Для режима разработки установите Python.".to_string()
    })?;

    if !venv.exists() {
        progress("Создание Python окружения...");
        let status = Command::new(&python_cmd)
            .args(["-m", "venv"])
            .arg(&venv)
            .status()
            .map_err(|e| format!("failed to create venv: {e}"))?;
        if !status.success() {
            return Err("python -m venv failed".into());
        }
    }

    progress("Установка зависимостей (может занять несколько минут)...");
    let pip = venv_pip(&venv);
    let req = dev_backend_dir().join("requirements.txt");
    let status = Command::new(&pip)
        .args(["install", "-r"])
        .arg(&req)
        .status()
        .map_err(|e| format!("failed to run pip: {e}"))?;
    if !status.success() {
        return Err("pip install failed".into());
    }

    std::fs::write(&marker, chrono_stamp()).map_err(|e| format!("write marker: {e}"))?;
    Ok(venv)
}

fn chrono_stamp() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    format!("installed_at={secs}")
}
