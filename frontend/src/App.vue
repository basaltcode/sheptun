<template>
  <div class="container">
    <div class="app-header">
      <img src="/logo.png" alt="Sheptun" class="app-logo" />
      <h1>Sheptun</h1>
      <label class="keep-awake-toggle" title="Не давать компьютеру уходить в сон, пока приложение открыто">
        <input type="checkbox" v-model="keepAwake" @change="applyKeepAwake" />
        <span>☕ Не спать</span>
      </label>
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

    <div v-if="!loading" class="tabs">
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
    
    <div v-if="activeTab === 'audio' && !loading" class="tab-content">
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
              <option value="Arabic">Арабский</option>
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
              <option value="transcribe">Транскрибация</option>
              <option value="translate">Перевод на английский</option>
              <option value="translate_other">Перевод на другой язык</option>
            </select>
            <small v-if="whisperSettings.task === 'translate_other'" class="task-hint">При первом использовании потребуется загрузка модели перевода (~100 МБ).</small>
          </div>
          <div class="setting-item" v-if="whisperSettings.task === 'translate_other'">
            <label for="target-lang-select-audio">Целевой язык:</label>
            <select id="target-lang-select-audio" v-model="whisperSettings.targetLanguage" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Spanish">Испанский</option>
              <option value="French">Французский</option>
              <option value="German">Немецкий</option>
              <option value="Arabic">Арабский</option>
              <option value="Chinese">Китайский</option>
              <option value="Japanese">Японский</option>
              <option value="Portuguese">Португальский</option>
              <option value="Italian">Итальянский</option>
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
    
    <div v-if="activeTab === 'video' && !loading" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">🎬 Видео файлы</h3>
        <p class="section-description">Создание субтитров или стенограммы из видео файлов с компьютера. Загрузите файлы в формате MP4, AVI, MOV, MKV или WEBM — результат будет сохранён в папку Downloads.</p>
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
              <option value="Arabic">Арабский</option>
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
              <option value="transcribe">Транскрибация</option>
              <option value="translate">Перевод на английский</option>
              <option value="translate_other">Перевод на другой язык</option>
            </select>
            <small v-if="whisperSettings.task === 'translate_other'" class="task-hint">При первом использовании потребуется загрузка модели перевода (~100 МБ).</small>
          </div>
          <div class="setting-item" v-if="whisperSettings.task === 'translate_other'">
            <label for="target-lang-select-video">Целевой язык:</label>
            <select id="target-lang-select-video" v-model="whisperSettings.targetLanguage" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Spanish">Испанский</option>
              <option value="French">Французский</option>
              <option value="German">Немецкий</option>
              <option value="Arabic">Арабский</option>
              <option value="Chinese">Китайский</option>
              <option value="Japanese">Японский</option>
              <option value="Portuguese">Португальский</option>
              <option value="Italian">Итальянский</option>
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
    
    <div v-if="activeTab === 'youtube' && !loading" class="tab-content">
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
              <option value="Arabic">Арабский</option>
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
              <option value="transcribe">Транскрибация</option>
              <option value="translate">Перевод на английский</option>
              <option value="translate_other">Перевод на другой язык</option>
            </select>
            <small v-if="whisperSettings.task === 'translate_other'" class="task-hint">При первом использовании потребуется загрузка модели перевода (~100 МБ).</small>
          </div>
          <div class="setting-item" v-if="whisperSettings.task === 'translate_other'">
            <label for="target-lang-select-youtube">Целевой язык:</label>
            <select id="target-lang-select-youtube" v-model="whisperSettings.targetLanguage" class="model-select">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Spanish">Испанский</option>
              <option value="French">Французский</option>
              <option value="German">Немецкий</option>
              <option value="Arabic">Арабский</option>
              <option value="Chinese">Китайский</option>
              <option value="Japanese">Японский</option>
              <option value="Portuguese">Португальский</option>
              <option value="Italian">Итальянский</option>
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

    <div v-if="activeTab === 'record' && !loading" class="tab-content">
      <div class="section-card">
        <h3 class="section-title">🎤 Запись</h3>
        <p class="section-description">
          Запишите звук с одного или нескольких устройств ввода. Можно совмещать микрофон с виртуальным устройством для захвата системного звука. По окончании записи файл распознаётся Whisper и сохраняется в Downloads.
        </p>

        <div class="record-sources">
          <div class="record-sources__header">
            <label class="record-sources__label">Устройства ввода:</label>
            <button
              @click="refreshAudioInputDevices"
              class="rename-btn"
              :disabled="recordState !== 'idle' || loading"
              type="button"
            >
              Обновить
            </button>
          </div>

          <div v-if="!devicesPermissionGranted && audioInputDevices.every(d => !d.label)" class="record-hint">
            Чтобы увидеть названия устройств, разрешите доступ к микрофону.
            <button
              @click="requestMicPermission"
              class="rename-btn"
              :disabled="recordState !== 'idle' || loading"
              type="button"
              style="margin-left: 0.5rem;"
            >
              Разрешить доступ
            </button>
          </div>

          <div v-if="audioInputDevices.length === 0 && devicesEnumerated" class="record-hint">
            Устройства ввода не найдены.
          </div>

          <div v-if="audioInputDevices.length > 0" class="record-sources__list">
            <label
              v-for="(device, idx) in audioInputDevices"
              :key="device.deviceId || idx"
              class="checkbox-row"
            >
              <input
                type="checkbox"
                :value="device.deviceId"
                v-model="selectedInputDeviceIds"
                :disabled="recordState !== 'idle' || loading"
              />
              <span>{{ device.label || `Устройство ${idx + 1}` }}</span>
            </label>
          </div>
        </div>

        <p v-if="audioInputDevices.length > 0 && selectedInputDeviceIds.length === 0" class="record-hint">
          Выберите хотя бы одно устройство.
        </p>
        <p class="record-hint">
          Для захвата системного звука (созвоны, YouTube) установите виртуальное аудио-устройство — оно появится в списке выше:
          <a href="https://existential.audio/blackhole/" target="_blank" rel="noopener">BlackHole</a> (macOS),
          <a href="https://vb-audio.com/Cable/" target="_blank" rel="noopener">VB-Cable</a> (Windows).
        </p>

        <div class="record-controls">
          <button
            v-if="recordState === 'idle'"
            @click="startRecording"
            :disabled="selectedInputDeviceIds.length === 0 || loading || !setupReady"
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
              <option value="Arabic">Арабский</option>
              <option value="">Автоопределение</option>
            </select>
          </div>

          <div class="setting-item">
            <label for="task-select-record">Задача:</label>
            <select id="task-select-record" v-model="whisperSettings.task" class="model-select" :disabled="recordState !== 'idle' || loading">
              <option value="transcribe">Транскрибация</option>
              <option value="translate">Перевод на английский</option>
              <option value="translate_other">Перевод на другой язык</option>
            </select>
            <small v-if="whisperSettings.task === 'translate_other'" class="task-hint">При первом использовании потребуется загрузка модели перевода (~100 МБ).</small>
          </div>
          <div class="setting-item" v-if="whisperSettings.task === 'translate_other'">
            <label for="target-lang-select-record">Целевой язык:</label>
            <select id="target-lang-select-record" v-model="whisperSettings.targetLanguage" class="model-select" :disabled="recordState !== 'idle' || loading">
              <option value="Russian">Русский</option>
              <option value="English">Английский</option>
              <option value="Spanish">Испанский</option>
              <option value="French">Французский</option>
              <option value="German">Немецкий</option>
              <option value="Arabic">Арабский</option>
              <option value="Chinese">Китайский</option>
              <option value="Japanese">Японский</option>
              <option value="Portuguese">Португальский</option>
              <option value="Italian">Итальянский</option>
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

    <div v-if="activeTab === 'telegram' && !loading" class="tab-content">
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
                <option value="Arabic">Арабский</option>
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
                <option value="translate">Перевод на английский</option>
                <option value="translate_other">Перевод на другой язык</option>
              </select>
              <small v-if="whisperSettings.task === 'translate_other'" class="task-hint">При первом использовании потребуется загрузка модели перевода (~100 МБ).</small>
            </div>
            <div class="setting-item" v-if="whisperSettings.task === 'translate_other'">
              <label for="target-lang-select-telegram">Целевой язык:</label>
              <select id="target-lang-select-telegram" v-model="whisperSettings.targetLanguage" class="model-select">
                <option value="Russian">Русский</option>
                <option value="English">Английский</option>
                <option value="Spanish">Испанский</option>
                <option value="French">Французский</option>
                <option value="German">Немецкий</option>
                <option value="Arabic">Арабский</option>
                <option value="Chinese">Китайский</option>
                <option value="Japanese">Японский</option>
                <option value="Portuguese">Португальский</option>
                <option value="Italian">Итальянский</option>
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

const keepAwake = ref(false)
try {
  keepAwake.value = localStorage.getItem('sheptun.keepAwake') === '1'
} catch {}

const applyKeepAwake = async () => {
  try {
    localStorage.setItem('sheptun.keepAwake', keepAwake.value ? '1' : '0')
  } catch {}
  if (!isTauri()) return
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('set_keep_awake', { enabled: keepAwake.value })
  } catch (err) {
    console.error('set_keep_awake failed:', err)
  }
}

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
  task: 'transcribe',
  targetLanguage: 'Russian'
})

const audioInputDevices = ref([])
const selectedInputDeviceIds = ref([])
const devicesPermissionGranted = ref(false)
const devicesEnumerated = ref(false)
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
let deviceChangeHandler = null

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
  selectedVideoFiles.value.forEach(file => {
    formData.append('files', file)
  })

  try {
    const isTranslateOther = whisperSettings.value.task === 'translate_other'
    const params = new URLSearchParams({
      model: whisperSettings.value.model === 'small' ? 'medium' : whisperSettings.value.model,
      language: whisperSettings.value.task === 'translate' ? 'English' : (whisperSettings.value.language || ''),
      output_format: whisperSettings.value.outputFormat === 'txt' ? 'srt' : whisperSettings.value.outputFormat,
      task: isTranslateOther ? 'transcribe' : whisperSettings.value.task,
      ...(isTranslateOther ? { target_language: whisperSettings.value.targetLanguage } : {})
    })
    const response = await fetch(`${await apiUrl('/transcribe/video')}?${params.toString()}`, {
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
    console.error('Ошибка при запуске транскрибации видео:', error)
    message.value = error.message || 'Ошибка соединения с сервером'
    messageType.value = 'error'
    loading.value = false
    currentTaskId.value = null
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
    const isTranslateOther = whisperSettings.value.task === 'translate_other'
    const params = new URLSearchParams({
      url: youtubeUrl.value,
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt,
      task: isTranslateOther ? 'transcribe' : whisperSettings.value.task,
      ...(isTranslateOther ? { target_language: whisperSettings.value.targetLanguage } : {})
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
    const isTranslateOther = whisperSettings.value.task === 'translate_other'
    const params = new URLSearchParams({
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt,
      task: isTranslateOther ? 'transcribe' : whisperSettings.value.task,
      ...(isTranslateOther ? { target_language: whisperSettings.value.targetLanguage } : {})
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
    const isTranslateOther = whisperSettings.value.task === 'translate_other'
    const params = new URLSearchParams({
      folder_name: selectedTelegramFolder.value,
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: whisperSettings.value.outputFormat,
      initial_prompt: whisperSettings.value.initialPrompt,
      task: isTranslateOther ? 'transcribe' : whisperSettings.value.task,
      ...(isTranslateOther ? { target_language: whisperSettings.value.targetLanguage } : {})
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

const refreshAudioInputDevices = async () => {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    const inputs = devices.filter(d => d.kind === 'audioinput')
    audioInputDevices.value = inputs
    devicesEnumerated.value = true
    if (inputs.some(d => d.label)) devicesPermissionGranted.value = true

    const availableIds = new Set(inputs.map(d => d.deviceId))
    selectedInputDeviceIds.value = selectedInputDeviceIds.value.filter(id => availableIds.has(id))

    if (selectedInputDeviceIds.value.length === 0 && inputs.length > 0) {
      const def = inputs.find(d => d.deviceId === 'default') || inputs[0]
      selectedInputDeviceIds.value = [def.deviceId]
    }
  } catch (err) {
    console.error('enumerateDevices failed:', err)
  }
}

const requestMicPermission = async () => {
  recordError.value = ''
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    stream.getTracks().forEach(t => t.stop())
    devicesPermissionGranted.value = true
    await refreshAudioInputDevices()
  } catch (err) {
    console.error('requestMicPermission failed:', err)
    recordError.value = err?.name === 'NotAllowedError'
      ? 'Доступ к микрофону отклонён. Проверьте разрешения системы.'
      : (err?.message || 'Не удалось получить доступ к микрофону.')
  }
}

const buildMixedStream = async () => {
  const ids = selectedInputDeviceIds.value
  if (!ids || ids.length === 0) {
    throw new Error('Выберите хотя бы одно устройство ввода.')
  }

  const streams = []
  for (const id of ids) {
    const constraints = id && id !== 'default'
      ? { audio: { deviceId: { exact: id } } }
      : { audio: true }
    const stream = await navigator.mediaDevices.getUserMedia(constraints)
    streams.push(stream)
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
  if (selectedInputDeviceIds.value.length === 0) return

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
    const isTranslateOther = whisperSettings.value.task === 'translate_other'
    const params = new URLSearchParams({
      model: whisperSettings.value.model,
      language: whisperSettings.value.language || '',
      output_format: 'txt',
      initial_prompt: whisperSettings.value.initialPrompt,
      task: isTranslateOther ? 'transcribe' : whisperSettings.value.task,
      ...(isTranslateOther ? { target_language: whisperSettings.value.targetLanguage } : {})
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
    if (keepAwake.value) {
      applyKeepAwake()
    }
  }

  if (navigator.mediaDevices?.enumerateDevices) {
    await refreshAudioInputDevices()
    if (navigator.mediaDevices.addEventListener) {
      deviceChangeHandler = () => { refreshAudioInputDevices() }
      navigator.mediaDevices.addEventListener('devicechange', deviceChangeHandler)
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
  if (deviceChangeHandler && navigator.mediaDevices?.removeEventListener) {
    navigator.mediaDevices.removeEventListener('devicechange', deviceChangeHandler)
    deviceChangeHandler = null
  }
})

const sendCompletionNotification = async () => {
  try {
    const { isPermissionGranted, requestPermission, sendNotification } =
      await import('@tauri-apps/plugin-notification')
    let granted = await isPermissionGranted()
    if (!granted) {
      const permission = await requestPermission()
      granted = permission === 'granted'
    }
    if (granted) {
      sendNotification({ title: 'Sheptun', body: 'Транскрипция завершена' })
    }
  } catch (e) {
    console.warn('Notification failed:', e)
  }
}

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

  sendCompletionNotification()
}
</script>

<style>
:root {
  --bg-grad: radial-gradient(120% 100% at 0% 0%, #1a1d3a 0%, #0d1020 45%, #160c28 100%);
  --surface: #1a1f2e;
  --surface-2: #232838;
  --surface-3: #2a2f42;
  --input-bg: #161a26;
  --input-bg-2: #1d2230;
  --border: rgba(255, 255, 255, 0.07);
  --border-strong: rgba(255, 255, 255, 0.12);
  --text: #e7eaf2;
  --text-2: #9aa1b3;
  --text-3: #6b7186;
  --accent: #4f7cff;
  --accent-2: #3b6ef0;
  --accent-soft: rgba(79, 124, 255, 0.18);
  --danger: #ef4444;
  --danger-2: #dc2626;
  --success: #10b981;
  --success-2: #059669;
  --warn: #f59e0b;
  --info: #38bdf8;
  --radius: 16px;
  --radius-sm: 10px;
  --radius-pill: 999px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body {
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #0a0b14;
  background-image: var(--bg-grad);
  background-attachment: fixed;
  color: var(--text);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100vh;
  padding: 1.5rem;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.container {
  background: linear-gradient(180deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.005) 100%), var(--surface);
  border: 1px solid var(--border);
  padding: 1.5rem 1.75rem 2rem;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.02) inset;
  max-width: 920px;
  width: 100%;
  text-align: left;
  color: var(--text);
}

/* Header */
.app-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  position: relative;
}

.app-logo {
  width: 32px;
  height: 32px;
  filter: drop-shadow(0 4px 10px rgba(79, 124, 255, 0.35));
}

h1 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: var(--text);
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1.25rem;
  padding: 0.4rem;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.tab-btn {
  flex: 1;
  padding: 0.55rem 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.78rem;
  color: var(--text-2);
  border-radius: 8px;
  transition: all 0.18s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  font-weight: 500;
  white-space: nowrap;
}

.tab-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.tab-btn:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.04);
}

.tab-btn.active {
  background: var(--accent-soft);
  color: #b9c8ff;
  font-weight: 600;
  box-shadow: 0 0 0 1px rgba(79, 124, 255, 0.25) inset;
}

.tab-content {
  min-height: 200px;
}

/* Cards */
.section-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0) 100%), var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem 1.25rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin: 0 0 0.85rem 0;
  padding-bottom: 0.6rem;
  border-bottom: 1px solid var(--border);
  letter-spacing: -0.01em;
}

.section-description {
  font-size: 0.85rem;
  color: var(--text-2);
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.instruction-steps {
  margin: 0.5rem 0 0 1.2rem;
  padding: 0;
  line-height: 1.8;
  color: var(--text-2);
}
.instruction-steps li { margin-bottom: 0.2rem; }
.instruction-steps code {
  background: rgba(255, 255, 255, 0.08);
  color: #c8d1e0;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  font-size: 0.82rem;
  font-family: ui-monospace, SF Mono, Menlo, monospace;
}

/* File drop zone */
.upload-area { margin-bottom: 0; }

input[type="file"] {
  padding: 1.75rem 1rem;
  border: 1.5px dashed rgba(79, 124, 255, 0.4);
  border-radius: var(--radius-sm);
  cursor: pointer;
  width: 100%;
  background: rgba(79, 124, 255, 0.04);
  color: var(--text-2);
  transition: all 0.2s;
  font-size: 0.9rem;
  text-align: center;
}
input[type="file"]:hover {
  border-color: var(--accent);
  background: rgba(79, 124, 255, 0.08);
  color: var(--text);
}
input[type="file"]:disabled { cursor: not-allowed; opacity: 0.5; }
input[type="file"]::file-selector-button {
  background: var(--accent-soft);
  color: #c8d4ff;
  border: 1px solid rgba(79, 124, 255, 0.3);
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  margin-right: 0.75rem;
  font-size: 0.85rem;
}

.file-info { margin-top: 0.85rem; color: var(--text-2); font-size: 0.88rem; }
.file-count { font-weight: 600; color: var(--text); margin-bottom: 0.4rem; }
.file-list { margin-top: 0.4rem; max-height: 150px; overflow-y: auto; }
.file-item {
  padding: 0.3rem 0.5rem;
  font-size: 0.85rem;
  color: var(--text-2);
  background: rgba(255,255,255,0.02);
  border-radius: 4px;
  margin-bottom: 0.2rem;
}

/* Settings */
.settings-form { margin-top: 1rem; margin-bottom: 1rem; }
.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.85rem 1rem;
  margin-bottom: 1rem;
}
@media (max-width: 720px) { .settings-grid { grid-template-columns: 1fr; } }

.setting-item { margin-bottom: 0.65rem; }
.setting-item.full-width { grid-column: 1 / -1; }
.setting-item:last-child { margin-bottom: 0; }
.setting-item label {
  display: block;
  font-size: 0.82rem;
  color: var(--text-2);
  font-weight: 500;
  margin-bottom: 0.4rem;
}

.model-select,
.youtube-url-input,
.prompt-textarea,
.rename-input,
.record-output {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
  background: var(--input-bg);
  color: var(--text);
  transition: border-color 0.15s, background 0.15s;
}
.model-select {
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'><path fill='none' stroke='%239aa1b3' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round' d='M1 1.5l5 5 5-5'/></svg>");
  background-repeat: no-repeat;
  background-position: right 0.85rem center;
  padding-right: 2.2rem;
  cursor: pointer;
}
.model-select option { background: var(--surface-2); color: var(--text); }

.model-select:focus,
.youtube-url-input:focus,
.prompt-textarea:focus,
.rename-input:focus,
.record-output:focus {
  outline: none;
  border-color: var(--accent);
  background: var(--input-bg-2);
  box-shadow: 0 0 0 3px rgba(79, 124, 255, 0.18);
}

.prompt-textarea { resize: vertical; min-height: 84px; line-height: 1.5; }
.record-output { min-height: 12rem; resize: vertical; }

/* Buttons */
.transcribe-btn {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  color: white;
  border: none;
  padding: 0.85rem 1.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s ease;
  box-shadow: 0 8px 20px rgba(79, 124, 255, 0.32);
  letter-spacing: 0.01em;
}
.transcribe-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(79, 124, 255, 0.45);
  filter: brightness(1.08);
}
.transcribe-btn:active:not(:disabled) { transform: translateY(0); }
.transcribe-btn:disabled {
  background: #2a2f42;
  color: var(--text-3);
  cursor: not-allowed;
  box-shadow: none;
}

.buttons-group { display: flex; gap: 0.6rem; margin-top: 0; flex-wrap: wrap; }

.actions-card {
  background: linear-gradient(180deg, rgba(79,124,255,0.06) 0%, rgba(79,124,255,0.01) 100%), var(--surface-2);
  border: 1px solid rgba(79, 124, 255, 0.18);
}

.primary-btn { flex: 1; min-width: 200px; }
.success-btn {
  background: linear-gradient(135deg, var(--success) 0%, var(--success-2) 100%);
  flex: 1; min-width: 200px;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
}
.success-btn:hover:not(:disabled) { box-shadow: 0 10px 26px rgba(16, 185, 129, 0.42); }

.info-btn {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  flex: 1; min-width: 200px;
  box-shadow: 0 8px 20px rgba(6, 182, 212, 0.28);
}
.info-btn:hover:not(:disabled) { box-shadow: 0 10px 26px rgba(6, 182, 212, 0.4); }

.youtube-btn {
  background: linear-gradient(135deg, #ff3b3b 0%, #d32626 100%);
  flex: 1; min-width: 200px;
  box-shadow: 0 8px 20px rgba(255, 59, 59, 0.3);
}
.youtube-btn:hover:not(:disabled) { box-shadow: 0 10px 26px rgba(255, 59, 59, 0.42); }

.telegram-btn {
  background: linear-gradient(135deg, #229ED9 0%, #1a7ea8 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 1rem;
  transition: all 0.18s;
  box-shadow: 0 8px 20px rgba(34, 158, 217, 0.3);
}
.telegram-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(34, 158, 217, 0.42); }
.telegram-btn:disabled { background: #2a2f42; color: var(--text-3); cursor: not-allowed; box-shadow: none; }

.stop-btn {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  padding: 0.75rem 1.75rem;
  border-radius: var(--radius-pill);
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
  box-shadow: 0 8px 20px rgba(239, 68, 68, 0.3);
}
.stop-btn:hover { filter: brightness(1.1); transform: translateY(-1px); }

/* Loader / Processing */
.loader {
  margin-top: 1rem;
  background: linear-gradient(180deg, rgba(255,255,255,0.025) 0%, rgba(255,255,255,0) 100%), var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  text-align: center;
  color: var(--text);
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
  width: 4px; height: 30px;
  background: var(--accent);
  border-radius: 2px;
  animation: wave 1.2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(79, 124, 255, 0.6);
}
.wave-bar:nth-child(1) { animation-delay: 0s; }
.wave-bar:nth-child(2) { animation-delay: 0.1s; }
.wave-bar:nth-child(3) { animation-delay: 0.2s; }
.wave-bar:nth-child(4) { animation-delay: 0.3s; }
.wave-bar:nth-child(5) { animation-delay: 0.4s; }

@keyframes wave {
  0%, 40%, 100% { transform: scaleY(0.4); opacity: 0.5; }
  20% { transform: scaleY(1); opacity: 1; }
}

.progress-section { margin-top: 1rem; width: 100%; }
.progress-info {
  display: flex; justify-content: space-between;
  margin-bottom: 0.5rem; font-size: 0.88rem;
  color: var(--text-2);
}
.time-info {
  display: flex; gap: 1.5rem; flex-wrap: wrap;
  margin-top: 0.5rem; padding: 0.6rem 0.85rem;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 0.85rem;
}
.time-item { display: flex; gap: 0.5rem; }
.time-label { color: var(--text-2); font-weight: 500; }
.time-value { color: #b9c8ff; font-weight: 600; }

.progress-bar {
  width: 100%; height: 24px;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border);
  border-radius: var(--radius-pill);
  margin-top: 1rem;
  position: relative;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-2) 0%, #6b96ff 100%);
  transition: width 0.3s ease;
  border-radius: var(--radius-pill);
  box-shadow: 0 0 18px rgba(79, 124, 255, 0.5);
}
.progress-text {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.82rem; font-weight: 600;
  color: var(--text);
  z-index: 1;
}

.model-download-section {
  margin-bottom: 1.25rem;
  padding: 0.85rem 1rem;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.25);
  border-radius: var(--radius-sm);
}
.model-download-bar { height: 18px; border-radius: var(--radius-pill); margin-top: 0.5rem; }
.model-download-fill {
  background: linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%);
  box-shadow: 0 0 14px rgba(245, 158, 11, 0.5);
}

.current-file-section {
  margin-top: 0.85rem;
  padding-top: 0.85rem;
  border-top: 1px solid var(--border);
}
.current-file-info {
  display: flex; justify-content: space-between;
  margin-bottom: 0.4rem; font-size: 0.82rem;
  color: var(--text-2);
}
.progress-bar-small {
  width: 100%; height: 14px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.progress-fill-small {
  height: 100%;
  background: linear-gradient(90deg, var(--success) 0%, #34d399 100%);
  transition: width 0.3s ease;
  border-radius: var(--radius-pill);
}

.current-file {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-2);
  font-style: italic;
}

/* Logs */
.whisper-logs-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}
.logs-header {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--text-2);
  margin-bottom: 0.5rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.logs-container {
  max-height: 220px;
  overflow-y: auto;
  background: #0b0d16;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.65rem 0.8rem;
  font-family: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  font-size: 0.75rem;
  text-align: left;
  line-height: 1.55;
}
.log-line {
  padding: 0.1rem 0;
  color: #b8c0d4;
  white-space: pre-wrap;
  word-break: break-word;
}
.last-log {
  margin-top: 0.5rem;
  padding: 0.55rem 0.75rem;
  background: rgba(79, 124, 255, 0.1);
  border-left: 3px solid var(--accent);
  border-radius: 6px;
  font-size: 0.82rem;
  color: #c8d4ff;
  text-align: left;
}

/* Messages / Result */
.message {
  margin-top: 1.25rem;
  padding: 0.9rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
}
.message.success {
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
  border: 1px solid rgba(16, 185, 129, 0.25);
}
.message.error {
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
  border: 1px solid rgba(239, 68, 68, 0.3);
}
.message.warning {
  background: rgba(245, 158, 11, 0.1);
  color: #fcd34d;
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.result-block { display: flex; flex-direction: column; gap: 0.75rem; }
.result-text { font-weight: 600; color: var(--text); }
.result-file { display: flex; flex-direction: column; gap: 0.4rem; }
.result-label { font-size: 0.82rem; color: var(--text-2); font-weight: 500; }
.rename-row { display: flex; gap: 0.5rem; }
.rename-input { flex: 1; padding: 0.5rem 0.75rem; }

.rename-btn {
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text);
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.15s;
}
.rename-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--accent);
  color: #b9c8ff;
}
.rename-btn:disabled { opacity: 0.5; cursor: default; }

.open-folder-btn {
  padding: 0.55rem 1rem;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  color: white;
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 600;
  transition: all 0.18s;
  align-self: flex-start;
  box-shadow: 0 6px 14px rgba(6, 182, 212, 0.28);
}
.open-folder-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(6, 182, 212, 0.4); }

/* Telegram folders */
.folders-list {
  margin-top: 1rem;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--input-bg);
  overflow: hidden;
}
.folder-item {
  padding: 0.85rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: all 0.18s;
  font-weight: 500;
  color: var(--text);
}
.folder-item:hover {
  background: rgba(79, 124, 255, 0.08);
  padding-left: 1.25rem;
  border-left: 3px solid var(--accent);
}
.folder-item:last-child { border-bottom: none; }
.folder-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.5rem; }
.folder-header h3 { margin: 0; font-size: 1rem; color: var(--text); }

.back-btn {
  background: rgba(255,255,255,0.06);
  color: var(--text);
  border: 1px solid var(--border-strong);
  padding: 0.45rem 0.9rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.15s;
}
.back-btn:hover { background: rgba(255,255,255,0.1); border-color: var(--accent); color: #b9c8ff; }

/* Files summary */
.files-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}
.summary-item {
  display: flex;
  flex-direction: column;
  padding: 0.75rem 0.9rem;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--accent);
}
.summary-label { font-size: 0.78rem; color: var(--text-2); margin-bottom: 0.2rem; }
.summary-value { font-size: 1.05rem; font-weight: 600; color: var(--text); }

.files-list-container {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--input-bg);
  overflow: hidden;
}
.file-item-detailed {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.7rem 0.9rem;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.file-item-detailed:hover { background: rgba(255,255,255,0.03); }
.file-item-detailed:last-child { border-bottom: none; }
.file-name { flex: 1; font-size: 0.88rem; color: var(--text); font-weight: 500; }
.file-meta { display: flex; gap: 1.25rem; font-size: 0.82rem; }
.file-size { color: var(--text-2); font-weight: 500; }
.file-duration { color: #b9c8ff; font-weight: 600; }

/* Header buttons */
.about-btn {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-pill);
  padding: 0.25rem 0.7rem;
  font-size: 0.72rem;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.18s;
  font-weight: 500;
}
.about-btn:hover { border-color: var(--accent); color: #b9c8ff; background: rgba(79,124,255,0.08); }

.keep-awake-toggle {
  position: absolute;
  right: 5rem;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  color: var(--text-2);
  cursor: pointer;
  user-select: none;
  padding: 0.25rem 0.7rem;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-pill);
  background: rgba(255,255,255,0.04);
  transition: all 0.18s;
}
.keep-awake-toggle:hover { border-color: var(--accent); color: #b9c8ff; background: rgba(79,124,255,0.08); }
.keep-awake-toggle input { margin: 0; cursor: pointer; accent-color: var(--accent); }

/* Banners */
.update-banner {
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 0.6rem 1rem;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  font-size: 0.88rem;
  margin-bottom: 1rem;
}
.update-banner--downloading {
  background: rgba(245, 158, 11, 0.1);
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.25);
}

.setup-banner {
  background: rgba(79, 124, 255, 0.1);
  color: #b9c8ff;
  border: 1px solid rgba(79, 124, 255, 0.25);
  padding: 0.7rem 1rem;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  font-size: 0.88rem;
  margin-bottom: 1rem;
}
.setup-banner--error {
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.3);
}
.setup-spinner {
  width: 16px; height: 16px;
  border: 2.5px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.update-btn {
  background: linear-gradient(135deg, var(--success) 0%, var(--success-2) 100%);
  color: white;
  border: none;
  border-radius: var(--radius-pill);
  padding: 0.4rem 1rem;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 4px 10px rgba(16, 185, 129, 0.28);
}
.update-btn:hover { transform: translateY(-1px); }

/* About dialog */
.about-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.about-dialog {
  background: linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0) 100%), var(--surface-2);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius);
  padding: 2rem;
  text-align: center;
  max-width: 380px;
  width: 90%;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.6);
  color: var(--text);
}
.about-logo { width: 72px; height: 72px; margin-bottom: 0.5rem; filter: drop-shadow(0 4px 14px rgba(79,124,255,0.4)); }
.about-dialog h2 { margin: 0 0 0.25rem; font-size: 1.4rem; color: var(--text); }
.about-version { color: var(--text-2); font-size: 0.9rem; margin: 0 0 0.85rem; }
.about-description { color: var(--text-2); font-size: 0.88rem; margin: 0 0 1.25rem; line-height: 1.5; }
.about-update-section { margin-bottom: 1.25rem; font-size: 0.88rem; color: var(--text-2); }

.check-update-btn {
  background: transparent;
  border: 1px solid var(--accent);
  color: #b9c8ff;
  border-radius: var(--radius-pill);
  padding: 0.45rem 1.1rem;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.check-update-btn:hover:not(:disabled) { background: var(--accent-soft); }
.check-update-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.about-close-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-pill);
  padding: 0.45rem 1.5rem;
  font-size: 0.88rem;
  cursor: pointer;
  color: var(--text);
  font-weight: 500;
  transition: all 0.15s;
}
.about-close-btn:hover { background: rgba(255,255,255,0.1); border-color: var(--accent); }

.update-check-msg { margin: 0.5rem 0 0; font-size: 0.85rem; }
.update-check-msg--uptodate { color: #6ee7b7; }
.update-check-msg--available { color: #b9c8ff; }
.update-check-msg--error { color: #fca5a5; }

/* Recording */
.record-sources {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.5rem 0 1rem;
}
.record-sources__header {
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.75rem;
}
.record-sources__label { font-size: 0.88rem; font-weight: 600; color: var(--text); }

.record-sources__list {
  display: flex; flex-direction: column;
  gap: 0.1rem;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: rgba(0,0,0,0.25);
}

/* iOS-style toggle for record source checkboxes */
.checkbox-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  font-size: 0.92rem;
  color: var(--text);
  padding: 0.5rem 0.25rem;
  border-radius: 6px;
  transition: background 0.15s;
}
.checkbox-row:hover { background: rgba(255,255,255,0.03); }
.checkbox-row span { flex: 1; order: 1; }
.checkbox-row input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  width: 38px;
  height: 22px;
  border-radius: var(--radius-pill);
  background: #2a2f42;
  border: 1px solid var(--border-strong);
  position: relative;
  cursor: pointer;
  flex-shrink: 0;
  order: 2;
  transition: background 0.18s;
  margin: 0;
}
.checkbox-row input[type="checkbox"]::before {
  content: '';
  position: absolute;
  top: 2px; left: 2px;
  width: 16px; height: 16px;
  border-radius: 50%;
  background: #d4d8e3;
  transition: transform 0.18s, background 0.18s;
  box-shadow: 0 1px 3px rgba(0,0,0,0.4);
}
.checkbox-row input[type="checkbox"]:checked {
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
  border-color: transparent;
}
.checkbox-row input[type="checkbox"]:checked::before {
  transform: translateX(16px);
  background: white;
}
.checkbox-row input[type="checkbox"]:disabled { opacity: 0.5; cursor: not-allowed; }

.record-hint {
  margin: 0.25rem 0 0.75rem;
  font-size: 0.85rem;
  color: var(--text-2);
  line-height: 1.5;
}
.record-hint a { color: #b9c8ff; text-decoration: none; }
.record-hint a:hover { text-decoration: underline; }
.record-hint--error { color: #fca5a5; }

.task-hint {
  display: block;
  margin-top: 0.4rem;
  color: var(--text-3);
  font-size: 0.78rem;
  font-style: italic;
}

.record-controls {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: center;
  margin-top: 1rem;
}
.record-btn {
  min-width: 14rem;
  padding: 1.1rem 2rem;
  font-size: 1rem;
  border-radius: var(--radius-pill);
}

/* Scrollbars */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.08);
  border-radius: var(--radius-pill);
  border: 2px solid transparent;
  background-clip: padding-box;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.16); background-clip: padding-box; border: 2px solid transparent; }

/* Selection */
::selection { background: rgba(79, 124, 255, 0.35); color: white; }

@media (max-width: 720px) {
  body { padding: 0.5rem; }
  .container { padding: 1rem 1rem 1.5rem; border-radius: 14px; }
  .tab-btn { font-size: 0.7rem; padding: 0.5rem 0.3rem; }
  .keep-awake-toggle { right: 4.2rem; font-size: 0.7rem; padding: 0.2rem 0.5rem; }
}
</style>

