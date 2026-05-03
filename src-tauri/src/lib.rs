mod backend;
mod commands;
mod keep_awake;
mod python;

use std::sync::Arc;

use tauri::{Manager, RunEvent, WindowEvent};

use crate::backend::BackendState;
use crate::keep_awake::KeepAwake;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .setup(|app| {
            let state = Arc::new(BackendState::new());
            app.manage(state.clone());

            let keep_awake = Arc::new(KeepAwake::new());
            app.manage(keep_awake.clone());

            if let Some(window) = app.get_webview_window("main") {
                let handle_for_close = app.handle().clone();
                window.on_window_event(move |event| {
                    if matches!(event, WindowEvent::CloseRequested { .. }) {
                        if let Some(state) = handle_for_close.try_state::<Arc<BackendState>>() {
                            state.kill();
                        }
                        if let Some(ka) = handle_for_close.try_state::<Arc<KeepAwake>>() {
                            ka.disable();
                        }
                        handle_for_close.exit(0);
                    }
                });
            }

            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                match backend::spawn_and_wait(&handle, state.clone()).await {
                    Ok(()) => {
                        if let Some(window) = handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    Err(err) => {
                        let logs = state.logs_snapshot().join("");
                        let message = format!(
                            "Не удалось запустить серверную часть приложения.\n\n{err}\n\nЛоги:\n{logs}"
                        );
                        log::error!("{message}");
                        eprintln!("{message}");
                        handle.exit(1);
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_backend_url,
            commands::get_backend_logs,
            commands::set_keep_awake,
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| match event {
            RunEvent::ExitRequested { .. } | RunEvent::Exit => {
                if let Some(state) = app_handle.try_state::<Arc<BackendState>>() {
                    state.kill();
                }
                if let Some(ka) = app_handle.try_state::<Arc<KeepAwake>>() {
                    ka.disable();
                }
            }
            RunEvent::WindowEvent {
                event: WindowEvent::Destroyed | WindowEvent::CloseRequested { .. },
                ..
            } => {
                if let Some(state) = app_handle.try_state::<Arc<BackendState>>() {
                    state.kill();
                }
                if let Some(ka) = app_handle.try_state::<Arc<KeepAwake>>() {
                    ka.disable();
                }
            }
            _ => {}
        });
}
