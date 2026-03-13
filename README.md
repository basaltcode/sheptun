# Whisper Транскрибация

Нативное десктопное приложение для транскрибации аудио и видео с помощью OpenAI Whisper.

Поддерживаемые платформы: **macOS**, **Windows**, **Linux**.

## Требования

- **Python 3.8+** — должен быть установлен в системе
  - macOS: `brew install python3`
  - Windows: [python.org/downloads](https://python.org/downloads) (отметьте "Add to PATH")
  - Linux: `sudo apt install python3 python3-venv`

## Установка

### macOS

1. Скачайте файл `Whisper Transcription-X.X.X.dmg` (x64) или `Whisper Transcription-X.X.X-arm64.dmg` (Apple Silicon)
2. Откройте `.dmg` и перетащите приложение в папку `Applications`
3. При первом запуске: правый клик → "Открыть" (приложение не подписано)
4. При первом запуске приложение автоматически создаст Python-окружение и установит зависимости (это может занять несколько минут)

### Windows

1. Скачайте и запустите `Whisper Transcription Setup X.X.X.exe`
2. Следуйте шагам установщика (можно выбрать папку установки)
3. При первом запуске приложение автоматически установит Python-зависимости

## Использование

1. Запустите приложение
2. Выберите вкладку: **Аудио**, **Видео** или **Telegram**
3. Загрузите файлы или выберите папку Telegram
4. Настройте параметры Whisper:
   - **Модель**: tiny, base, small, medium, large (чем больше — тем точнее, но медленнее)
   - **Язык**: русский, английский, украинский или авто
   - **Формат**: txt, srt, vtt, json, tsv
5. Нажмите "Распознать"
6. Результат сохранится в папку `~/Downloads`

## Сборка из исходников

### Разработка

```bash
# Установить зависимости
npm install
cd frontend && npm install && cd ..

# Запуск в режиме разработки
npm run dev
```

### Сборка установщиков

```bash
# macOS (.dmg)
npm run build:mac

# Windows (.exe) — требуется Windows или CI
npm run build:win

# Linux (.AppImage)
npm run build:linux
```

Собранные файлы появятся в папке `release/`.

## Старый способ запуска (без Electron)

Можно запускать как веб-приложение через браузер:

```bash
./start.sh
```

Откройте `http://localhost:5173` в браузере.
