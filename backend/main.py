from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import subprocess
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict
import logging
import asyncio
import json
import uuid
import re
import threading
from datetime import datetime
from mutagen import File as MutagenFile
import shutil
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = Path.home() / "Downloads"
TELEGRAM_DIR = Path(os.environ.get("TELEGRAM_DIR", str(Path.home() / "Downloads" / "Telegram Desktop")))
ALLOWED_EXTENSIONS = {".ogg", ".mp3", ".wav", ".m4a", ".webm", ".mp4"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}

# Whisper venv for bundled mode
WHISPER_VENV_DIR = Path.home() / ".sheptun" / "whisper-venv"
whisper_setup_done = False
whisper_setup_status = {"stage": "pending", "message": ""}

def get_whisper_python() -> Path:
    """Get the Python executable that has whisper installed."""
    # If running from source (not bundled), use current Python
    if not getattr(sys, 'frozen', False):
        return Path(sys.executable)

    # Bundled mode: use whisper venv
    if sys.platform == 'win32':
        return WHISPER_VENV_DIR / "Scripts" / "python.exe"
    return WHISPER_VENV_DIR / "bin" / "python"


def _find_embedded_python() -> str | None:
    """Find Python bundled with the app in resources/python/."""
    if not getattr(sys, 'frozen', False):
        return None
    # PyInstaller: sys._MEIPASS is the temp dir, but resources are next to the app
    # Electron puts extraResources at process.resourcesPath which is passed via env
    resources_dir = os.environ.get('SHEPTUN_RESOURCES_PATH', '')
    if not resources_dir:
        # Fallback: relative to the binary location
        resources_dir = str(Path(sys.executable).parent.parent)
    if sys.platform == 'win32':
        candidate = os.path.join(resources_dir, 'python', 'python.exe')
    else:
        candidate = os.path.join(resources_dir, 'python', 'bin', 'python3')
    if os.path.isfile(candidate):
        logger.info(f"Found embedded Python: {candidate}")
        return candidate
    return None


def _find_system_python() -> str | None:
    """Find Python 3 on the system PATH."""
    candidates = ['python3', 'python'] if sys.platform != 'win32' else ['python', 'python3', 'py']
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, '--version'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and 'Python 3' in (result.stdout + result.stderr):
                return candidate
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None


def _find_python() -> str | None:
    """Find Python: embedded first, then system."""
    return _find_embedded_python() or _find_system_python()


def ensure_whisper_installed():
    """Create venv and install whisper if needed (bundled mode only)."""
    global whisper_setup_done, whisper_setup_status
    if whisper_setup_done:
        return
    if not getattr(sys, 'frozen', False):
        whisper_setup_done = True
        whisper_setup_status = {"stage": "ready", "message": ""}
        return

    whisper_python = get_whisper_python()
    marker = WHISPER_VENV_DIR / ".deps-v3-installed"

    if marker.exists() and whisper_python.exists():
        whisper_setup_done = True
        whisper_setup_status = {"stage": "ready", "message": ""}
        return

    logger.info("Setting up whisper environment...")
    whisper_setup_status = {"stage": "installing", "message": "Поиск Python..."}

    # Find Python: embedded first, then system
    system_python = _find_python()
    if not system_python:
        whisper_setup_status = {"stage": "error", "message": "Python 3 не найден"}
        raise RuntimeError(
            "Python 3 не найден. Переустановите приложение или установите Python 3.8+.\n"
            "macOS: brew install python3\n"
            "Windows: https://python.org/downloads\n"
            "Linux: sudo apt install python3 python3-venv"
        )

    # Create venv
    whisper_setup_status = {"stage": "installing", "message": "Создание окружения..."}
    WHISPER_VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [system_python, '-m', 'venv', str(WHISPER_VENV_DIR)],
        check=True, capture_output=True
    )

    # Install whisper, yt-dlp, and imageio-ffmpeg (bundles ffmpeg binary)
    whisper_setup_status = {"stage": "installing", "message": "Установка зависимостей (это может занять несколько минут)..."}
    pip = WHISPER_VENV_DIR / ("Scripts" if sys.platform == 'win32' else "bin") / "pip"
    subprocess.run(
        [str(pip), 'install', 'openai-whisper', 'yt-dlp', 'imageio-ffmpeg'],
        check=True, capture_output=True
    )

    # Create ffmpeg symlink in venv bin so it's on PATH
    whisper_setup_status = {"stage": "installing", "message": "Настройка ffmpeg..."}
    venv_bin_dir = WHISPER_VENV_DIR / ("Scripts" if sys.platform == 'win32' else "bin")
    ffmpeg_link = venv_bin_dir / ("ffmpeg.exe" if sys.platform == 'win32' else "ffmpeg")
    if not ffmpeg_link.exists():
        try:
            whisper_python = get_whisper_python()
            result = subprocess.run(
                [str(whisper_python), '-c', 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'],
                capture_output=True, text=True
            )
            ffmpeg_real = result.stdout.strip()
            if ffmpeg_real and Path(ffmpeg_real).exists():
                if sys.platform == 'win32':
                    shutil.copy2(ffmpeg_real, str(ffmpeg_link))
                else:
                    ffmpeg_link.symlink_to(ffmpeg_real)
                logger.info(f"ffmpeg linked: {ffmpeg_link} -> {ffmpeg_real}")
        except Exception as e:
            logger.warning(f"Could not link ffmpeg from imageio-ffmpeg: {e}")

    marker.write_text("installed")
    whisper_setup_done = True
    whisper_setup_status = {"stage": "ready", "message": ""}
    logger.info("Whisper + yt-dlp + ffmpeg environment ready")


def update_yt_dlp():
    """Update yt-dlp to the latest version (YouTube changes frequently)."""
    if not getattr(sys, 'frozen', False):
        return
    try:
        pip = WHISPER_VENV_DIR / ("Scripts" if sys.platform == 'win32' else "bin") / "pip"
        if not pip.exists():
            return
        logger.info("Updating yt-dlp...")
        subprocess.run(
            [str(pip), 'install', '--upgrade', 'yt-dlp'],
            capture_output=True, timeout=60
        )
        logger.info("yt-dlp updated")
    except Exception as e:
        logger.warning(f"Failed to update yt-dlp: {e}")


def get_env_with_deps() -> dict:
    """Return env with venv bin dir prepended to PATH (for ffmpeg, yt-dlp access)."""
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    if getattr(sys, 'frozen', False):
        venv_bin = str(WHISPER_VENV_DIR / ("Scripts" if sys.platform == 'win32' else "bin"))
        env['PATH'] = venv_bin + os.pathsep + env.get('PATH', '')
    return env


def get_yt_dlp_bin() -> str:
    """Get yt-dlp binary path: check venv first, then system PATH."""
    if sys.platform == 'win32':
        venv_bin = WHISPER_VENV_DIR / "Scripts" / "yt-dlp.exe"
    else:
        venv_bin = WHISPER_VENV_DIR / "bin" / "yt-dlp"
    if venv_bin.exists():
        return str(venv_bin)
    system_bin = shutil.which("yt-dlp")
    if system_bin:
        return system_bin
    raise Exception("yt-dlp не найден. Перезапустите приложение для автоматической установки.")


progress_store: Dict[str, Dict] = {}
active_tasks: Dict[str, bool] = {}


@app.on_event("startup")
async def startup_event():
    def _setup():
        try:
            ensure_whisper_installed()
            update_yt_dlp()
        except Exception as e:
            logger.error(f"Failed to setup whisper: {e}")
    threading.Thread(target=_setup, daemon=True).start()

async def process_audio_files_async(
    file_paths: List[dict],
    task_id: str,
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "",
    task: str = "transcribe"
):
    import threading
    import queue

    try:
        active_tasks[task_id] = True
        task_start_time = datetime.now()
        total_files = len(file_paths)

        progress_store[task_id] = {
            "status": "processing",
            "current": 0,
            "total": total_files,
            "current_file": "",
            "current_file_progress": 0,
            "message": f"Найдено {total_files} файлов",
            "whisper_logs": [],
            "last_log": "",
            "start_time": task_start_time.timestamp(),
            "elapsed_seconds": 0,
            "estimated_remaining_seconds": None,
            "previous_total_progress": 0,
            "previous_total_time": 0,
            "total_progress_speed_history": []
        }

        all_texts = []

        for idx, file_info in enumerate(file_paths, 1):
            if not active_tasks.get(task_id, True):
                progress_store[task_id]["status"] = "cancelled"
                progress_store[task_id]["message"] = "Обработка остановлена пользователем"
                return

            tmp_path = file_info["tmp_path"]
            original_name = file_info["name"]
            file_path = Path(tmp_path)

            try:
                file_duration = get_audio_duration(file_path)
                estimated_processing_time = file_duration * 0.1 if file_duration > 0 else 300
            except Exception:
                file_duration = 0
                estimated_processing_time = 300

            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            progress_store[task_id].update({
                "status": "processing",
                "current": idx,
                "current_file": original_name,
                "current_file_progress": 0,
                "message": f"Обработка файла {idx}/{total_files}: {original_name} ({file_size_mb:.2f} MB)",
                "whisper_logs": [],
                "last_log": ""
            })

            whisper_cmd = [
                str(get_whisper_python()), "-m", "whisper",
                str(tmp_path),
                "--model", model,
                "--task", task,
                "--output_format", output_format,
                "--output_dir", str(DOWNLOADS_DIR),
                "--verbose", "False"
            ]

            if language:
                whisper_cmd.extend(["--language", language])
            if initial_prompt:
                whisper_cmd.extend(["--initial_prompt", initial_prompt])

            env = get_env_with_deps()

            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            if sys.platform == 'win32':
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(whisper_cmd, **popen_kwargs)

            log_queue = queue.Queue()

            def read_stream(stream, stream_name):
                try:
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        line = line.rstrip()
                        if line:
                            log_queue.put((stream_name, line))
                except Exception as e:
                    logger.error(f"Ошибка чтения {stream_name}: {str(e)}")
                finally:
                    try:
                        stream.close()
                    except:
                        pass

            stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, 'stdout'), daemon=True)
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, 'stderr'), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            start_time = datetime.now()
            last_eta_update = 0
            whisper_logs = []
            whisper_reported_progress = False
            model_downloading = False

            while process.poll() is None:
                if not active_tasks.get(task_id, True):
                    process.terminate()
                    process.wait()
                    progress_store[task_id]["status"] = "cancelled"
                    progress_store[task_id]["message"] = "Обработка остановлена пользователем"
                    return

                while not log_queue.empty():
                    try:
                        stream_type, line = log_queue.get_nowait()
                        log_entry = f"[{stream_type.upper()}] {line}"
                        whisper_logs.append(log_entry)
                        if len(whisper_logs) > 100:
                            whisper_logs = whisper_logs[-100:]

                        if stream_type == 'stderr':
                            # Detect model download vs transcription
                            is_model_download = 'MiB/s' in line or 'MB/s' in line or 'kB/s' in line
                            is_transcription = 'frames/s' in line or 'it/s' in line

                            if is_model_download and not is_transcription:
                                model_downloading = True
                                percent_match = re.search(r'(\d+)%', line)
                                if percent_match:
                                    dl_pct = int(percent_match.group(1))
                                    progress_store[task_id]["model_download_progress"] = dl_pct
                                    progress_store[task_id]["message"] = f"Загрузка модели {model}... {dl_pct}%"
                                    # Don't update file progress during model download
                            else:
                                if model_downloading:
                                    model_downloading = False
                                    progress_store[task_id]["model_download_progress"] = 100
                                    progress_store[task_id]["message"] = f"Обработка файла {idx}/{total_files}: {original_name} ({file_size_mb:.2f} MB)"

                                percent_match = re.search(r'(\d+)%', line)
                                if percent_match:
                                    whisper_reported_progress = True
                                    progress_store[task_id]["current_file_progress"] = min(int(percent_match.group(1)), 99)

                        progress_store[task_id]["whisper_logs"] = whisper_logs[-20:]
                        progress_store[task_id]["last_log"] = log_entry
                    except queue.Empty:
                        break

                elapsed = (datetime.now() - start_time).total_seconds()
                total_elapsed = (datetime.now() - task_start_time).total_seconds()

                if not whisper_reported_progress and estimated_processing_time > 0:
                    file_progress = min(int((elapsed / estimated_processing_time) * 100), 95)
                    current_stored = progress_store[task_id].get("current_file_progress", 0)
                    if file_progress > current_stored:
                        progress_store[task_id]["current_file_progress"] = file_progress

                progress_store[task_id]["elapsed_seconds"] = int(total_elapsed)

                total_progress = ((idx - 1) / total_files * 100) + (progress_store[task_id]["current_file_progress"] / total_files)
                progress_store[task_id]["total_progress"] = total_progress

                if total_elapsed >= last_eta_update + 30:
                    prev_total_time = progress_store[task_id].get("previous_total_time", 0)
                    prev_total_progress = progress_store[task_id].get("previous_total_progress", 0)
                    total_speed_history = progress_store[task_id].get("total_progress_speed_history", [])

                    if prev_total_time > 0:
                        time_delta = total_elapsed - prev_total_time
                        progress_delta = total_progress - prev_total_progress
                        if time_delta > 0 and progress_delta > 0:
                            speed = progress_delta / time_delta
                            total_speed_history.append(speed)
                            if len(total_speed_history) > 5:
                                total_speed_history.pop(0)
                            if total_speed_history:
                                avg_speed = sum(total_speed_history) / len(total_speed_history)
                                if avg_speed > 0 and total_progress < 100:
                                    remaining_progress = 100 - total_progress
                                    progress_store[task_id]["estimated_remaining_seconds"] = int(remaining_progress / avg_speed)

                    progress_store[task_id]["previous_total_time"] = total_elapsed
                    progress_store[task_id]["previous_total_progress"] = total_progress
                    progress_store[task_id]["total_progress_speed_history"] = total_speed_history
                    last_eta_update = total_elapsed

                await asyncio.sleep(0.2)

            process.wait()
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)

            while not log_queue.empty():
                try:
                    stream_type, line = log_queue.get_nowait()
                    whisper_logs.append(f"[{stream_type.upper()}] {line}")
                except queue.Empty:
                    break

            if process.returncode != 0:
                logger.warning(f"Ошибка обработки {original_name}")
                progress_store[task_id]["current_file_progress"] = 0
                progress_store[task_id]["last_log"] = f"Ошибка обработки {original_name}"
                continue

            progress_store[task_id]["current_file_progress"] = 100
            progress_store[task_id]["last_log"] = f"Файл {original_name} обработан успешно"

            base_name = Path(original_name).stem
            output_ext = f".{output_format}" if output_format != "txt" else ".txt"

            # whisper saves with tmp file stem, rename to original name
            tmp_stem = Path(tmp_path).stem
            whisper_output = DOWNLOADS_DIR / f"{tmp_stem}{output_ext}"
            final_output = DOWNLOADS_DIR / f"{base_name}{output_ext}"

            if whisper_output.exists():
                if output_format == "txt":
                    with open(whisper_output, "r", encoding="utf-8") as f:
                        all_texts.append(f.read())
                    whisper_output.unlink()
                else:
                    if final_output.exists():
                        final_output.unlink()
                    whisper_output.rename(final_output)

            # clean extra formats
            for ext in [".srt", ".vtt", ".json", ".tsv", ".txt"]:
                extra = DOWNLOADS_DIR / f"{tmp_stem}{ext}"
                if extra.exists():
                    extra.unlink()

        # cleanup temp files
        for file_info in file_paths:
            try:
                os.unlink(file_info["tmp_path"])
            except:
                pass

        output_file_name = ""
        if output_format == "txt":
            if not all_texts:
                progress_store[task_id] = {
                    "status": "error",
                    "current": total_files,
                    "total": total_files,
                    "current_file": "",
                    "current_file_progress": 0,
                    "message": "Не удалось обработать файлы"
                }
                return

            merged_text = "\n\n".join(all_texts)
            if total_files == 1:
                out_name = Path(file_paths[0]["name"]).stem + ".txt"
            else:
                out_name = "merged.txt"
            merged_file = DOWNLOADS_DIR / out_name
            with open(merged_file, "w", encoding="utf-8") as f:
                f.write(merged_text)
            output_file_name = out_name
        else:
            if total_files == 1:
                output_file_name = Path(file_paths[0]["name"]).stem + f".{output_format}"
            else:
                output_file_name = ""

        progress_store[task_id] = {
            "status": "completed",
            "current": total_files,
            "total": total_files,
            "current_file": "",
            "current_file_progress": 100,
            "message": "Готово. Файл сохранён в Downloads",
            "output_file": output_file_name,
            "output_dir": str(DOWNLOADS_DIR)
        }
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        progress_store[task_id] = {
            "status": "error",
            "current": progress_store.get(task_id, {}).get("current", 0),
            "total": progress_store.get(task_id, {}).get("total", 0),
            "current_file": "",
            "current_file_progress": 0,
            "message": f"Ошибка: {str(e)}"
        }
    finally:
        if task_id in active_tasks:
            del active_tasks[task_id]


@app.post("/transcribe")
async def transcribe_audio(
    files: List[UploadFile] = File(...),
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией.",
    task: str = "transcribe",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не выбраны")

    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model not in valid_models:
        model = "small"

    # Save uploaded files to temp
    file_paths = []
    for file in files:
        if not file.filename:
            continue
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            continue
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            file_paths.append({"tmp_path": tmp_file.name, "name": file.filename})

    if not file_paths:
        raise HTTPException(status_code=400, detail="Нет подходящих файлов")

    task_id = str(uuid.uuid4())
    active_tasks[task_id] = True
    progress_store[task_id] = {
        "status": "starting",
        "current": 0,
        "total": len(file_paths),
        "current_file": "",
        "current_file_progress": 0,
        "message": "Начало обработки...",
        "whisper_logs": [],
        "last_log": ""
    }

    background_tasks.add_task(
        process_audio_files_async,
        file_paths, task_id, model, language, output_format, initial_prompt, task
    )

    return JSONResponse(
        status_code=200,
        content={"task_id": task_id, "message": "Обработка начата"}
    )


@app.post("/transcribe/{task_id}/stop")
async def stop_audio_transcription(task_id: str):
    if task_id in active_tasks:
        active_tasks[task_id] = False
        return JSONResponse(status_code=200, content={"message": "Остановка обработки..."})
    return JSONResponse(status_code=404, content={"message": "Задача не найдена"})

@app.get("/telegram/folders")
async def get_telegram_folders():
    if not TELEGRAM_DIR.exists():
        return JSONResponse(status_code=404, content={"detail": "Папка Telegram Desktop не найдена"})
    
    folders = []
    for item in TELEGRAM_DIR.iterdir():
        if item.is_dir() and item.name.startswith("ChatExport_"):
            folders.append(item.name)
    
    return JSONResponse(status_code=200, content={"folders": sorted(folders, reverse=True)})

def natural_sort_key(text):
    def convert(text_part):
        return int(text_part) if text_part.isdigit() else text_part.lower()
    return [convert(c) for c in re.split(r'(\d+)', text)]

def get_audio_duration(file_path: Path) -> float:
    try:
        if not file_path.exists():
            return 0.0
        audio_file = MutagenFile(str(file_path))
        if audio_file is not None and hasattr(audio_file, 'info') and audio_file.info is not None:
            duration = getattr(audio_file.info, 'length', 0.0)
            return float(duration) if duration else 0.0
        return 0.0
    except Exception as e:
        logger.warning(f"Не удалось получить продолжительность для {file_path.name}: {str(e)}")
        return 0.0

@app.get("/telegram/folders/{folder_name}/files")
async def get_telegram_files(folder_name: str):
    folder_path = TELEGRAM_DIR / folder_name
    voice_messages_path = folder_path / "voice_messages"
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Папка не найдена")
    
    ogg_files = []
    
    if voice_messages_path.exists():
        for file in voice_messages_path.iterdir():
            if file.is_file() and file.suffix.lower() == ".ogg":
                stat = file.stat()
                duration = get_audio_duration(file)
                ogg_files.append({
                    "name": file.name,
                    "path": str(file),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "duration": duration
                })
    else:
        for file in folder_path.rglob("*.ogg"):
            stat = file.stat()
            duration = get_audio_duration(file)
            ogg_files.append({
                "name": file.name,
                "path": str(file),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "duration": duration
            })
    
    sorted_files = sorted(ogg_files, key=lambda x: natural_sort_key(x["name"]))
    total_size = sum(f["size"] for f in sorted_files)
    
    return JSONResponse(status_code=200, content={
        "files": sorted_files,
        "total_size": total_size,
        "total_files": len(sorted_files)
    })

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    async def event_generator():
        last_data = None
        while True:
            if task_id in progress_store:
                progress = progress_store[task_id]
                try:
                    current_data = json.dumps(progress, ensure_ascii=False)
                    
                    if current_data != last_data:
                        yield f"data: {current_data}\n\n"
                        last_data = current_data
                    
                    if progress.get("status") in ["completed", "error", "cancelled"]:
                        break
                except Exception as e:
                    logger.error(f"Ошибка сериализации прогресса: {str(e)}")
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Ошибка сериализации'}, ensure_ascii=False)}\n\n"
                    break
            else:
                yield f"data: {json.dumps({'status': 'not_found'}, ensure_ascii=False)}\n\n"
                break
            
            await asyncio.sleep(0.5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

async def process_telegram_files_async(
    folder_name: str,
    task_id: str,
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
):
    try:
        active_tasks[task_id] = True
        task_start_time = datetime.now()
        progress_store[task_id] = {
            "status": "starting",
            "current": 0,
            "total": 0,
            "current_file": "",
            "current_file_progress": 0,
            "message": "Начало обработки...",
            "whisper_logs": [],
            "last_log": "",
            "start_time": task_start_time.timestamp(),
            "elapsed_seconds": 0,
            "estimated_remaining_seconds": None
        }
        
        folder_path = TELEGRAM_DIR / folder_name
        voice_messages_path = folder_path / "voice_messages"
        
        ogg_files = []
        if voice_messages_path.exists():
            for file in voice_messages_path.iterdir():
                if file.is_file() and file.suffix.lower() == ".ogg":
                    ogg_files.append(file)
        else:
            for file in folder_path.rglob("*.ogg"):
                ogg_files.append(file)
        
        sorted_files = sorted(ogg_files, key=lambda x: natural_sort_key(x.name))
        total_files = len(sorted_files)
        
        progress_store[task_id] = {
            "status": "processing",
            "current": 0,
            "total": total_files,
            "current_file": "",
            "current_file_progress": 0,
            "message": f"Найдено {total_files} файлов",
            "whisper_logs": [],
            "last_log": "",
            "start_time": task_start_time.timestamp(),
            "elapsed_seconds": 0,
            "estimated_remaining_seconds": None,
            "previous_total_progress": 0,
            "previous_total_time": 0,
            "total_progress_speed_history": []
        }
        
        all_texts = []
        
        for idx, file_path in enumerate(sorted_files, 1):
            if not active_tasks.get(task_id, True):
                progress_store[task_id] = {
                    "status": "cancelled",
                    "current": idx - 1,
                    "total": total_files,
                    "current_file": "",
                    "current_file_progress": 0,
                    "message": "Обработка остановлена пользователем"
                }
                return
            
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            try:
                file_duration = get_audio_duration(file_path)
                estimated_processing_time = file_duration * 0.1 if file_duration > 0 else 300
            except Exception as e:
                logger.warning(f"Ошибка при получении продолжительности файла {file_path.name}: {str(e)}")
                file_duration = 0
                estimated_processing_time = 300
            
            progress_store[task_id] = {
                "status": "processing",
                "current": idx,
                "total": total_files,
                "current_file": file_path.name,
                "current_file_progress": 0,
                "message": f"Обработка файла {idx}/{total_files}: {file_path.name} ({file_size_mb:.2f} MB)",
                "whisper_logs": [],
                "last_log": ""
            }
            logger.info(f"Обработка файла {idx}/{total_files}: {file_path.name} (0%)")
            
            whisper_cmd = [
                str(get_whisper_python()), "-m", "whisper",
                str(file_path),
                "--model", model,
                "--output_format", output_format,
                "--output_dir", str(DOWNLOADS_DIR),
                "--verbose", "False"
            ]
            
            if language:
                whisper_cmd.extend(["--language", language])
            
            if initial_prompt:
                whisper_cmd.extend(["--initial_prompt", initial_prompt])
            
            import threading
            import queue
            
            env = get_env_with_deps()

            popen_kwargs2 = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            if sys.platform == 'win32':
                popen_kwargs2['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(whisper_cmd, **popen_kwargs2)

            log_queue = queue.Queue()

            def read_stream(stream, stream_name):
                try:
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        try:
                            line = line.rstrip()
                            if line:
                                log_queue.put((stream_name, line))
                        except UnicodeDecodeError:
                            try:
                                line = line.decode('utf-8', errors='replace').rstrip()
                                if line:
                                    log_queue.put((stream_name, line))
                            except:
                                pass
                except Exception as e:
                    logger.error(f"Ошибка чтения {stream_name}: {str(e)}")
                finally:
                    try:
                        stream.close()
                    except:
                        pass
            
            stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, 'stdout'), daemon=True)
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, 'stderr'), daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            
            start_time = datetime.now()
            last_progress_update = 0
            last_eta_update = 0
            total_frames = None
            current_frames = 0
            whisper_logs = []
            
            previous_progress_time = None
            previous_progress_value = 0
            progress_speed_history = []
            
            logs_processed = 0
            max_logs_per_iteration = 50
            
            while process.poll() is None:
                if not active_tasks.get(task_id, True):
                    process.terminate()
                    process.wait()
                    progress_store[task_id] = {
                        "status": "cancelled",
                        "current": idx - 1,
                        "total": total_files,
                        "current_file": "",
                        "current_file_progress": 0,
                        "message": "Обработка остановлена пользователем",
                        "whisper_logs": whisper_logs
                    }
                    return
                
                logs_processed = 0
                while not log_queue.empty() and logs_processed < max_logs_per_iteration:
                    try:
                        stream_type, line = log_queue.get_nowait()
                        log_entry = f"[{stream_type.upper()}] {line}"
                        whisper_logs.append(log_entry)
                        logs_processed += 1
                        
                        if len(whisper_logs) > 100:
                            whisper_logs = whisper_logs[-100:]
                        
                        logger.info(f"[Whisper] {log_entry}")
                        
                        import re
                        if stream_type == 'stderr':
                            percent_match = re.search(r'(\d+)%', line)
                            if percent_match:
                                file_progress = int(percent_match.group(1))
                                progress_store[task_id]["current_file_progress"] = min(file_progress, 99)
                            
                            frames_match = re.search(r'(\d+)/(\d+)\s+\[.*?frames/s\]', line)
                            if frames_match:
                                current_frames = int(frames_match.group(1))
                                total_frames = int(frames_match.group(2))
                                if total_frames > 0:
                                    file_progress = int((current_frames / total_frames) * 100)
                                    progress_store[task_id]["current_file_progress"] = min(file_progress, 99)
                            
                            frames_match2 = re.search(r'(\d+)/(\d+)\s+frames', line)
                            if frames_match2:
                                current_frames = int(frames_match2.group(1))
                                total_frames = int(frames_match2.group(2))
                                if total_frames > 0:
                                    file_progress = int((current_frames / total_frames) * 100)
                                    progress_store[task_id]["current_file_progress"] = min(file_progress, 99)
                        
                        progress_store[task_id]["whisper_logs"] = whisper_logs[-20:]
                        progress_store[task_id]["last_log"] = log_entry
                    except queue.Empty:
                        break
                    except Exception as e:
                        logger.error(f"Ошибка обработки лога: {str(e)}")
                        break
                
                current_time = datetime.now()
                elapsed = (current_time - start_time).total_seconds()
                total_elapsed = (current_time - task_start_time).total_seconds()
                
                if total_frames and total_frames > 0:
                    if elapsed >= last_progress_update + 1:
                        estimated_total = (elapsed / current_frames * total_frames) if current_frames > 0 else estimated_processing_time
                        if estimated_total > 0:
                            file_progress = min(int((elapsed / estimated_total) * 100), 99)
                            progress_store[task_id]["current_file_progress"] = file_progress
                        last_progress_update = elapsed
                else:
                    if estimated_processing_time > 0:
                        file_progress = min(int((elapsed / estimated_processing_time) * 100), 95)
                    else:
                        file_progress = min(int((elapsed / 300) * 100), 95)
                    progress_store[task_id]["current_file_progress"] = file_progress
                
                progress_store[task_id]["elapsed_seconds"] = int(total_elapsed)
                
                total_progress = ((idx - 1) / total_files * 100) + (file_progress / total_files)
                progress_store[task_id]["total_progress"] = total_progress
                
                if total_elapsed >= last_eta_update + 60:
                    prev_total_time = progress_store[task_id].get("previous_total_time", 0)
                    prev_total_progress = progress_store[task_id].get("previous_total_progress", 0)
                    total_speed_history = progress_store[task_id].get("total_progress_speed_history", [])
                    
                    if prev_total_time > 0:
                        time_delta = total_elapsed - prev_total_time
                        progress_delta = total_progress - prev_total_progress
                        
                        if time_delta > 0 and progress_delta > 0:
                            speed = progress_delta / time_delta
                            total_speed_history.append(speed)
                            
                            if len(total_speed_history) > 5:
                                total_speed_history.pop(0)
                            
                            if total_speed_history:
                                avg_speed = sum(total_speed_history) / len(total_speed_history)
                                
                                if avg_speed > 0 and total_progress < 100:
                                    remaining_progress = 100 - total_progress
                                    estimated_remaining = remaining_progress / avg_speed
                                    progress_store[task_id]["estimated_remaining_seconds"] = int(estimated_remaining)
                    
                    progress_store[task_id]["previous_total_time"] = total_elapsed
                    progress_store[task_id]["previous_total_progress"] = total_progress
                    progress_store[task_id]["total_progress_speed_history"] = total_speed_history
                    last_eta_update = total_elapsed
                
                await asyncio.sleep(0.2)
            
            process.wait()
            returncode = process.returncode
            
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            
            while not log_queue.empty():
                try:
                    stream_type, line = log_queue.get_nowait()
                    log_entry = f"[{stream_type.upper()}] {line}"
                    whisper_logs.append(log_entry)
                    logger.info(f"[Whisper] {log_entry}")
                except queue.Empty:
                    break
                except Exception:
                    break
            
            if returncode != 0:
                error_msg = "Ошибка обработки файла"
                try:
                    if process.stderr:
                        error_output = process.stderr.read()
                        if error_output:
                            error_msg = error_output.decode('utf-8', errors='replace')[:200]
                except:
                    pass
                logger.warning(f"Ошибка обработки {file_path.name}: {error_msg}")
                progress_store[task_id]["current_file_progress"] = 0
                progress_store[task_id]["last_log"] = f"Ошибка: {error_msg}"
                continue
            
            progress_store[task_id]["current_file_progress"] = 100
            progress_store[task_id]["whisper_logs"] = whisper_logs[-20:]
            progress_store[task_id]["last_log"] = f"Файл {file_path.name} обработан успешно"
            logger.info(f"Обработка файла {idx}/{total_files}: {file_path.name} (100%)")
            logger.info(f"Файл {file_path.name} обработан успешно")
            base_name = file_path.stem
            txt_file = DOWNLOADS_DIR / f"{base_name}.txt"
            
            for ext in [".srt", ".vtt", ".json", ".tsv"]:
                extra_file = DOWNLOADS_DIR / f"{base_name}{ext}"
                if extra_file.exists():
                    os.unlink(extra_file)
            
            if txt_file.exists():
                with open(txt_file, "r", encoding="utf-8") as f:
                    all_texts.append(f.read())
                txt_file.unlink()
        
        if not all_texts:
            progress_store[task_id] = {
                "status": "error",
                "current": total_files,
                "total": total_files,
                "current_file": "",
                "message": "Не удалось обработать файлы"
            }
            return
        
        merged_text = "\n\n".join(all_texts)
        merged_file = DOWNLOADS_DIR / "merged.txt"
        
        with open(merged_file, "w", encoding="utf-8") as f:
            f.write(merged_text)
        
        logger.info(f"Файл merged.txt сохранён в {merged_file}")
        progress_store[task_id] = {
            "status": "completed",
            "current": total_files,
            "total": total_files,
            "current_file": "",
            "current_file_progress": 100,
            "message": "Готово. Файл сохранён в Downloads"
        }
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        current_info = progress_store.get(task_id, {})
        if isinstance(current_info, dict):
            current = current_info.get("current", 0)
            total = current_info.get("total", 0)
        else:
            current = 0
            total = 0
        progress_store[task_id] = {
            "status": "error",
            "current": current,
            "total": total,
            "current_file": "",
            "current_file_progress": 0,
            "message": f"Ошибка: {str(e)}"
        }
    finally:
        if task_id in active_tasks:
            del active_tasks[task_id]

@app.post("/transcribe/telegram")
async def transcribe_telegram_files(
    folder_name: str,
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией.",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    folder_path = TELEGRAM_DIR / folder_name
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Папка не найдена")
    
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model not in valid_models:
        model = "small"
    
    task_id = str(uuid.uuid4())
    active_tasks[task_id] = True
    
    progress_store[task_id] = {
        "status": "starting",
        "current": 0,
        "total": 0,
        "current_file": "",
        "current_file_progress": 0,
        "message": "Начало обработки...",
        "whisper_logs": [],
        "last_log": ""
    }
    
    background_tasks.add_task(
        process_telegram_files_async,
        folder_name,
        task_id,
        model,
        language,
        output_format,
        initial_prompt
    )
    
    return JSONResponse(
        status_code=200,
        content={"task_id": task_id, "message": "Обработка начата"}
    )

@app.post("/transcribe/telegram/{task_id}/stop")
async def stop_transcription(task_id: str):
    if task_id in active_tasks:
        active_tasks[task_id] = False
        return JSONResponse(status_code=200, content={"message": "Остановка обработки..."})
    return JSONResponse(status_code=404, content={"message": "Задача не найдена"})

@app.post("/transcribe/video")
async def transcribe_video(
    files: List[UploadFile] = File(...),
    model: str = "medium",
    language: str = "English",
    output_format: str = "srt",
    task: str = "translate"
):
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не выбраны")
    
    all_outputs = []
    temp_files = []
    
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model not in valid_models:
        model = "medium"
    
    if task not in ["transcribe", "translate"]:
        task = "translate"
    
    whisper_cmd = [
        str(get_whisper_python()), "-m", "whisper",
        "--model", model,
        "--task", task,
        "--output_format", output_format,
        "--output_dir", str(DOWNLOADS_DIR)
    ]
    
    if language:
        whisper_cmd.extend(["--language", language])
    
    try:
        for file in files:
            if not file.filename:
                continue
            
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
                continue
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                content = await file.read()
                tmp_file.write(content)
                tmp_path = tmp_file.name
                temp_files.append(tmp_path)
            
            cmd = whisper_cmd + [tmp_path]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
                env=get_env_with_deps()
            )
            
            if result.returncode != 0:
                continue
            
            base_name = Path(file.filename).stem
            output_file = DOWNLOADS_DIR / f"{base_name}.{output_format}"
            
            if output_file.exists():
                all_outputs.append(str(output_file))
        
        if not all_outputs:
            raise HTTPException(status_code=500, detail="Не удалось обработать файлы")
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Готово. Файлы сохранены в Downloads: {', '.join([Path(f).name for f in all_outputs])}"}
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Таймаут транскрибации")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

@app.post("/transcribe/youtube")
async def transcribe_youtube(
    url: str,
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией.",
    task: str = "transcribe",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not url:
        raise HTTPException(status_code=400, detail="URL не указан")

    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model not in valid_models:
        model = "small"

    task_id = str(uuid.uuid4())
    active_tasks[task_id] = True
    progress_store[task_id] = {
        "status": "downloading",
        "current": 0,
        "total": 1,
        "current_file": "",
        "current_file_progress": 0,
        "message": "Загрузка аудио с YouTube...",
        "whisper_logs": [],
        "last_log": ""
    }

    background_tasks.add_task(
        process_youtube_async,
        url, task_id, model, language, output_format, initial_prompt, task
    )

    return JSONResponse(
        status_code=200,
        content={"task_id": task_id, "message": "Загрузка и обработка начаты"}
    )


async def process_youtube_async(
    url: str,
    task_id: str,
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "",
    task: str = "transcribe"
):
    tmp_dir = None
    try:
        import threading
        import queue

        active_tasks[task_id] = True
        task_start_time = datetime.now()

        progress_store[task_id] = {
            "status": "downloading",
            "current": 0,
            "total": 1,
            "current_file": "",
            "current_file_progress": 0,
            "message": "Загрузка аудио с YouTube...",
            "whisper_logs": [],
            "last_log": "",
            "start_time": task_start_time.timestamp(),
            "elapsed_seconds": 0,
            "estimated_remaining_seconds": None
        }

        tmp_dir = tempfile.mkdtemp()

        # Find yt-dlp binary (venv or system)
        yt_dlp_bin = get_yt_dlp_bin()

        yt_base_cmd = [
            yt_dlp_bin,
            "-x", "--audio-format", "mp3", "--audio-quality", "192K",
            "--no-playlist",
            "-o", os.path.join(tmp_dir, "%(title)s.%(ext)s"),
            "--print", "after_move:filepath",
            url
        ]

        env = get_env_with_deps()

        def run_yt_dlp(yt_cmd):
            """Run yt-dlp and monitor progress. Returns (process, downloaded_file, stderr_lines)."""
            nonlocal task_start_time

            popen_kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            if sys.platform == 'win32':
                popen_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(yt_cmd, **popen_kwargs)

            _log_queue = queue.Queue()
            _stderr_lines = []

            def read_stream(stream, stream_name):
                try:
                    while True:
                        line = stream.readline()
                        if not line:
                            break
                        line = line.rstrip()
                        if line:
                            _log_queue.put((stream_name, line))
                except Exception as e:
                    logger.error(f"Ошибка чтения {stream_name}: {str(e)}")
                finally:
                    try:
                        stream.close()
                    except:
                        pass

            stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, 'stdout'), daemon=True)
            stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, 'stderr'), daemon=True)
            stdout_thread.start()
            stderr_thread.start()

            _downloaded_file = None

            return process, stdout_thread, stderr_thread, _log_queue, _stderr_lines, _downloaded_file

        async def monitor_yt_dlp(process, stdout_thread, stderr_thread, _log_queue, _stderr_lines, _downloaded_file):
            """Monitor yt-dlp process, return (downloaded_file, stderr_lines)."""
            downloaded_file = _downloaded_file

            while process.poll() is None:
                if not active_tasks.get(task_id, True):
                    process.terminate()
                    process.wait()
                    progress_store[task_id]["status"] = "cancelled"
                    progress_store[task_id]["message"] = "Обработка остановлена пользователем"
                    return None, _stderr_lines

                while not _log_queue.empty():
                    try:
                        stream_type, line = _log_queue.get_nowait()

                        if stream_type == 'stdout' and line.strip().endswith('.mp3'):
                            downloaded_file = line.strip()

                        if stream_type == 'stderr':
                            _stderr_lines.append(line)
                            percent_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                            if percent_match:
                                pct = float(percent_match.group(1))
                                progress_store[task_id]["current_file_progress"] = min(int(pct), 99)

                            if '[download]' in line:
                                progress_store[task_id]["message"] = f"Загрузка: {line.split('[download]')[-1].strip()}"
                            elif '[ExtractAudio]' in line:
                                progress_store[task_id]["message"] = "Извлечение аудио..."
                                progress_store[task_id]["current_file_progress"] = 100

                        progress_store[task_id]["last_log"] = f"[{stream_type.upper()}] {line}"
                    except queue.Empty:
                        break

                total_elapsed = (datetime.now() - task_start_time).total_seconds()
                progress_store[task_id]["elapsed_seconds"] = int(total_elapsed)
                await asyncio.sleep(0.3)

            process.wait()
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)

            # Drain remaining output
            while not _log_queue.empty():
                try:
                    stream_type, line = _log_queue.get_nowait()
                    if stream_type == 'stdout' and line.strip().endswith('.mp3'):
                        downloaded_file = line.strip()
                    if stream_type == 'stderr':
                        _stderr_lines.append(line)
                except queue.Empty:
                    break

            return downloaded_file, _stderr_lines

        # Try without cookies first, then with cookies on failure
        proc, sthread, ethread, lqueue, elines, dfile = run_yt_dlp(yt_base_cmd)
        downloaded_file, stderr_lines = await monitor_yt_dlp(proc, sthread, ethread, lqueue, elines, dfile)

        if downloaded_file is None and progress_store[task_id].get("status") == "cancelled":
            return

        if proc.returncode != 0:
            # Retry with browser cookies
            logger.info("yt-dlp failed without cookies, retrying with --cookies-from-browser chrome")
            progress_store[task_id]["message"] = "Повторная попытка с cookies браузера..."
            progress_store[task_id]["current_file_progress"] = 0

            # Clean tmp_dir for retry
            for f in os.listdir(tmp_dir):
                os.remove(os.path.join(tmp_dir, f))

            yt_cmd_cookies = [yt_dlp_bin, "--cookies-from-browser", "chrome"] + yt_base_cmd[1:]
            proc2, sthread2, ethread2, lqueue2, elines2, dfile2 = run_yt_dlp(yt_cmd_cookies)
            downloaded_file, stderr_lines2 = await monitor_yt_dlp(proc2, sthread2, ethread2, lqueue2, elines2, dfile2)

            if downloaded_file is None and progress_store[task_id].get("status") == "cancelled":
                return

            if proc2.returncode != 0:
                # Show last meaningful error lines from yt-dlp
                all_errors = stderr_lines + stderr_lines2
                error_details = [l for l in all_errors if 'ERROR' in l or 'error' in l.lower()]
                if error_details:
                    last_error = error_details[-1].strip()
                    # Remove yt-dlp prefix like "ERROR: "
                    last_error = re.sub(r'^ERROR:\s*', '', last_error)
                    raise Exception(f"Ошибка загрузки с YouTube: {last_error}")
                else:
                    raise Exception("Ошибка загрузки с YouTube. Проверьте ссылку.")

        # Find downloaded mp3 if not captured via --print
        if not downloaded_file or not os.path.exists(downloaded_file):
            for f in os.listdir(tmp_dir):
                if f.endswith('.mp3'):
                    downloaded_file = os.path.join(tmp_dir, f)
                    break

        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception("Не удалось найти загруженный аудио файл")

        # Extract title from filename
        video_title = Path(downloaded_file).stem
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)[:100]

        progress_store[task_id]["message"] = f"Транскрибация: {safe_title}"
        progress_store[task_id]["current_file_progress"] = 0

        file_paths = [{"tmp_path": downloaded_file, "name": f"{safe_title}.mp3"}]

        # Delegate to the audio processing function — it manages progress_store and active_tasks
        await process_audio_files_async(
            file_paths, task_id, model, language, output_format, initial_prompt, task
        )

    except Exception as e:
        logger.error(f"Ошибка YouTube: {str(e)}")
        progress_store[task_id] = {
            "status": "error",
            "current": 0,
            "total": 1,
            "current_file": "",
            "current_file_progress": 0,
            "message": f"Ошибка: {str(e)}"
        }
        if task_id in active_tasks:
            del active_tasks[task_id]
    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


@app.get("/telegram/folders/{folder_name}/messages")
async def export_telegram_messages(folder_name: str):
    folder_path = TELEGRAM_DIR / folder_name
    result_json_path = folder_path / "result.json"
    
    if not folder_path.exists():
        raise HTTPException(status_code=404, detail="Папка не найдена")
    
    if not result_json_path.exists():
        raise HTTPException(status_code=404, detail="Файл result.json не найден")
    
    try:
        with open(result_json_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Файл result.json имеет неверный формат JSON")
        
        messages = []
        current_date = None
        current_sender = None
        
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                from datetime import datetime as dt
                if "T" in date_str:
                    msg_date = dt.fromisoformat(date_str.replace("Z", "+00:00"))
                elif len(date_str) == 10:
                    msg_date = dt.strptime(date_str, "%Y-%m-%d")
                else:
                    msg_date = dt.fromisoformat(date_str.replace("Z", "+00:00"))
                return msg_date
            except Exception as e:
                logger.warning(f"Ошибка парсинга даты {date_str}: {str(e)}")
                return None
        
        if "messages" in data:
            for msg in data["messages"]:
                if msg.get("type") == "message" or "text" in msg:
                    date_str = msg.get("date", msg.get("date_unixtime", ""))
                    if isinstance(date_str, (int, float)):
                        from datetime import datetime as dt
                        date_obj = dt.fromtimestamp(date_str)
                    else:
                        date_obj = parse_date(date_str)
                    
                    if date_obj:
                        date_str_formatted = date_obj.strftime("%d.%m")
                        if date_str_formatted != current_date:
                            if current_date is not None:
                                messages.append("")
                            current_date = date_str_formatted
                            messages.append(date_str_formatted)
                            current_sender = None
                    
                    from_name = msg.get("from", msg.get("from_id", "Unknown"))
                    if isinstance(from_name, dict):
                        from_name = from_name.get("name", from_name.get("id", "Unknown"))
                    
                    text_parts = msg.get("text", msg.get("text_entities", msg.get("message", "")))
                    
                    text_content = ""
                    if isinstance(text_parts, str):
                        text_content = text_parts
                    elif isinstance(text_parts, list):
                        text_lines = []
                        for item in text_parts:
                            if isinstance(item, str):
                                text_lines.append(item)
                            elif isinstance(item, dict):
                                text_lines.append(item.get("text", item.get("text_entity", item.get("type", ""))))
                        text_content = "\n".join(text_lines)
                    
                    if text_content and text_content.strip():
                        if from_name != current_sender:
                            if current_sender is not None:
                                messages.append("")
                            messages.append(f"{from_name}:")
                            current_sender = from_name
                        
                        for line in text_content.strip().split("\n"):
                            if line.strip():
                                messages.append(line.strip())
        
        output_text = "\n".join(messages)
        output_file = DOWNLOADS_DIR / f"{folder_name}_messages.txt"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_text)
        
        message_count = len([m for m in messages if ":" in m and not m.startswith("\n")])
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Сообщения экспортированы в {output_file.name}",
                "file_path": str(output_file),
                "messages_count": message_count
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта сообщений: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка экспорта: {str(e)}")

@app.post("/rename-output")
async def rename_output(old_name: str, new_name: str):
    old_path = DOWNLOADS_DIR / old_name
    new_path = DOWNLOADS_DIR / new_name
    if not old_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    if new_path.exists():
        raise HTTPException(status_code=400, detail="Файл с таким именем уже существует")
    old_path.rename(new_path)
    return JSONResponse(status_code=200, content={"message": f"Файл переименован в {new_name}"})


@app.get("/read-output")
async def read_output(name: str):
    path = DOWNLOADS_DIR / name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    if path.resolve().parent != DOWNLOADS_DIR.resolve():
        raise HTTPException(status_code=400, detail="Некорректный путь")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Файл не в текстовом формате")
    return JSONResponse(status_code=200, content={"text": text})


@app.get("/open-downloads")
async def open_downloads():
    if sys.platform == "win32":
        os.startfile(str(DOWNLOADS_DIR))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(DOWNLOADS_DIR)])
    else:
        subprocess.Popen(["xdg-open", str(DOWNLOADS_DIR)])
    return JSONResponse(status_code=200, content={"message": "Папка открыта"})


@app.get("/setup-status")
async def setup_status():
    return whisper_setup_status


@app.get("/")
async def root():
    return {"message": "Whisper API"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("SHEPTUN_PORT", "8000")))
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
