use std::sync::{atomic::Ordering, Arc};

use tauri::State;

use crate::backend::BackendState;
use crate::keep_awake::KeepAwake;

#[tauri::command]
pub fn get_backend_url(state: State<Arc<BackendState>>) -> String {
    let port = state.port.load(Ordering::SeqCst);
    format!("http://127.0.0.1:{port}")
}

#[tauri::command]
pub fn get_backend_logs(state: State<Arc<BackendState>>) -> String {
    state.logs_snapshot().join("")
}

#[tauri::command]
pub fn set_keep_awake(enabled: bool, state: State<Arc<KeepAwake>>) -> Result<(), String> {
    if enabled {
        state.enable()
    } else {
        state.disable();
        Ok(())
    }
}
