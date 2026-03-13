# Whisper Транскрибация

Локальное web-приложение для транскрибации аудио с помощью Whisper.

## Установка

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Запуск

Одной командой:

```bash
./start.sh
```

Или отдельно:

### Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

После запуска откройте браузер и перейдите по адресу `http://localhost:5173`

## Использование

1. Выберите аудиофайл (ogg, mp3, wav)
2. Нажмите кнопку "Распознать"
3. Дождитесь завершения обработки
4. Транскрибированный файл будет сохранён в папку Downloads
