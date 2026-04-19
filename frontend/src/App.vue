<template>
  <div class="container">
    <div class="app-header">
      <img src="/logo.png" alt="Sheptun" class="app-logo" />
      <h1>Sheptun</h1>
      <button class="about-btn" @click="showAbout = true" title="О программе">v{{ appVersion }}</button>
    </div>

    <div v-if="updateDownloaded" class="update-banner">
      Доступна новая версия {{ updateVersion }}
      <button class="update-btn" @click="installUpdate()">Обновить</button>
    </div>
    <div v-else-if="updateAvailable" class="update-banner update-banner--downloading">
      Загружается обновление {{ updateVersion }}...
    </div>

    <div v-if="showAbout" class="about-overlay" @click.self="showAbout = false">
      <div class="about-dialog">
        <img src="/logo.png" alt="Sheptun" class="about-logo" />
        <h2>Sheptun</h2>
        <p class="about-version">Версия {{ appVersion }}</p>
        <p class="about-description">Транскрибация аудио и видео с помощью OpenAI Whisper</p>
        <div class="about-update-section">
          <div v-if="updateDownloaded">
            Доступна версия {{ updateVersion }}
            <button class="update-btn" @click="installUpdate()">Установить и перезапустить</button>
          </div>
          <div v-else-if="updateAvailable">
            Загружается версия {{ updateVersion }}...
          </div>
          <div v-else>
            <button
              class="check-update-btn"
              @click="checkForUpdates()"
              :disabled="updateCheckStatus === 'checking'"
            >
              {{ updateCheckStatus === 'checking' ? 'Проверяем...' : 'Проверить обновления' }}
            </button>
            <p
              v-if="updateCheckMessage"
              :class="['update-check-msg', 'update-check-msg--' + updateCheckStatus]"
            >
              {{ updateCheckMessage }}
            </p>
          </div>
        </div>
        <button class="about-close-btn" @click="showAbout = false">Закрыть</button>
      </div>
    </div>
    
    <div v-if="setupStatus.stage === 'installing'" class="setup-banner">
      <div class="setup-spinner"></div>
      {{ setupStatus.message || 'Подготовка к работе...' }}
    </div>
    <div v-else-if="setupStatus.stage === 'error'" class="setup-banner setup-banner--error">
      Ошибка настройки: {{ setupStatus.message }}
    </div>

    <div class="tabs">
      <button 
        @click="activeTab = 'audio'" 
        :class="['tab-btn', { active: activeTab === 'audio' }]"
      >
        🎵 Аудио файлы
      </button>
      <button 
        @click="activeTab = 'video'" 
        :class="['tab-btn', { active: activeTab === 'video' }]"
      >
        🎬 Видео файлы
      </button>
      <button
        @click="activeTab = 'youtube'"
        :class="['tab-btn', { active: activeTab === 'youtube' }]"
      >
        <svg class="tab-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <path fill="#FF0000" d="M23.498 6.186a3.017 3.017 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.017 3.017 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.017 3.017 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814Z"/>
          <path fill="#FFFFFF" d="M9.545 15.568V8.432L15.818 12l-6.273 3.568Z"/>
        </svg>
        YouTube
      </button>
      <button
        @click="activeTab = 'record'"
        :class="['tab-btn', { active: activeTab === 'record' }]"
      >
        🎤 Запись
      </button>
      <button
        @click="activeTab = 'telegram'"
        :class="['tab-btn', { active: activeTab === 'telegram' }]"
      >
        <svg class="tab-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
          <circle cx="12" cy="12" r="12" fill="#229ED9"/>
          <path fill="#FFFFFF" d="M5.43 11.78c3.5-1.53 5.83-2.53 7-3.02 3.33-1.39 4.03-1.63 4.48-1.64.1 0 .32.02.47.14.12.1.15.24.17.33.02.1.04.3.02.47-.18 1.92-.96 6.58-1.36 8.74-.17.91-.5 1.22-.83 1.25-.7.07-1.24-.46-1.92-.91-1.06-.7-1.66-1.13-2.7-1.81-1.2-.78-.42-1.21.26-1.91.18-.18 3.28-3.01 3.34-3.27.01-.03.01-.15-.06-.21-.07-.06-.17-.04-.25-.02-.1.02-1.72 1.09-4.84 3.21-.46.31-.87.47-1.24.46-.41-.01-1.2-.23-1.78-.42-.72-.23-1.29-.36-1.24-.76.03-.21.31-.42.85-.64Z"/>
        </svg>
        Telegram
      </button>
    </div>
    
    <div v-if="activeTab === 'audio'" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">📁 Аудио файлы</h3>
        <p class="section-description">Транскрибация аудио файлов с компьютера. Загрузите файлы в формате OGG, MP3, WAV или M4A — текст будет сохранён в папку Downloads.</p>
        <div class="upload-area">
          <input
            type="file"
            ref="fileInput"
            @change="handleFileSelect"
            accept=".ogg,.mp3,.wav,.m4a"
            :disabled="loading"
            multiple
          />
        </div>
        <div v-if="selectedFiles.length > 0" class="file-info">
          <div class="file-count">Выбрано файлов: {{ selectedFiles.length }}</div>
          <div class="file-list">
            <div v-for="file in selectedFiles" :key="file.name" class="file-item">
              {{ file.name }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="section-card">
        <h3 class="section-title">⚙️ Настройки обработки</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label for="model-select-audio">Модель:</label>
            <select id="model-select-audio" v-model="whisperSettings.model" class="model-select">
              <option value="tiny">Tiny — 39 MB, самая быстрая, низкая точность</option>
              <option value="base">Base — 74 MB, быстрая, средняя точность</option>
              <option value="small">Small — 244 MB, средняя скорость, хорошая точность</option>
              <option value="medium">Medium — 769 MB, медленная, высокая точность</option>
              <option value="large">Large — 1.5 GB, очень медленная, максимальная точность</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="language-select-audio">Язык:</label>
            <select id="language-select-audio" v-model="whisperSettings.language" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Ukrainian">Украинский</option>
              <option value="">Автоопределение</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="output-format-select-audio">Формат вывода:</label>
            <select id="output-format-select-audio" v-model="whisperSettings.outputFormat" class="model-select">
              <option value="txt">TXT</option>
              <option value="srt">SRT</option>
              <option value="vtt">VTT</option>
              <option value="json">JSON</option>
              <option value="tsv">TSV</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="task-select-audio">Задача:</label>
            <select id="task-select-audio" v-model="whisperSettings.task" class="model-select">
              <option value="transcribe">Транскрибация (speech-to-text)</option>
              <option value="translate">Перевод (speech-to-English)</option>
            </select>
          </div>
        </div>
        
        <div class="setting-item full-width">
          <label for="initial-prompt-audio">Начальный промпт:</label>
          <textarea 
            id="initial-prompt-audio" 
            v-model="whisperSettings.initialPrompt" 
            class="prompt-textarea"
            placeholder="Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
          ></textarea>
        </div>
      </div>
      
      <div class="section-card actions-card">
        <div class="buttons-group">
          <button
            @click="transcribe"
            :disabled="selectedFiles.length === 0 || loading || !setupReady"
            class="transcribe-btn primary-btn"
          >
            {{ loading ? 'Распознавание...' : '🎵 Распознать аудио' }}
          </button>
          <button
            v-if="loading && currentTaskId"
            @click="stopTranscription"
            class="stop-btn"
          >
            ⏹ Остановить
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="activeTab === 'video'" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">🎬 Видео файлы</h3>
        <p class="section-description">Создание субтитров из видео файлов с компьютера. Загрузите файлы в формате MP4, AVI, MOV, MKV или WEBM — субтитры будут сохранены в папку Downloads.</p>
        <div class="upload-area">
          <input
            type="file"
            ref="videoInput"
            @change="handleVideoSelect"
            accept=".mp4,.avi,.mov,.mkv,.webm,.flv"
            :disabled="loading"
            multiple
          />
        </div>
        <div v-if="selectedVideoFiles.length > 0" class="file-info">
          <div class="file-count">Выбрано видео: {{ selectedVideoFiles.length }}</div>
          <div class="file-list">
            <div v-for="file in selectedVideoFiles" :key="file.name" class="file-item">
              {{ file.name }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="section-card">
        <h3 class="section-title">⚙️ Настройки обработки</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label for="model-select-video">Модель:</label>
            <select id="model-select-video" v-model="whisperSettings.model" class="model-select">
              <option value="tiny">Tiny — 39 MB, самая быстрая, низкая точность</option>
              <option value="base">Base — 74 MB, быстрая, средняя точность</option>
              <option value="small">Small — 244 MB, средняя скорость, хорошая точность</option>
              <option value="medium">Medium — 769 MB, медленная, высокая точность</option>
              <option value="large">Large — 1.5 GB, очень медленная, максимальная точность</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="language-select-video">Язык:</label>
            <select id="language-select-video" v-model="whisperSettings.language" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Ukrainian">Украинский</option>
              <option value="">Автоопределение</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="output-format-select-video">Формат вывода:</label>
            <select id="output-format-select-video" v-model="whisperSettings.outputFormat" class="model-select">
              <option value="txt">TXT</option>
              <option value="srt">SRT</option>
              <option value="vtt">VTT</option>
              <option value="json">JSON</option>
              <option value="tsv">TSV</option>
            </select>
          </div>
          
          <div class="setting-item">
            <label for="task-select-video">Задача:</label>
            <select id="task-select-video" v-model="whisperSettings.task" class="model-select">
              <option value="transcribe">Транскрибация (speech-to-text)</option>
              <option value="translate">Перевод (speech-to-English)</option>
            </select>
          </div>
        </div>
        
        <div class="setting-item full-width">
          <label for="initial-prompt-video">Начальный промпт:</label>
          <textarea 
            id="initial-prompt-video" 
            v-model="whisperSettings.initialPrompt" 
            class="prompt-textarea"
            placeholder="Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
          ></textarea>
        </div>
      </div>
      
      <div class="section-card actions-card">
        <div class="buttons-group">
          <button
            @click="transcribeVideo"
            :disabled="selectedVideoFiles.length === 0 || loading || !setupReady"
            class="transcribe-btn success-btn"
          >
            {{ loading ? 'Обработка...' : '🎬 Создать субтитры для видео' }}
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="activeTab === 'youtube'" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">YouTube</h3>
        <p class="section-description">Транскрибация видео с YouTube. Вставьте ссылку — аудио будет скачано и распознано, результат сохранится в папку Downloads.</p>
        <div class="setting-item">
          <label for="youtube-url">Ссылка на видео:</label>
          <input
            id="youtube-url"
            v-model="youtubeUrl"
            type="text"
            class="youtube-url-input"
            placeholder="https://www.youtube.com/watch?v=..."
            :disabled="loading"
          />
        </div>
      </div>

      <div class="section-card">
        <h3 class="section-title">Настройки обработки</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label for="model-select-youtube">Модель:</label>
            <select id="model-select-youtube" v-model="whisperSettings.model" class="model-select">
              <option value="tiny">Tiny — 39 MB, самая быстрая, низкая точность</option>
              <option value="base">Base — 74 MB, быстрая, средняя точность</option>
              <option value="small">Small — 244 MB, средняя скорость, хорошая точность</option>
              <option value="medium">Medium — 769 MB, медленная, высокая точность</option>
              <option value="large">Large — 1.5 GB, очень медленная, максимальная точность</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="language-select-youtube">Язык:</label>
            <select id="language-select-youtube" v-model="whisperSettings.language" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Ukrainian">Украинский</option>
              <option value="">Автоопределение</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="output-format-select-youtube">Формат вывода:</label>
            <select id="output-format-select-youtube" v-model="whisperSettings.outputFormat" class="model-select">
              <option value="txt">TXT</option>
              <option value="srt">SRT</option>
              <option value="vtt">VTT</option>
              <option value="json">JSON</option>
              <option value="tsv">TSV</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="task-select-youtube">Задача:</label>
            <select id="task-select-youtube" v-model="whisperSettings.task" class="model-select">
              <option value="transcribe">Транскрибация (speech-to-text)</option>
              <option value="translate">Перевод (speech-to-English)</option>
            </select>
          </div>
        </div>

        <div class="setting-item full-width">
          <label for="initial-prompt-youtube">Начальный промпт:</label>
          <textarea
            id="initial-prompt-youtube"
            v-model="whisperSettings.initialPrompt"
            class="prompt-textarea"
            placeholder="Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
          ></textarea>
        </div>
      </div>

      <div class="section-card actions-card">
        <div class="buttons-group">
          <button
            @click="transcribeYoutube"
            :disabled="!youtubeUrl || loading || !setupReady"
            class="transcribe-btn youtube-btn"
          >
            {{ loading ? 'Обработка...' : 'Транскрибировать' }}
          </button>
          <button
            v-if="loading && currentTaskId"
            @click="stopTranscription"
            class="stop-btn"
          >
            Остановить
          </button>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'record'" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">🎤 Запись</h3>
        <p class="section-description">
          Запишите голос с микрофона, захватите системный звук (созвон, YouTube, любой звук с компьютера) или оба сразу. По окончании записи файл распознаётся Whisper и сохраняется в Downloads.
        </p>
        <div class="record-sources">
          <label class="checkbox-row">
            <input
              type="checkbox"
              v-model="recordSources.mic"
              :disabled="recordState !== 'idle' || loading"
            />
            <span>Микрофон</span>
          </label>
          <label class="checkbox-row">
            <input
              type="checkbox"
              v-model="recordSources.system"
              :disabled="recordState !== 'idle' || loading"
            />
            <span>Системный звук (созвон / YouTube)</span>
          </label>
        </div>
        <p v-if="!recordSources.mic && !recordSources.system" class="record-hint">
          Выберите хотя бы один источник звука.
        </p>
        <p v-if="recordSources.system" class="record-hint">
          При записи системного звука появится системный диалог — выберите окно или вкладку и отметьте «Поделиться звуком».
        </p>

        <div class="record-controls">
          <button
            v-if="recordState === 'idle'"
            @click="startRecording"
            :disabled="(!recordSources.mic && !recordSources.system) || loading || !setupReady"
            class="transcribe-btn record-btn"
          >
            ● Начать запись
          </button>
          <button
            v-else-if="recordState === 'recording'"
            @click="stopRecording"
            class="stop-btn record-btn"
          >
            ■ Остановить запись ({{ formatElapsedTime(recordElapsed) }})
          </button>
        </div>

        <p v-if="recordError" class="record-hint record-hint--error">{{ recordError }}</p>
      </div>

      <div class="section-card">
        <h3 class="section-title">Настройки обработки</h3>
        <div class="settings-grid">
          <div class="setting-item">
            <label for="model-select-record">Модель:</label>
            <select id="model-select-record" v-model="whisperSettings.model" class="model-select" :disabled="recordState !== 'idle' || loading">
              <option value="tiny">Tiny — 39 MB, самая быстрая, низкая точность</option>
              <option value="base">Base — 74 MB, быстрая, средняя точность</option>
              <option value="small">Small — 244 MB, средняя скорость, хорошая точность</option>
              <option value="medium">Medium — 769 MB, медленная, высокая точность</option>
              <option value="large">Large — 1.5 GB, очень медленная, максимальная точность</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="language-select-record">Язык:</label>
            <select id="language-select-record" v-model="whisperSettings.language" class="model-select" :disabled="recordState !== 'idle' || loading">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Ukrainian">Украинский</option>
              <option value="">Автоопределение</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="task-select-record">Задача:</label>
            <select id="task-select-record" v-model="whisperSettings.task" class="model-select" :disabled="recordState !== 'idle' || loading">
              <option value="transcribe">Транскрибация (speech-to-text)</option>
              <option value="translate">Перевод (speech-to-English)</option>
            </select>
          </div>
        </div>

        <div class="setting-item full-width">
          <label for="initial-prompt-record">Начальный промпт:</label>
          <textarea
            id="initial-prompt-record"
            v-model="whisperSettings.initialPrompt"
            class="prompt-textarea"
            placeholder="Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
            :disabled="recordState !== 'idle' || loading"
          ></textarea>
        </div>
      </div>

      <div v-if="recordedText" class="section-card">
        <h3 class="section-title">Распознанный текст</h3>
        <textarea
          v-model="recordedText"
          class="record-output"
          rows="10"
        ></textarea>
        <div class="buttons-group" style="margin-top: 0.75rem;">
          <button @click="copyRecordedText" class="rename-btn">Копировать</button>
          <button @click="clearRecordedText" class="rename-btn">Очистить</button>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'telegram'" class="tab-content">
      <div class="section-card" style="margin-bottom: 1.5rem;">
        <h3 class="section-title">Импорт из Telegram</h3>
        <div class="section-description">
          <p><strong>Как это работает:</strong></p>
          <ol class="instruction-steps">
            <li>Откройте <strong>Telegram Desktop</strong>, выберите нужный чат</li>
            <li>Нажмите <strong>⋮ → Экспорт истории чата</strong></li>
            <li>В настройках экспорта отметьте <strong>«Голосовые сообщения»</strong> и нажмите <strong>«Экспортировать»</strong></li>
            <li>Папка <code>ChatExport_*</code> появится в <strong>Downloads / Telegram Desktop</strong></li>
            <li>Нажмите <strong>«Загрузить папки»</strong> ниже — приложение автоматически найдёт экспорт и покажет аудиофайлы для распознавания</li>
          </ol>
          <p style="margin-top: 0.5rem; color: var(--text-secondary, #888);">Или скачайте отдельный аудиофайл и добавьте его через вкладку <strong>«Аудио»</strong>.</p>
        </div>
      </div>
      <div v-if="!selectedTelegramFolder" class="telegram-section">
        <button
          @click="loadTelegramFolders" 
          :disabled="loadingFolders"
          class="telegram-btn"
        >
          {{ loadingFolders ? 'Загрузка...' : 'Загрузить папки' }}
        </button>
        
        <div v-if="telegramFolders.length > 0" class="folders-list">
          <div 
            v-for="folder in telegramFolders" 
            :key="folder"
            @click="selectTelegramFolder(folder)"
            class="folder-item"
          >
            {{ folder }}
          </div>
        </div>
      </div>
      
      <div v-if="selectedTelegramFolder" class="telegram-section">
        <div class="section-card">
          <div class="folder-header">
            <button @click="selectedTelegramFolder = null" class="back-btn">← Назад</button>
            <h3 class="section-title">{{ selectedTelegramFolder }}</h3>
          </div>
        </div>
        
        <div v-if="telegramFiles.length > 0" class="section-card">
          <h3 class="section-title">📊 Статистика файлов</h3>
          <div class="files-summary">
            <div class="summary-item">
              <span class="summary-label">Найдено файлов:</span>
              <span class="summary-value">{{ telegramFiles.length }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Общий размер:</span>
              <span class="summary-value">{{ formatSize(telegramFilesTotalSize) }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Общее время:</span>
              <span class="summary-value">{{ formatDuration(telegramFilesTotalDuration) }}</span>
            </div>
          </div>
        </div>
        
        <div v-if="telegramFiles.length > 0" class="section-card">
          <h3 class="section-title">📁 Список файлов</h3>
          <div class="files-list-container">
            <div v-for="file in telegramFiles" :key="file.name" class="file-item-detailed">
              <div class="file-name">{{ shortenFileName(file.name) }}</div>
              <div class="file-meta">
                <span class="file-size">{{ formatSize(file.size) }}</span>
                <span class="file-duration">{{ formatDuration(file.duration || 0) }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="section-card" v-if="!loading">
          <h3 class="section-title">⚙️ Настройки обработки</h3>
          <div class="settings-grid">
            <div class="setting-item">
              <label for="model-select">Модель:</label>
              <select id="model-select" v-model="whisperSettings.model" class="model-select">
                <option value="tiny">Tiny (быстрая, низкая точность)</option>
                <option value="base">Base (быстрая, средняя точность)</option>
                <option value="small">Small (средняя скорость, хорошая точность)</option>
                <option value="medium">Medium (медленная, высокая точность)</option>
                <option value="large">Large (очень медленная, максимальная точность)</option>
              </select>
            </div>
            
            <div class="setting-item">
              <label for="language-select-telegram">Язык:</label>
              <select id="language-select-telegram" v-model="whisperSettings.language" class="model-select">
                <option value="Russian">Русский</option>
                <option value="English">Английский</option>
                <option value="Ukrainian">Украинский</option>
                <option value="">Автоопределение</option>
              </select>
            </div>
            
            <div class="setting-item">
              <label for="output-format-select-telegram">Формат вывода:</label>
              <select id="output-format-select-telegram" v-model="whisperSettings.outputFormat" class="model-select">
                <option value="txt">TXT</option>
                <option value="srt">SRT</option>
                <option value="vtt">VTT</option>
                <option value="json">JSON</option>
                <option value="tsv">TSV</option>
              </select>
            </div>
            
            <div class="setting-item">
              <label for="task-select-telegram">Задача:</label>
              <select id="task-select-telegram" v-model="whisperSettings.task" class="model-select">
                <option value="transcribe">Транскрибация</option>
                <option value="translate">Перевод</option>
              </select>
            </div>
          </div>
          
          <div class="setting-item full-width">
            <label for="initial-prompt-telegram">Начальный промпт:</label>
            <textarea 
              id="initial-prompt-telegram" 
              v-model="whisperSettings.initialPrompt" 
              class="prompt-textarea"
              placeholder="Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией."
            ></textarea>
          </div>
        </div>
        
        <div class="section-card actions-card">
          <div class="buttons-group">
            <button
              v-if="!loading"
              @click="transcribeTelegram"
              :disabled="telegramFiles.length === 0 || !setupReady"
              class="transcribe-btn primary-btn"
            >
              🎵 Распознать все голосовые
            </button>
            <button
              v-if="!loading"
              @click="exportTelegramMessages(selectedTelegramFolder)"
              :disabled="!selectedTelegramFolder"
              class="transcribe-btn info-btn"
            >
              💬 Сохранить текст переписки
            </button>
            <button
              v-if="loading"
              @click="stopTranscription"
              :disabled="!currentTaskId"
              class="stop-btn"
            >
              ⏹ Остановить
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="loader">
      <div class="wave-animation">
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
      </div>
      <p v-if="progress.modelDownloadProgress !== undefined && progress.modelDownloadProgress < 100">
        {{ progress.message }}
      </p>
      <p v-else-if="progress.status === 'processing'">
        {{ progress.message }}
      </p>
      <p v-else-if="progress.status === 'downloading'">{{ progress.message }}</p>
      <p v-else-if="progress.status === 'starting'">Начало обработки...</p>
      <p v-else>Обработка файлов...</p>

      <div class="progress-section">
        <div v-if="progress.modelDownloadProgress !== undefined && progress.modelDownloadProgress < 100" class="model-download-section">
          <div class="current-file-info">
            <span>Загрузка модели (нужно только при первом использовании)</span>
            <span>{{ progress.modelDownloadProgress }}%</span>
          </div>
          <div class="progress-bar model-download-bar">
            <div class="progress-fill model-download-fill" :style="{ width: progress.modelDownloadProgress + '%' }"></div>
          </div>
        </div>

        <div v-if="progress.total > 0" class="progress-info">
          <span>Общий прогресс: {{ progress.current }} / {{ progress.total }} файлов</span>
          <span>{{ progressPercent }}%</span>
        </div>

        <div class="time-info">
          <div class="time-item">
            <span class="time-label">Прошло времени:</span>
            <span class="time-value">{{ formatElapsedTime(elapsedTime) }}</span>
          </div>
          <div v-if="estimatedRemaining !== null && estimatedRemaining > 0" class="time-item">
            <span class="time-label">Осталось примерно:</span>
            <span class="time-value">{{ formatElapsedTime(estimatedRemaining) }}</span>
          </div>
        </div>
        <div v-if="progress.total > 0" class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>

        <div v-if="progress.currentFile && !(progress.modelDownloadProgress !== undefined && progress.modelDownloadProgress < 100)" class="current-file-section">
          <div class="current-file-info">
            <span>Текущий файл: {{ shortenFileName(progress.currentFile) }}</span>
            <span>{{ progress.currentFileProgress || 0 }}%</span>
          </div>
          <div class="progress-bar-small">
            <div class="progress-fill-small" :style="{ width: (progress.currentFileProgress || 0) + '%' }"></div>
          </div>
        </div>
        
        <div v-if="progress.whisperLogs && progress.whisperLogs.length > 0" class="whisper-logs-section">
          <div class="logs-header">Логи Whisper:</div>
          <div class="logs-container">
            <div v-for="(log, index) in progress.whisperLogs" :key="index" class="log-line">
              {{ log }}
            </div>
          </div>
        </div>
        
        <div v-if="progress.lastLog" class="last-log">
          {{ progress.lastLog }}
        </div>
      </div>
      
      <button
        v-if="currentTaskId"
        @click="stopTranscription"
        class="stop-btn"
        style="margin-top: 1rem;"
      >
        Остановить
      </button>
    </div>
    
    <div v-if="message" :class="['message', messageType]">
      <div v-if="messageType === 'success' && outputFileName" class="result-block">
        <div class="result-text">{{ message }}</div>
        <div class="result-file">
          <label class="result-label">Имя файла:</label>
          <div class="rename-row">
            <input
              v-model="outputFileName"
              class="rename-input"
              @keydown.enter="renameOutput"
            />
            <button @click="renameOutput" class="rename-btn" :disabled="outputFileName === outputFileNameOriginal">Переименовать</button>
          </div>
        </div>
        <button @click="openDownloads" class="open-folder-btn">Открыть папку Downloads</button>
      </div>
      <template v-else>{{ message }}</template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { apiUrl } from './api.js'

const isTauri = () => typeof window !== 'undefined' && !!window.__TAURI_INTERNALS__

const fileInput = ref(null)
const videoInput = ref(null)
const selectedFiles = ref([])
const selectedVideoFiles = ref([])
const loading = ref(false)
const message = ref('')
const messageType = ref('')
const activeTab = ref('audio')
const progress = ref({ current: 0, total: 0, currentFile: '', currentFileProgress: 0, message: '', status: '', whisperLogs: [], lastLog: '', elapsed_seconds: 0, estimated_remaining_seconds: null, start_time: null })
const startTime = ref(null)
const elapsedTime = ref(0)
const estimatedRemaining = ref(null)

const appVersion = ref('')
const updateAvailable = ref(false)
const updateDownloaded = ref(false)
const updateVersion = ref('')
const showAbout = ref(false)
const updateCheckStatus = ref('idle')
const updateCheckMessage = ref('')
const setupStatus = ref({ stage: 'pending', message: '' })

const installUpdate = async () => {
  if (!isTauri()) return
  try {
    const { relaunch } = await import('@tauri-apps/plugin-process')
    await relaunch()
  } catch (err) {
    console.error('installUpdate failed:', err)
  }
}

const checkForUpdates = async () => {
  if (!isTauri()) {
    updateCheckStatus.value = 'error'
    updateCheckMessage.value = 'Обновления работают только в десктоп-приложении'
    return
  }
  updateCheckStatus.value = 'checking'
  updateCheckMessage.value = ''
  try {
    const { check } = await import('@tauri-apps/plugin-updater')
    const update = await check()
    if (update?.available) {
      updateAvailable.value = true
      updateVersion.value = update.version
      updateCheckStatus.value = 'available'
      updateCheckMessage.value = `Доступна версия ${update.version} — начинаем загрузку...`
      await update.downloadAndInstall((event) => {
        if (event.event === 'Finished') {
          updateDownloaded.value = true
        }
      })
    } else {
      updateCheckStatus.value = 'uptodate'
      updateCheckMessage.value = `У вас последняя версия ${appVersion.value}`
    }
  } catch (err) {
    console.error('checkForUpdates failed:', err)
    updateCheckStatus.value = 'error'
    updateCheckMessage.value = 'Не удалось проверить обновления — проверьте интернет и попробуйте позже'
  }
}

const telegramFolders = ref([])
const selectedTelegramFolder = ref(null)
const telegramFiles = ref([])
const telegramFilesTotalSize = ref(0)
const telegramFilesTotalDuration = ref(0)
const loadingFolders = ref(false)
const currentTaskId = ref(null)
const youtubeUrl = ref('')
const outputFileName = ref('')
const outputFileNameOriginal = ref('')
const eventSource = ref(null)
const whisperSettings = ref({
  model: 'small',
  language: 'Russian',
  outputFormat: 'txt',
  initialPrompt: 'Это связная лекция на русском языке. Оформляй текст абзацами, с нормальной пунктуацией.',
  task: 'transcribe'
})

const recordSources = ref({ mic: true, system: false })
const recordState = ref('idle')
const recordError = ref('')
const recordedText = ref('')
const recordElapsed = ref(0)
const mediaRecorderRef = ref(null)
const recordedChunks = ref([])
const activeStreams = ref([])
const activeAudioContext = ref(null)
const recordTimerId = ref(null)
const recordStartedAt = ref(0)
const recordMimeType = ref('')

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    selectedFiles.value = files
    message.value = ''
  }
}

const handleVideoSelect = (event) => {
  const files = Array.from(event.target.files)
  if (files.length > 0) {
    selectedVideoFiles.value = files
    message.value = ''
  }
}

const transcribeVideo = async () => {
  if (selectedVideoFiles.value.length === 0) return
  
  loading.value = true
  message.value = ''
  messageType.value = ''
  
  const formData = new FormData()
  selectedVideoFiles.value.forEach(file => {
    formData.append('files', file)
  })
  
  try {
    const params = new URLSearchParams({
      model: whisperSettings.value.model === 'small' ? 'medium' : whisperSettings.value.model,
      language: whisperSettings.value.task === 'translate' ? 'English' : (whisperSettings.value.language || ''),
      output_format: whisperSettings.value.outputFormat === 'txt' ? 'srt' : whisperSettings.value.outputFormat,
      task: whisperSettings.value.task
    })
    const response = await fetch(`${await apiUrl('/transcribe/video')}?${params.toString()}`, {
      method: 'POST',
      body: formData
    })
    
    const data = await response.json()
    
    if (response.ok) {
      message.value = data.message
      messageType.value = 'success'
    } else {
      message.value = data.detail || 'Произошла ошибка'
      messageType.value = 'error'
    }
  } catch (error) {
    message.value = 'Ошибка соединения с сервером'
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const transcribeYoutube = async () => {
  if (!youtubeUrl.value) return

  loading.value = true
  message.value = ''
  messageType.value = ''
  progress.value = { current: 0, total: 0, currentFile: '', currentFileProgress: 0, message: '', status: '', whisperLogs: [], lastLog: '', elapsed_seconds: 0, estimated_remaining_seconds: null, start_time: null }
  startTime.value = null
  elapsedTime.value = 0
  estimatedRemaining.value = null
  currentTaskId.value = null
  outputFileName.value = ''
  outputFileNameOriginal.value = ''

  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }

  try {
    const params = new URLSearchParams({
      url: youtubeUrl.value,
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt,
      task: whisperSettings.value.task
    })

    const response = await fetch(`${await apiUrl('/transcribe/youtube')}?${params.toString()}`, {
      method: 'POST'
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Ошибка при запуске транскрибации')
    }

    const data = await response.json()

    if (!data.task_id) {
      throw new Error('Не получен task_id от сервера')
    }

    currentTaskId.value = data.task_id

    eventSource.value = new EventSource(await apiUrl(`/progress/${data.task_id}`))

    eventSource.value.onmessage = (event) => {
      try {
        const progressData = JSON.parse(event.data)
        progress.value = {
          current: progressData.current || 0,
          total: progressData.total || 0,
          currentFile: progressData.current_file || '',
          currentFileProgress: progressData.current_file_progress || 0,
          modelDownloadProgress: progressData.model_download_progress,
          message: progressData.message || '',
          status: progressData.status || '',
          whisperLogs: progressData.whisper_logs || [],
          lastLog: progressData.last_log || '',
          elapsed_seconds: progressData.elapsed_seconds || 0,
          estimated_remaining_seconds: progressData.estimated_remaining_seconds || null,
          start_time: progressData.start_time || null
        }

        if (progressData.start_time && !startTime.value) {
          startTime.value = progressData.start_time
        }
        if (progressData.elapsed_seconds !== undefined) {
          elapsedTime.value = progressData.elapsed_seconds
        }
        estimatedRemaining.value = progressData.estimated_remaining_seconds || null

        if (progressData.status === 'completed') {
          playCompletionSound()
          message.value = progressData.message || 'Обработка завершена'
          messageType.value = 'success'
          outputFileName.value = progressData.output_file || ''
          outputFileNameOriginal.value = progressData.output_file || ''
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        } else if (progressData.status === 'error' || progressData.status === 'cancelled') {
          message.value = progressData.message || (progressData.status === 'cancelled' ? 'Обработка остановлена' : 'Произошла ошибка')
          messageType.value = progressData.status === 'cancelled' ? 'warning' : 'error'
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        }
      } catch (parseError) {
        console.error('Ошибка парсинга данных прогресса:', parseError)
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('SSE connection error:', error)
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
      if (progress.value.status !== 'completed' && progress.value.status !== 'error') {
        message.value = 'Ошибка соединения с сервером'
        messageType.value = 'error'
        loading.value = false
        currentTaskId.value = null
      }
    }
  } catch (error) {
    console.error('Ошибка при запуске транскрибации YouTube:', error)
    message.value = error.message || 'Ошибка соединения с сервером'
    messageType.value = 'error'
    loading.value = false
    currentTaskId.value = null
  }
}

const exportTelegramMessages = async (folderName) => {
  loading.value = true
  message.value = ''
  messageType.value = ''
  
  try {
    const response = await fetch(await apiUrl(`/telegram/folders/${encodeURIComponent(folderName)}/messages`))
    const data = await response.json()
    
    if (response.ok) {
      message.value = data.message
      messageType.value = 'success'
    } else {
      message.value = data.detail || 'Ошибка экспорта сообщений'
      messageType.value = 'error'
    }
  } catch (error) {
    message.value = 'Ошибка соединения с сервером'
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}

const transcribe = async () => {
  if (selectedFiles.value.length === 0) return

  loading.value = true
  message.value = ''
  messageType.value = ''
  progress.value = { current: 0, total: 0, currentFile: '', currentFileProgress: 0, message: '', status: '', whisperLogs: [], lastLog: '', elapsed_seconds: 0, estimated_remaining_seconds: null, start_time: null }
  startTime.value = null
  elapsedTime.value = 0
  estimatedRemaining.value = null
  currentTaskId.value = null
  outputFileName.value = ''
  outputFileNameOriginal.value = ''

  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }

  const formData = new FormData()
  selectedFiles.value.forEach(file => {
    formData.append('files', file)
  })

  try {
    const params = new URLSearchParams({
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt,
      task: whisperSettings.value.task
    })
    const response = await fetch(`${await apiUrl('/transcribe')}?${params.toString()}`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Ошибка при запуске транскрибации')
    }

    const data = await response.json()

    if (!data.task_id) {
      throw new Error('Не получен task_id от сервера')
    }

    currentTaskId.value = data.task_id

    eventSource.value = new EventSource(await apiUrl(`/progress/${data.task_id}`))

    eventSource.value.onmessage = (event) => {
      try {
        const progressData = JSON.parse(event.data)
        progress.value = {
          current: progressData.current || 0,
          total: progressData.total || 0,
          currentFile: progressData.current_file || '',
          currentFileProgress: progressData.current_file_progress || 0,
          modelDownloadProgress: progressData.model_download_progress,
          message: progressData.message || '',
          status: progressData.status || '',
          whisperLogs: progressData.whisper_logs || [],
          lastLog: progressData.last_log || '',
          elapsed_seconds: progressData.elapsed_seconds || 0,
          estimated_remaining_seconds: progressData.estimated_remaining_seconds || null,
          start_time: progressData.start_time || null
        }

        if (progressData.start_time && !startTime.value) {
          startTime.value = progressData.start_time
        }
        if (progressData.elapsed_seconds !== undefined) {
          elapsedTime.value = progressData.elapsed_seconds
        }
        estimatedRemaining.value = progressData.estimated_remaining_seconds || null

        if (progressData.status === 'completed') {
          playCompletionSound()
          message.value = progressData.message || 'Обработка завершена'
          messageType.value = 'success'
          outputFileName.value = progressData.output_file || ''
          outputFileNameOriginal.value = progressData.output_file || ''
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        } else if (progressData.status === 'error' || progressData.status === 'cancelled') {
          message.value = progressData.message || (progressData.status === 'cancelled' ? 'Обработка остановлена' : 'Произошла ошибка')
          messageType.value = progressData.status === 'cancelled' ? 'warning' : 'error'
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        }
      } catch (parseError) {
        console.error('Ошибка парсинга данных прогресса:', parseError)
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('SSE connection error:', error)
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
      if (progress.value.status !== 'completed' && progress.value.status !== 'error') {
        message.value = 'Ошибка соединения с сервером'
        messageType.value = 'error'
        loading.value = false
        currentTaskId.value = null
      }
    }
  } catch (error) {
    console.error('Ошибка при запуске транскрибации:', error)
    message.value = error.message || 'Ошибка соединения с сервером'
    messageType.value = 'error'
    loading.value = false
    currentTaskId.value = null
  }
}

const loadTelegramFolders = async () => {
  loadingFolders.value = true
  telegramFolders.value = []
  
  try {
    const response = await fetch(await apiUrl('/telegram/folders'))
    const data = await response.json()
    
    if (response.ok) {
      telegramFolders.value = data.folders || []
    } else {
      message.value = data.detail || 'Ошибка загрузки папок'
      messageType.value = 'error'
    }
  } catch (error) {
    message.value = 'Ошибка соединения с сервером'
    messageType.value = 'error'
  } finally {
    loadingFolders.value = false
  }
}

const selectTelegramFolder = async (folderName) => {
  selectedTelegramFolder.value = folderName
  telegramFiles.value = []
  telegramFilesTotalSize.value = 0
  telegramFilesTotalDuration.value = 0
  
  try {
    const response = await fetch(await apiUrl(`/telegram/folders/${encodeURIComponent(folderName)}/files`))
    const data = await response.json()
    
    if (response.ok) {
      telegramFiles.value = data.files || []
      telegramFilesTotalSize.value = data.total_size || 0
      
      if (data.files && data.files.length > 0) {
        telegramFilesTotalDuration.value = data.files.reduce((sum, f) => sum + (f.duration || 0), 0)
      }
    } else {
      message.value = data.detail || 'Ошибка загрузки файлов'
      messageType.value = 'error'
    }
  } catch (error) {
    message.value = 'Ошибка соединения с сервером'
    messageType.value = 'error'
  }
}

const transcribeTelegram = async () => {
  if (!selectedTelegramFolder.value) return
  
  loading.value = true
  message.value = ''
  messageType.value = ''
  progress.value = { current: 0, total: 0, currentFile: '', currentFileProgress: 0, message: '', status: '', whisperLogs: [], lastLog: '', elapsed_seconds: 0, estimated_remaining_seconds: null, start_time: null }
  startTime.value = null
  elapsedTime.value = 0
  estimatedRemaining.value = null
  currentTaskId.value = null
  outputFileName.value = ''
  outputFileNameOriginal.value = ''

  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }
  
  try {
    const params = new URLSearchParams({
      folder_name: selectedTelegramFolder.value,
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt
    })
    
    const response = await fetch(`${await apiUrl('/transcribe/telegram')}?${params.toString()}`, {
      method: 'POST'
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Ошибка при запуске транскрибации')
    }
    
    const data = await response.json()
    
    if (!data.task_id) {
      throw new Error('Не получен task_id от сервера')
    }
    
    currentTaskId.value = data.task_id
    
    eventSource.value = new EventSource(await apiUrl(`/progress/${data.task_id}`))
    
      eventSource.value.onmessage = (event) => {
        try {
          const progressData = JSON.parse(event.data)
          progress.value = {
            current: progressData.current || 0,
            total: progressData.total || 0,
            currentFile: progressData.current_file || '',
            currentFileProgress: progressData.current_file_progress || 0,
            message: progressData.message || '',
            status: progressData.status || '',
            whisperLogs: progressData.whisper_logs || [],
            lastLog: progressData.last_log || '',
            elapsed_seconds: progressData.elapsed_seconds || 0,
            estimated_remaining_seconds: progressData.estimated_remaining_seconds || null,
            start_time: progressData.start_time || null
          }
          
          if (progressData.start_time && !startTime.value) {
            startTime.value = progressData.start_time
          }
          
          if (progressData.elapsed_seconds !== undefined) {
            elapsedTime.value = progressData.elapsed_seconds
          }
          estimatedRemaining.value = progressData.estimated_remaining_seconds || null
        
        if (progressData.status === 'completed') {
          playCompletionSound()
          message.value = progressData.message || 'Обработка завершена'
          messageType.value = 'success'
          outputFileName.value = progressData.output_file || ''
          outputFileNameOriginal.value = progressData.output_file || ''
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        } else if (progressData.status === 'error' || progressData.status === 'cancelled') {
          message.value = progressData.message || (progressData.status === 'cancelled' ? 'Обработка остановлена' : 'Произошла ошибка')
          messageType.value = progressData.status === 'cancelled' ? 'warning' : 'error'
          loading.value = false
          if (eventSource.value) {
            eventSource.value.close()
            eventSource.value = null
          }
          currentTaskId.value = null
        }
      } catch (parseError) {
        console.error('Ошибка парсинга данных прогресса:', parseError)
      }
    }
    
    eventSource.value.onerror = (error) => {
      console.error('SSE connection error:', error)
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
      if (progress.value.status !== 'completed' && progress.value.status !== 'error') {
        message.value = 'Ошибка соединения с сервером'
        messageType.value = 'error'
        loading.value = false
        currentTaskId.value = null
      }
    }
  } catch (error) {
    console.error('Ошибка при запуске транскрибации:', error)
    message.value = error.message || 'Ошибка соединения с сервером'
    messageType.value = 'error'
    loading.value = false
    currentTaskId.value = null
  }
}

const stopTranscription = async () => {
  if (!currentTaskId.value) return

  try {
    // Try both stop endpoints
    const urls = [
      await apiUrl(`/transcribe/${currentTaskId.value}/stop`),
      await apiUrl(`/transcribe/telegram/${currentTaskId.value}/stop`)
    ]
    await Promise.allSettled(urls.map(url => fetch(url, { method: 'POST' })))
  } catch (error) {
    console.error('Ошибка остановки:', error)
  }
}

const pickRecorderMimeType = () => {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4;codecs=mp4a.40.2',
    'audio/mp4',
    'audio/ogg;codecs=opus'
  ]
  if (typeof MediaRecorder === 'undefined') return ''
  for (const type of candidates) {
    try {
      if (MediaRecorder.isTypeSupported(type)) return type
    } catch (_) {}
  }
  return ''
}

const mimeToExt = (mime) => {
  if (!mime) return 'webm'
  if (mime.includes('webm')) return 'webm'
  if (mime.includes('mp4')) return 'mp4'
  if (mime.includes('ogg')) return 'ogg'
  return 'webm'
}

const releaseRecordingResources = () => {
  if (recordTimerId.value) {
    clearInterval(recordTimerId.value)
    recordTimerId.value = null
  }
  for (const stream of activeStreams.value) {
    try {
      stream.getTracks().forEach(t => t.stop())
    } catch (_) {}
  }
  activeStreams.value = []
  if (activeAudioContext.value) {
    try { activeAudioContext.value.close() } catch (_) {}
    activeAudioContext.value = null
  }
  mediaRecorderRef.value = null
}

const buildMixedStream = async () => {
  const streams = []
  let systemVideoTrack = null

  if (recordSources.value.system) {
    const displayStream = await navigator.mediaDevices.getDisplayMedia({
      video: true,
      audio: true
    })
    const audioTracks = displayStream.getAudioTracks()
    if (audioTracks.length === 0) {
      displayStream.getTracks().forEach(t => t.stop())
      throw new Error('Не удалось получить системный звук. В диалоге шаринга отметьте «Поделиться звуком» (обычно работает при выборе вкладки браузера).')
    }
    systemVideoTrack = displayStream.getVideoTracks()[0]
    if (systemVideoTrack) systemVideoTrack.stop()
    streams.push(displayStream)
  }

  if (recordSources.value.mic) {
    const micStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    streams.push(micStream)
  }

  activeStreams.value = streams

  if (streams.length === 1) {
    return new MediaStream(streams[0].getAudioTracks())
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext
  const ctx = new AudioCtx()
  activeAudioContext.value = ctx
  const dest = ctx.createMediaStreamDestination()
  for (const stream of streams) {
    if (stream.getAudioTracks().length === 0) continue
    const source = ctx.createMediaStreamSource(new MediaStream(stream.getAudioTracks()))
    source.connect(dest)
  }
  return dest.stream
}

const startRecording = async () => {
  if (recordState.value !== 'idle') return
  if (!recordSources.value.mic && !recordSources.value.system) return

  recordError.value = ''
  recordedChunks.value = []
  recordElapsed.value = 0

  try {
    const mixedStream = await buildMixedStream()
    const mimeType = pickRecorderMimeType()
    recordMimeType.value = mimeType
    const recorder = mimeType
      ? new MediaRecorder(mixedStream, { mimeType })
      : new MediaRecorder(mixedStream)
    mediaRecorderRef.value = recorder

    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) recordedChunks.value.push(event.data)
    }
    recorder.onstop = async () => {
      const chunks = recordedChunks.value
      const blob = new Blob(chunks, { type: recordMimeType.value || 'audio/webm' })
      releaseRecordingResources()
      recordState.value = 'idle'
      if (blob.size === 0) {
        recordError.value = 'Запись пустая — ничего не отправлено.'
        return
      }
      await transcribeRecordedBlob(blob)
    }

    recorder.start()
    recordState.value = 'recording'
    recordStartedAt.value = Date.now()
    recordTimerId.value = setInterval(() => {
      recordElapsed.value = Math.floor((Date.now() - recordStartedAt.value) / 1000)
    }, 500)
  } catch (err) {
    console.error('startRecording failed:', err)
    releaseRecordingResources()
    recordState.value = 'idle'
    if (err && err.name === 'NotAllowedError') {
      recordError.value = 'Доступ к записи отклонён. Проверьте разрешения системы.'
    } else {
      recordError.value = err?.message || 'Не удалось начать запись.'
    }
  }
}

const stopRecording = () => {
  const recorder = mediaRecorderRef.value
  if (!recorder) {
    releaseRecordingResources()
    recordState.value = 'idle'
    return
  }
  try {
    if (recorder.state !== 'inactive') recorder.stop()
  } catch (err) {
    console.error('stopRecording failed:', err)
    releaseRecordingResources()
    recordState.value = 'idle'
  }
}

const transcribeRecordedBlob = async (blob) => {
  loading.value = true
  message.value = ''
  messageType.value = ''
  progress.value = { current: 0, total: 0, currentFile: '', currentFileProgress: 0, message: '', status: '', whisperLogs: [], lastLog: '', elapsed_seconds: 0, estimated_remaining_seconds: null, start_time: null }
  startTime.value = null
  elapsedTime.value = 0
  estimatedRemaining.value = null
  currentTaskId.value = null
  outputFileName.value = ''
  outputFileNameOriginal.value = ''

  if (eventSource.value) {
    eventSource.value.close()
    eventSource.value = null
  }

  const ext = mimeToExt(recordMimeType.value)
  const ts = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  const filename = `dictation-${ts.getFullYear()}-${pad(ts.getMonth() + 1)}-${pad(ts.getDate())}-${pad(ts.getHours())}${pad(ts.getMinutes())}${pad(ts.getSeconds())}.${ext}`

  const formData = new FormData()
  formData.append('files', new File([blob], filename, { type: blob.type || `audio/${ext}` }))

  try {
    const params = new URLSearchParams({
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: 'txt',
      initial_prompt: whisperSettings.value.initialPrompt,
      task: whisperSettings.value.task
    })
    const response = await fetch(`${await apiUrl('/transcribe')}?${params.toString()}`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || 'Ошибка при запуске транскрибации')
    }

    const data = await response.json()
    if (!data.task_id) throw new Error('Не получен task_id от сервера')

    currentTaskId.value = data.task_id
    eventSource.value = new EventSource(await apiUrl(`/progress/${data.task_id}`))

    eventSource.value.onmessage = async (event) => {
      try {
        const progressData = JSON.parse(event.data)
        progress.value = {
          current: progressData.current || 0,
          total: progressData.total || 0,
          currentFile: progressData.current_file || '',
          currentFileProgress: progressData.current_file_progress || 0,
          modelDownloadProgress: progressData.model_download_progress,
          message: progressData.message || '',
          status: progressData.status || '',
          whisperLogs: progressData.whisper_logs || [],
          lastLog: progressData.last_log || '',
          elapsed_seconds: progressData.elapsed_seconds || 0,
          estimated_remaining_seconds: progressData.estimated_remaining_seconds || null,
          start_time: progressData.start_time || null
        }
        if (progressData.start_time && !startTime.value) startTime.value = progressData.start_time
        if (progressData.elapsed_seconds !== undefined) elapsedTime.value = progressData.elapsed_seconds
        estimatedRemaining.value = progressData.estimated_remaining_seconds || null

        if (progressData.status === 'completed') {
          playCompletionSound()
          message.value = progressData.message || 'Обработка завершена'
          messageType.value = 'success'
          outputFileName.value = progressData.output_file || ''
          outputFileNameOriginal.value = progressData.output_file || ''
          loading.value = false
          if (eventSource.value) { eventSource.value.close(); eventSource.value = null }
          currentTaskId.value = null
          if (outputFileName.value) {
            try {
              const textResp = await fetch(`${await apiUrl('/read-output')}?name=${encodeURIComponent(outputFileName.value)}`)
              if (textResp.ok) {
                const textData = await textResp.json()
                recordedText.value = textData.text || ''
              }
            } catch (readErr) {
              console.error('read-output failed:', readErr)
            }
          }
        } else if (progressData.status === 'error' || progressData.status === 'cancelled') {
          message.value = progressData.message || (progressData.status === 'cancelled' ? 'Обработка остановлена' : 'Произошла ошибка')
          messageType.value = progressData.status === 'cancelled' ? 'warning' : 'error'
          loading.value = false
          if (eventSource.value) { eventSource.value.close(); eventSource.value = null }
          currentTaskId.value = null
        }
      } catch (parseError) {
        console.error('Ошибка парсинга данных прогресса:', parseError)
      }
    }

    eventSource.value.onerror = (error) => {
      console.error('SSE connection error:', error)
      if (eventSource.value) { eventSource.value.close(); eventSource.value = null }
      if (progress.value.status !== 'completed' && progress.value.status !== 'error') {
        message.value = 'Ошибка соединения с сервером'
        messageType.value = 'error'
        loading.value = false
        currentTaskId.value = null
      }
    }
  } catch (error) {
    console.error('transcribeRecordedBlob failed:', error)
    message.value = error.message || 'Ошибка соединения с сервером'
    messageType.value = 'error'
    loading.value = false
    currentTaskId.value = null
  }
}

const copyRecordedText = async () => {
  if (!recordedText.value) return
  try {
    await navigator.clipboard.writeText(recordedText.value)
  } catch (err) {
    console.error('copyRecordedText failed:', err)
  }
}

const clearRecordedText = () => {
  recordedText.value = ''
}

const renameOutput = async () => {
  if (!outputFileName.value || outputFileName.value === outputFileNameOriginal.value) return
  try {
    const params = new URLSearchParams({
      old_name: outputFileNameOriginal.value,
      new_name: outputFileName.value
    })
    const response = await fetch(`${await apiUrl('/rename-output')}?${params.toString()}`, { method: 'POST' })
    const data = await response.json()
    if (response.ok) {
      outputFileNameOriginal.value = outputFileName.value
      message.value = data.message
    } else {
      message.value = data.detail || 'Ошибка переименования'
      messageType.value = 'error'
    }
  } catch (error) {
    message.value = 'Ошибка соединения с сервером'
    messageType.value = 'error'
  }
}

const openDownloads = async () => {
  try {
    await fetch(await apiUrl('/open-downloads'))
  } catch (error) {
    console.error('Ошибка открытия папки:', error)
  }
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds) return '0 сек'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}ч ${minutes}м ${secs}с`
  } else if (minutes > 0) {
    return `${minutes}м ${secs}с`
  } else {
    return `${secs}с`
  }
}

const formatElapsedTime = (seconds) => {
  if (!seconds && seconds !== 0) return '0 сек'
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}ч ${minutes}м ${secs}с`
  } else if (minutes > 0) {
    return `${minutes}м ${secs}с`
  } else {
    return `${secs}с`
  }
}

const shortenFileName = (fileName) => {
  if (!fileName) return ''
  if (fileName.length <= 50) return fileName
  return fileName.substring(0, 30) + '...' + fileName.substring(fileName.length - 17)
}

const setupReady = computed(() => setupStatus.value.stage === 'ready')

const progressPercent = computed(() => {
  if (progress.value.total === 0) return 0
  return Math.round((progress.value.current / progress.value.total) * 100)
})

let timerInterval = null

onMounted(async () => {
  timerInterval = setInterval(() => {
    if (loading.value && startTime.value) {
      const now = Date.now() / 1000
      elapsedTime.value = Math.floor(now - startTime.value)
    }
  }, 1000)

  if (isTauri()) {
    try {
      const { getVersion } = await import('@tauri-apps/api/app')
      appVersion.value = await getVersion()
    } catch (err) {
      console.error('getVersion failed:', err)
    }
  }
  // Poll setup status until ready
  let setupRetries = 0
  const pollSetup = async () => {
    try {
      const url = await apiUrl('/setup-status')
      const res = await fetch(url)
      const data = await res.json()
      setupStatus.value = data
      setupRetries = 0
      if (data.stage !== 'ready') {
        setTimeout(pollSetup, 2000)
      }
    } catch {
      setupRetries++
      if (setupRetries > 30) {
        setupStatus.value = { stage: 'error', message: 'Нет связи с сервером. Попробуйте перезапустить приложение.' }
      } else {
        setTimeout(pollSetup, 2000)
      }
    }
  }
  pollSetup()

  if (isTauri()) {
    try {
      const { check } = await import('@tauri-apps/plugin-updater')
      const update = await check()
      if (update?.available) {
        updateAvailable.value = true
        updateVersion.value = update.version
        update.downloadAndInstall((event) => {
          if (event.event === 'Finished') {
            updateDownloaded.value = true
          }
        }).catch((err) => console.error('auto update failed:', err))
      }
    } catch (err) {
      console.error('check updates failed:', err)
    }
  }
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})

const playCompletionSound = () => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const oscillator = audioContext.createOscillator()
  const gainNode = audioContext.createGain()
  
  oscillator.connect(gainNode)
  gainNode.connect(audioContext.destination)
  
  oscillator.frequency.value = 800
  oscillator.type = 'sine'
  
  gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
  gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5)
  
  oscillator.start(audioContext.currentTime)
  oscillator.stop(audioContext.currentTime + 0.5)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #f5f5f5;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.container {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  max-width: 900px;
  width: 100%;
  text-align: left;
}

.app-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  position: relative;
}

.app-logo {
  width: 40px;
  height: 40px;
}

h1 {
  margin: 0;
  color: #333;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #eee;
}

.tab-btn {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.95rem;
  color: #666;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

.tab-icon {
  width: 1.1em;
  height: 1.1em;
  flex-shrink: 0;
  vertical-align: middle;
}

.tab-btn:hover {
  color: #007bff;
}

.tab-btn.active {
  color: #007bff;
  border-bottom-color: #007bff;
  font-weight: 600;
}

.tab-content {
  min-height: 200px;
}

.telegram-section {
  text-align: left;
}

.telegram-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-bottom: 1rem;
  transition: background 0.2s;
}

.telegram-btn:hover:not(:disabled) {
  background: #218838;
}

.telegram-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.folders-list {
  margin-top: 1rem;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.folder-item {
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.2s;
  font-weight: 500;
}

.folder-item:hover {
  background: #f8f9fa;
  padding-left: 1.25rem;
  border-left: 3px solid #007bff;
}

.folder-item:last-child {
  border-bottom: none;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.folder-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #333;
}

.back-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
}

.back-btn:hover {
  background: #5a6268;
}

.upload-area {
  margin-bottom: 0;
}

input[type="file"] {
  padding: 1rem;
  border: 2px dashed #007bff;
  border-radius: 8px;
  cursor: pointer;
  width: 100%;
  background: #f8f9ff;
  transition: all 0.3s;
}

input[type="file"]:hover {
  border-color: #0056b3;
  background: #f0f4ff;
}

input[type="file"]:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.file-info {
  margin-top: 1rem;
  color: #666;
  font-size: 0.9rem;
}

.file-count {
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
}

.file-list {
  margin-top: 0.5rem;
  text-align: left;
  max-height: 150px;
  overflow-y: auto;
}

.file-item {
  padding: 0.25rem 0;
  font-size: 0.85rem;
  color: #555;
}

.transcribe-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
  transition: background 0.2s;
}

.transcribe-btn:hover:not(:disabled) {
  background: #0056b3;
}

.transcribe-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.loader {
  margin-top: 2rem;
}

.wave-animation {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 40px;
  margin: 0 auto 1rem;
}

.wave-bar {
  width: 4px;
  height: 30px;
  background: #007bff;
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
}

.wave-bar:nth-child(1) { animation-delay: 0s; }
.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave {
  0%, 40%, 100% {
    transform: scaleY(0.4);
    opacity: 0.5;
  }
  20% {
    transform: scaleY(1);
    opacity: 1;
  }
}

.time-info {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 0.9rem;
}

.time-item {
  display: flex;
  gap: 0.5rem;
}

.time-label {
  color: #666;
  font-weight: 500;
}

.time-value {
  color: #007bff;
  font-weight: 600;
}

.message {
  margin-top: 1.5rem;
  padding: 1rem;
  border-radius: 4px;
}

.message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background: #e9ecef;
  border-radius: 15px;
  margin-top: 1rem;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #007bff;
  transition: width 0.3s ease;
  border-radius: 15px;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.85rem;
  font-weight: 600;
  color: #333;
  z-index: 1;
}

.current-file {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #666;
  font-style: italic;
}

.files-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 0;
}

.summary-item {
  display: flex;
  flex-direction: column;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 3px solid #007bff;
}

.summary-label {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.summary-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
}

.files-list-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  margin-top: 0.5rem;
  background: #ffffff;
}

.file-item-detailed {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #eee;
  transition: background 0.2s;
}

.file-item-detailed:hover {
  background: #f8f9fa;
}

.file-item-detailed:last-child {
  border-bottom: none;
}

.file-name {
  flex: 1;
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
}

.file-meta {
  display: flex;
  gap: 1.5rem;
  font-size: 0.85rem;
}

.file-size {
  color: #666;
  font-weight: 500;
}

.file-duration {
  color: #007bff;
  font-weight: 600;
}

.section-card {
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 1rem 0;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid #f0f0f0;
}

.section-description {
  font-size: 0.85rem;
  color: #666;
  margin: -0.5rem 0 1rem 0;
  font-style: italic;
}

.instruction-steps {
  margin: 0.5rem 0 0 1.2rem;
  padding: 0;
  font-style: normal;
  line-height: 1.8;
}

.instruction-steps li {
  margin-bottom: 0.2rem;
}

.instruction-steps code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  font-size: 0.82rem;
}

@media (prefers-color-scheme: dark) {
  .instruction-steps code {
    background: rgba(255, 255, 255, 0.1);
  }
}

.settings-form {
  margin-top: 1rem;
  margin-bottom: 1rem;
  text-align: left;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}

.setting-item {
  margin-bottom: 1rem;
}

.setting-item.full-width {
  grid-column: 1 / -1;
}

.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item label {
  display: block;
  font-size: 0.9rem;
  color: #555;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.model-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  background: white;
  cursor: pointer;
}

.model-select:focus {
  outline: none;
  border-color: #007bff;
}

.prompt-textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
}

.prompt-textarea:focus {
  outline: none;
  border-color: #007bff;
}

.buttons-group {
  display: flex;
  gap: 0.75rem;
  margin-top: 0;
  flex-wrap: wrap;
}

.actions-card {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border: 2px solid #e0e0e0;
}

.primary-btn {
  background: #007bff;
  flex: 1;
  min-width: 200px;
}

.primary-btn:hover:not(:disabled) {
  background: #0056b3;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,123,255,0.3);
}

.success-btn {
  background: #28a745;
  flex: 1;
  min-width: 200px;
}

.success-btn:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(40,167,69,0.3);
}

.info-btn {
  background: #17a2b8;
  flex: 1;
  min-width: 200px;
}

.info-btn:hover:not(:disabled) {
  background: #138496;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(23,162,184,0.3);
}

.transcribe-btn {
  transition: all 0.2s;
  font-weight: 500;
}

.youtube-url-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.95rem;
  font-family: inherit;
}

.youtube-url-input:focus {
  outline: none;
  border-color: #ff0000;
}

.youtube-btn {
  background: #ff0000;
  flex: 1;
  min-width: 200px;
}

.youtube-btn:hover:not(:disabled) {
  background: #cc0000;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(255,0,0,0.3);
}

.stop-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.stop-btn:hover {
  background: #c82333;
}

.progress-section {
  margin-top: 1rem;
  width: 100%;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.model-download-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 8px;
}

.model-download-bar {
  height: 24px;
  border-radius: 12px;
  margin-top: 0.5rem;
}

.model-download-fill {
  background: #ffc107;
}

.current-file-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.current-file-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: #666;
}

.progress-bar-small {
  width: 100%;
  height: 20px;
  background: #e9ecef;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill-small {
  height: 100%;
  background: #28a745;
  transition: width 0.3s ease;
  border-radius: 10px;
}

.result-block {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.result-text {
  font-weight: 600;
}

.result-file {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.result-label {
  font-size: 0.85rem;
  color: #155724;
  font-weight: 500;
}

.rename-row {
  display: flex;
  gap: 0.5rem;
}

.rename-input {
  flex: 1;
  padding: 0.4rem 0.6rem;
  border: 1px solid #c3e6cb;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
  background: white;
}

.rename-input:focus {
  outline: none;
  border-color: #28a745;
}

.rename-btn {
  padding: 0.4rem 1rem;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background 0.2s;
}

.rename-btn:hover:not(:disabled) {
  background: #218838;
}

.rename-btn:disabled {
  background: #94d3a2;
  cursor: default;
}

.open-folder-btn {
  padding: 0.5rem 1rem;
  background: #17a2b8;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background 0.2s;
  align-self: flex-start;
}

.open-folder-btn:hover {
  background: #138496;
}

.message.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.whisper-logs-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.logs-header {
  font-size: 0.85rem;
  font-weight: 600;
  color: #666;
  margin-bottom: 0.5rem;
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  background: #f8f9fa;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.5rem;
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  text-align: left;
}

.log-line {
  padding: 0.25rem 0;
  color: #333;
  white-space: pre-wrap;
  word-break: break-word;
}

.last-log {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #e7f3ff;
  border-left: 3px solid #007bff;
  border-radius: 4px;
  font-size: 0.85rem;
  color: #004085;
  text-align: left;
}

.about-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: 1px solid #ccc;
  border-radius: 12px;
  padding: 0.2rem 0.7rem;
  font-size: 0.75rem;
  color: #888;
  cursor: pointer;
  transition: all 0.2s;
}

.about-btn:hover {
  border-color: #007bff;
  color: #007bff;
}

.update-banner {
  background: #d4edda;
  color: #155724;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.update-banner--downloading {
  background: #fff3cd;
  color: #856404;
}

.setup-banner {
  background: #e8f0fe;
  color: #1a56db;
  padding: 0.8rem 1rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.setup-banner--error {
  background: #fde8e8;
  color: #c81e1e;
}

.setup-spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid #1a56db;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.update-btn {
  background: #28a745;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.35rem 1rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s;
}

.update-btn:hover {
  background: #218838;
}

.about-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.about-dialog {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  max-width: 360px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.about-logo {
  width: 80px;
  height: 80px;
  margin-bottom: 0.5rem;
}

.about-dialog h2 {
  margin: 0 0 0.3rem;
  font-size: 1.4rem;
}

.about-version {
  color: #888;
  font-size: 0.9rem;
  margin: 0 0 0.8rem;
}

.about-description {
  color: #555;
  font-size: 0.85rem;
  margin: 0 0 1.2rem;
}

.about-update-section {
  margin-bottom: 1.2rem;
  font-size: 0.85rem;
  color: #555;
}

.check-update-btn {
  background: none;
  border: 1px solid #007bff;
  color: #007bff;
  border-radius: 6px;
  padding: 0.4rem 1rem;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.check-update-btn:hover {
  background: #007bff;
  color: white;
}

.about-close-btn {
  background: #f0f0f0;
  border: none;
  border-radius: 6px;
  padding: 0.4rem 1.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  color: #333;
  transition: background 0.2s;
}

.about-close-btn:hover {
  background: #e0e0e0;
}

.record-sources {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.5rem 0 1rem;
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-size: 0.95rem;
}

.checkbox-row input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  cursor: pointer;
}

.record-hint {
  margin: 0.25rem 0 0.75rem;
  font-size: 0.85rem;
  color: #666;
}

.record-hint--error {
  color: #c62828;
}

.record-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 0.5rem;
}

.record-btn {
  min-width: 14rem;
}

.record-output {
  width: 100%;
  min-height: 12rem;
  padding: 0.75rem;
  font-family: inherit;
  font-size: 0.95rem;
  border: 1px solid #ccc;
  border-radius: 6px;
  resize: vertical;
  box-sizing: border-box;
}

.update-check-msg {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
}

.update-check-msg--uptodate {
  color: #2e7d32;
}

.update-check-msg--available {
  color: #1565c0;
}

.update-check-msg--error {
  color: #c62828;
}
</style>
