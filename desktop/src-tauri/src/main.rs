use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use tauri::api::process::{Command, CommandChild, CommandEvent};
use tauri::Manager;

#[derive(Clone)]
struct BackendState {
    url: Arc<Mutex<String>>,
}

#[tauri::command]
fn backend_url(state: tauri::State<BackendState>) -> String {
    state.url.lock().expect("backend url lock poisoned").clone()
}

fn main() {
    let backend: Arc<Mutex<Option<CommandChild>>> = Arc::new(Mutex::new(None));
    let backend_for_exit = Arc::clone(&backend);
    let backend_state = BackendState {
        url: Arc::new(Mutex::new(String::new())),
    };
    let backend_state_for_setup = backend_state.clone();

    tauri::Builder::default()
        .manage(backend_state)
        .invoke_handler(tauri::generate_handler![backend_url])
        .setup(move |app| {
            let port = 8765;
            let backend_url = format!("http://127.0.0.1:{}", port);
            *backend_state_for_setup.url.lock().expect("backend url lock poisoned") =
                backend_url.clone();

            if let Some(window) = app.get_window("main") {
                let script = format!(
                    "window.__CIVILAI_BACKEND_URL__ = {};",
                    serde_json::to_string(&backend_url)?
                );
                let _ = window.eval(&script);
            }

            let mut env = HashMap::new();
            env.insert("CIVILAI_DESKTOP".to_string(), "1".to_string());
            env.insert("CIVILAI_BACKEND_PORT".to_string(), port.to_string());
            env.insert("DEBUG".to_string(), "False".to_string());

            let (mut rx, child) = Command::new_sidecar("civilai-backend")?
                .envs(env)
                .spawn()?;

            *backend.lock().expect("backend lock poisoned") = Some(child);

            let handle = app.handle();
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    if let CommandEvent::Stderr(line) | CommandEvent::Stdout(line) = event {
                        println!("[civilai-backend] {}", line);
                    }
                }
                handle.exit(1);
            });

            Ok(())
        })
        .on_window_event(move |event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event.event() {
                if let Some(child) = backend_for_exit.lock().expect("backend lock poisoned").take() {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running CivilAI desktop");
}
