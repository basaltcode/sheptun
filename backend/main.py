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
from datetime import datetime
from mutagen import File as MutagenFile
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
ALLOWED_EXTENSIONS = {".ogg", ".mp3", ".wav"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
WHISPER_PYTHON = Path(sys.executable)

progress_store: Dict[str, Dict] = {}
active_tasks: Dict[str, bool] = {}

@app.post("/transcribe")
async def transcribe_audio(
    files: List[UploadFile] = File(...),
    model: str = "small",
    language: str = "Russian",
    output_format: str = "txt",
    initial_prompt: str = "Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
):
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не выбраны")
    
    all_texts = []
    temp_files = []
    
    valid_models = ["tiny", "base", "small", "medium", "large"]
    if model not in valid_models:
        model = "small"
    
    whisper_cmd = [
        str(WHISPER_PYTHON), "-m", "whisper",
        "--model", model,
        "--output_format", output_format,
        "--output_dir", str(DOWNLOADS_DIR)
    ]
    
    if language:
        whisper_cmd.extend(["--language", language])
    
    if initial_prompt:
        whisper_cmd.extend(["--initial_prompt", initial_prompt])
    
    try:
        for file in files:
            if not file.filename:
                continue
            
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
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
                timeout=600
            )
            
            if result.returncode != 0:
                continue
            
            base_name = Path(file.filename).stem
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
            raise HTTPException(status_code=500, detail="Не удалось обработать файлы")
        
        merged_text = "\n\n".join(all_texts)
        merged_file = DOWNLOADS_DIR / "merged.txt"
        
        with open(merged_file, "w", encoding="utf-8") as f:
            f.write(merged_text)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Готово. Файл сохранён в Downloads"}
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Таймаут транскрибации")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
    finally:
        for tmp_path in temp_files:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

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
                str(WHISPER_PYTHON), "-m", "whisper",
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
            
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            process = subprocess.Popen(
                whisper_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                env=env
            )
            
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
        str(WHISPER_PYTHON), "-m", "whisper",
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
                timeout=3600
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

@app.get("/")
async def root():
    return {"message": "Whisper API"}
