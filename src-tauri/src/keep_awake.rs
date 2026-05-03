use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

pub struct KeepAwake {
    child: Mutex<Option<Child>>,
}

impl KeepAwake {
    pub const fn new() -> Self {
        Self {
            child: Mutex::new(None),
        }
    }

    pub fn enable(&self) -> Result<(), String> {
        let mut guard = self.child.lock().unwrap();
        if let Some(child) = guard.as_mut() {
            if matches!(child.try_wait(), Ok(None)) {
                return Ok(());
            }
        }
        let child = spawn_inhibitor()?;
        *guard = Some(child);
        Ok(())
    }

    pub fn disable(&self) {
        let mut guard = self.child.lock().unwrap();
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

impl Drop for KeepAwake {
    fn drop(&mut self) {
        self.disable();
    }
}

#[cfg(target_os = "macos")]
fn spawn_inhibitor() -> Result<Child, String> {
    Command::new("caffeinate")
        .args(["-dis"])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("failed to spawn caffeinate: {e}"))
}

#[cfg(target_os = "linux")]
fn spawn_inhibitor() -> Result<Child, String> {
    Command::new("systemd-inhibit")
        .args([
            "--what=sleep:idle",
            "--who=Sheptun",
            "--why=Transcription in progress",
            "--mode=block",
            "sleep",
            "infinity",
        ])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("failed to spawn systemd-inhibit: {e}"))
}

#[cfg(target_os = "windows")]
fn spawn_inhibitor() -> Result<Child, String> {
    // ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED = 0x80000003
    let script = "Add-Type -Name P -Namespace W -MemberDefinition '[System.Runtime.InteropServices.DllImport(\"kernel32.dll\")] public static extern uint SetThreadExecutionState(uint e);'; [W.P]::SetThreadExecutionState(2147483651) | Out-Null; while($true) { Start-Sleep -Seconds 60 }";
    Command::new("powershell")
        .args(["-NoProfile", "-WindowStyle", "Hidden", "-Command", script])
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("failed to spawn powershell: {e}"))
}

#[cfg(not(any(target_os = "macos", target_os = "linux", target_os = "windows")))]
fn spawn_inhibitor() -> Result<Child, String> {
    Err("keep-awake not supported on this platform".to_string())
}
