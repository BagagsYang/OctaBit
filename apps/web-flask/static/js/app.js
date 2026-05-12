    const appConfigElement = document.getElementById('octabit-config');
    const appConfig = JSON.parse(appConfigElement.textContent);
    const TRANSLATIONS = appConfig.translations;
    const CURRENT_LOCALE = appConfig.currentLocale;
    const DEFAULT_LOCALE = appConfig.defaultLocale;
    const SUPPORTED_LOCALES = appConfig.supportedLocales;
    const LOCALE_COOKIE_NAME = appConfig.localeCookieName;
    const ICONS = window.octabitLucideIcons || { svg: () => '' };
    const LOCALE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;
    const themeController = window.octabitTheme || {};
    const THEME_STORAGE_KEY = themeController.storageKey || 'octabitTheme';
    const THEME_VALUES = ['light', 'dark'];
    const LANGUAGE_SWITCH_STATE_KEY = 'pendingLanguageSwitchState';
    const LANGUAGE_SWITCH_STATE_DB_NAME = 'octabitWebState';
    const LANGUAGE_SWITCH_STATE_STORE_NAME = 'pageState';
    const LANGUAGE_SWITCH_STATE_RECORD_KEY = 'pending-language-switch';
    const CONTROL_SWITCH_TRANSITION_MS = 200;
    const PREVIEW_VOLUME = 0.5;
    const MIN_CURVE_FREQUENCY_HZ = 8.175798915643707;
    const MAX_CURVE_FREQUENCY_HZ = 12543.853951415975;
    const MIN_CURVE_GAIN_DB = -36.0;
    const MAX_CURVE_GAIN_DB = 12.0;
    const MAX_CURVE_POINTS = 8;
    const CURVE_WIDTH = 320;
    const CURVE_HEIGHT = 150;
    const CURVE_MARGIN = { top: 14, right: 14, bottom: 24, left: 38 };
    const curveLogSpan = Math.log(MAX_CURVE_FREQUENCY_HZ) - Math.log(MIN_CURVE_FREQUENCY_HZ);
    const layerPresets = [
        { type: 'pulse', duty: 0.5, volume: 1.0 },
        { type: 'sine', duty: 0.5, volume: 1.0 },
        { type: 'triangle', duty: 0.5, volume: 1.0 },
        { type: 'sawtooth', duty: 0.5, volume: 1.0 },
    ];
    const maxLayers = layerPresets.length;

    function t(key, params = {}) {
        const template = Object.prototype.hasOwnProperty.call(TRANSLATIONS, key)
            ? TRANSLATIONS[key]
            : key;

        return template.replace(/\{(\w+)\}/g, (match, token) => {
            return Object.prototype.hasOwnProperty.call(params, token) ? params[token] : match;
        });
    }

    function createDefaultCurve() {
        return [
            { frequency_hz: MIN_CURVE_FREQUENCY_HZ, gain_db: 0.0 },
            { frequency_hz: MAX_CURVE_FREQUENCY_HZ, gain_db: 0.0 },
        ];
    }

    function createDefaultLayer(index) {
        const preset = layerPresets[index] || layerPresets[0];
        return {
            active: index === 0,
            type: preset.type,
            duty: preset.duty,
            volume: preset.volume,
            curveEnabled: false,
            frequencyCurve: createDefaultCurve(),
            selectedPointIndex: 0,
        };
    }

    let fileQueue = [];
    let layerCount = 1;
    let dragStartIndex;
    let previewAudio = new Audio();
    previewAudio.volume = PREVIEW_VOLUME;
    let dragState = null;
    let layerRenderTimer = null;
    let convertedFiles = [];
    const layers = Array.from({ length: maxLayers }, (_, index) => createDefaultLayer(index));

    const synthForm = document.getElementById('synthForm');
    const loading = document.querySelector('.loading');
    const submitBtn = document.getElementById('submitBtn');
    const htmlElement = document.documentElement;
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('midi_file');
    const queueList = document.getElementById('queueList');
    const clearQueueBtn = document.getElementById('clearQueueBtn');
    const keepQueueToggle = document.getElementById('keepQueueToggle');
    const queueCountSpan = document.getElementById('queueCount');
    const queueCountAction = document.getElementById('queueCountAction');
    const queueEmpty = document.getElementById('queueEmpty');
    const processingStatus = document.getElementById('processingStatus');
    const themeSelect = document.getElementById('themeSelect');
    const languageSelect = document.getElementById('languageSelect');
    const layersContainer = document.getElementById('layersContainer');
    const addLayerBtn = document.getElementById('addLayerBtn');
    const removeLayerBtn = document.getElementById('removeLayerBtn');
    const rateSelect = document.getElementById('rate');
    const convertedList = document.getElementById('convertedList');
    const convertedEmpty = document.getElementById('convertedEmpty');
    const convertedCount = document.getElementById('convertedCount');
    const clearConvertedBtn = document.getElementById('clearConvertedBtn');
    const savedKeepQueuePreference = localStorage.getItem('keepQueueAfterSynth');

    document.title = t('meta.site_title');
    htmlElement.setAttribute('lang', CURRENT_LOCALE);
    languageSelect.value = CURRENT_LOCALE;

    function isThemeValue(value) {
        return THEME_VALUES.includes(value);
    }

    function storedTheme() {
        if (typeof themeController.storedTheme === 'function') {
            return themeController.storedTheme();
        }

        try {
            const value = localStorage.getItem(THEME_STORAGE_KEY);
            return isThemeValue(value) ? value : null;
        } catch (error) {
            return null;
        }
    }

    function clearStoredTheme() {
        try {
            localStorage.removeItem(THEME_STORAGE_KEY);
        } catch (error) {
            console.warn('Failed to clear theme preference.', error);
        }
    }

    function systemTheme() {
        if (typeof themeController.systemTheme === 'function') {
            return themeController.systemTheme();
        }

        if (!window.matchMedia) {
            return 'dark';
        }

        if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }

        if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }

        return 'dark';
    }

    function resolvedTheme() {
        return storedTheme() || systemTheme();
    }

    function isFollowingSystemTheme() {
        return !storedTheme();
    }

    function selectedThemeValue() {
        return storedTheme() || 'system';
    }

    function applyTheme(theme) {
        if (typeof themeController.applyTheme === 'function') {
            return themeController.applyTheme(theme);
        }

        const nextTheme = isThemeValue(theme) ? theme : systemTheme();
        htmlElement.classList.add('theme-change-instant');
        htmlElement.setAttribute('data-bs-theme', nextTheme);
        void htmlElement.offsetHeight;
        htmlElement.classList.remove('theme-change-instant');
        return nextTheme;
    }

    function syncThemeSelect() {
        themeSelect.value = selectedThemeValue();
    }

    function saveTheme(theme) {
        if (!isThemeValue(theme)) {
            return;
        }

        try {
            localStorage.setItem(THEME_STORAGE_KEY, theme);
        } catch (error) {
            console.warn('Failed to save theme preference.', error);
        }

        applyTheme(theme);
        syncThemeSelect();
    }

    function followSystemTheme() {
        clearStoredTheme();
        applyTheme();
        syncThemeSelect();
    }

    applyTheme(resolvedTheme());
    syncThemeSelect();
    keepQueueToggle.checked = savedKeepQueuePreference === 'true';

    themeSelect.addEventListener('change', () => {
        if (themeSelect.value === 'system') {
            followSystemTheme();
        } else {
            saveTheme(themeSelect.value);
        }
    });

    if (window.matchMedia) {
        const systemThemeQueries = [
            window.matchMedia('(prefers-color-scheme: dark)'),
            window.matchMedia('(prefers-color-scheme: light)'),
        ];
        const syncSystemTheme = () => {
            if (isFollowingSystemTheme()) {
                applyTheme();
                syncThemeSelect();
            }
        };

        systemThemeQueries.forEach((systemThemeQuery) => {
            if (typeof systemThemeQuery.addEventListener === 'function') {
                systemThemeQuery.addEventListener('change', syncSystemTheme);
            } else if (typeof systemThemeQuery.addListener === 'function') {
                systemThemeQuery.addListener(syncSystemTheme);
            }
        });
    }

    languageSelect.addEventListener('change', async () => {
        const selectedLocale = languageSelect.value;
        const nextLocale = SUPPORTED_LOCALES.includes(selectedLocale) ? selectedLocale : DEFAULT_LOCALE;
        if (nextLocale === CURRENT_LOCALE) {
            return;
        }

        languageSelect.disabled = true;
        try {
            await persistLanguageSwitchState();
        } catch (error) {
            console.warn('Failed to preserve page state during language change.', error);
        }

        document.cookie = `${LOCALE_COOKIE_NAME}=${encodeURIComponent(nextLocale)}; path=/; max-age=${LOCALE_COOKIE_MAX_AGE_SECONDS}; SameSite=Lax`;

        const url = new URL(window.location.href);
        if (nextLocale === DEFAULT_LOCALE) {
            url.searchParams.delete('lang');
        } else {
            url.searchParams.set('lang', nextLocale);
        }
        window.location.href = url.toString();
    });

    keepQueueToggle.addEventListener('change', () => {
        localStorage.setItem('keepQueueAfterSynth', keepQueueToggle.checked);
    });

    function supportsIndexedDb() {
        return typeof window.indexedDB !== 'undefined';
    }

    function openLanguageSwitchDb() {
        return new Promise((resolve, reject) => {
            const request = window.indexedDB.open(LANGUAGE_SWITCH_STATE_DB_NAME, 1);

            request.onupgradeneeded = () => {
                const database = request.result;
                if (!database.objectStoreNames.contains(LANGUAGE_SWITCH_STATE_STORE_NAME)) {
                    database.createObjectStore(LANGUAGE_SWITCH_STATE_STORE_NAME);
                }
            };

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function requestToPromise(request) {
        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    function transactionDone(transaction) {
        return new Promise((resolve, reject) => {
            transaction.oncomplete = () => resolve();
            transaction.onabort = () => reject(transaction.error);
            transaction.onerror = () => reject(transaction.error);
        });
    }

    async function writeLanguageSwitchState(state) {
        const database = await openLanguageSwitchDb();
        try {
            const transaction = database.transaction(LANGUAGE_SWITCH_STATE_STORE_NAME, 'readwrite');
            transaction.objectStore(LANGUAGE_SWITCH_STATE_STORE_NAME).put(state, LANGUAGE_SWITCH_STATE_RECORD_KEY);
            await transactionDone(transaction);
        } finally {
            database.close();
        }
    }

    async function readLanguageSwitchState() {
        const database = await openLanguageSwitchDb();
        try {
            const transaction = database.transaction(LANGUAGE_SWITCH_STATE_STORE_NAME, 'readonly');
            const request = transaction.objectStore(LANGUAGE_SWITCH_STATE_STORE_NAME).get(LANGUAGE_SWITCH_STATE_RECORD_KEY);
            const state = await requestToPromise(request);
            await transactionDone(transaction);
            return state;
        } finally {
            database.close();
        }
    }

    async function clearLanguageSwitchState() {
        if (!supportsIndexedDb()) {
            return;
        }

        const database = await openLanguageSwitchDb();
        try {
            const transaction = database.transaction(LANGUAGE_SWITCH_STATE_STORE_NAME, 'readwrite');
            transaction.objectStore(LANGUAGE_SWITCH_STATE_STORE_NAME).delete(LANGUAGE_SWITCH_STATE_RECORD_KEY);
            await transactionDone(transaction);
        } finally {
            database.close();
        }
    }

    function cloneCurve(points) {
        return points.map((point) => ({
            frequency_hz: point.frequency_hz,
            gain_db: point.gain_db,
        }));
    }

    function cloneLayerState(layer) {
        return {
            active: layer.active,
            type: layer.type,
            duty: layer.duty,
            volume: layer.volume,
            curveEnabled: layer.curveEnabled,
            frequencyCurve: cloneCurve(layer.frequencyCurve),
            selectedPointIndex: layer.selectedPointIndex,
        };
    }

    function sanitiseLayerState(rawLayer, index) {
        const fallbackLayer = createDefaultLayer(index);
        const allowedTypes = new Set(layerPresets.map((preset) => preset.type));
        const dutyValue = Number(rawLayer?.duty);
        const volumeValue = Number(rawLayer?.volume);
        const frequencyCurve = Array.isArray(rawLayer?.frequencyCurve) && rawLayer.frequencyCurve.length >= 2
            ? rawLayer.frequencyCurve
                .map((point) => ({
                    frequency_hz: clamp(
                        Number(point.frequency_hz) || MIN_CURVE_FREQUENCY_HZ,
                        MIN_CURVE_FREQUENCY_HZ,
                        MAX_CURVE_FREQUENCY_HZ,
                    ),
                    gain_db: clamp(
                        Number(point.gain_db) || 0.0,
                        MIN_CURVE_GAIN_DB,
                        MAX_CURVE_GAIN_DB,
                    ),
                }))
                .sort((leftPoint, rightPoint) => leftPoint.frequency_hz - rightPoint.frequency_hz)
            : fallbackLayer.frequencyCurve;

        const selectedPointIndex = clamp(
            Math.trunc(Number(rawLayer?.selectedPointIndex) || 0),
            0,
            frequencyCurve.length - 1,
        );

        return {
            active: Boolean(rawLayer?.active),
            type: allowedTypes.has(rawLayer?.type) ? rawLayer.type : fallbackLayer.type,
            duty: clamp(Number.isFinite(dutyValue) ? dutyValue : fallbackLayer.duty, 0.01, 0.99),
            volume: clamp(Number.isFinite(volumeValue) ? volumeValue : fallbackLayer.volume, 0.0, 2.0),
            curveEnabled: Boolean(rawLayer?.curveEnabled),
            frequencyCurve,
            selectedPointIndex,
        };
    }

    async function persistLanguageSwitchState() {
        if (!supportsIndexedDb()) {
            return;
        }

        const state = {
            fileQueue: [...fileQueue],
            layerCount,
            layers: layers.map((layer) => cloneLayerState(layer)),
            rate: rateSelect.value,
            keepQueue: keepQueueToggle.checked,
        };

        await writeLanguageSwitchState(state);
        sessionStorage.setItem(LANGUAGE_SWITCH_STATE_KEY, '1');
    }

    async function restoreLanguageSwitchState() {
        if (sessionStorage.getItem(LANGUAGE_SWITCH_STATE_KEY) !== '1') {
            return;
        }

        sessionStorage.removeItem(LANGUAGE_SWITCH_STATE_KEY);

        if (!supportsIndexedDb()) {
            return;
        }

        try {
            const savedState = await readLanguageSwitchState();
            if (!savedState) {
                return;
            }

            fileQueue = Array.isArray(savedState.fileQueue)
                ? savedState.fileQueue.filter((file) => file instanceof File && isMidiFile(file))
                : [];

            const restoredLayerCount = clamp(
                Math.trunc(Number(savedState.layerCount) || 1),
                1,
                maxLayers,
            );
            layerCount = restoredLayerCount;

            for (let index = 0; index < maxLayers; index += 1) {
                const rawLayer = Array.isArray(savedState.layers) ? savedState.layers[index] : null;
                layers[index] = rawLayer ? sanitiseLayerState(rawLayer, index) : createDefaultLayer(index);
            }

            if (typeof savedState.rate === 'string' && Array.from(rateSelect.options).some((option) => option.value === savedState.rate)) {
                rateSelect.value = savedState.rate;
            }

            if (typeof savedState.keepQueue === 'boolean') {
                keepQueueToggle.checked = savedState.keepQueue;
                localStorage.setItem('keepQueueAfterSynth', String(savedState.keepQueue));
            }
        } finally {
            await clearLanguageSwitchState();
        }
    }

    function isMidiFile(file) {
        return (
            file.type === 'audio/midi'
            || file.type === 'audio/x-midi'
            || /\.midi?$/i.test(file.name)
        );
    }

    function formatFileSize(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return '0 KB';
        }

        if (bytes < 1024 * 1024) {
            return `${Math.max(1, Math.round(bytes / 1024))} KB`;
        }

        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }

    function renderQueue() {
        queueList.innerHTML = '';
        fileQueue.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'queue-item';
            li.setAttribute('draggable', 'true');
            li.setAttribute('data-index', index);
            li.setAttribute('data-full-name', file.name);

            const fileInfo = document.createElement('div');
            fileInfo.className = 'min-w-0';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;

            const fileMeta = document.createElement('div');
            fileMeta.className = 'file-meta';
            fileMeta.textContent = formatFileSize(file.size);

            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'remove-btn';
            removeButton.innerHTML = ICONS.svg('x');
            removeButton.setAttribute('aria-label', t('queue.remove_file', { filename: file.name }));
            removeButton.addEventListener('click', () => window.removeFromQueue(index));

            fileInfo.append(fileName, fileMeta);
            li.append(fileInfo, removeButton);
            queueList.appendChild(li);
        });
        queueCountSpan.textContent = fileQueue.length;
        queueCountAction.textContent = fileQueue.length;
        queueEmpty.style.display = fileQueue.length > 0 ? 'none' : 'grid';
        clearQueueBtn.style.display = fileQueue.length > 0 ? 'block' : 'none';
        submitBtn.disabled = fileQueue.length === 0;
    }

    function renderConvertedFiles() {
        convertedList.innerHTML = '';
        convertedFiles.forEach((file, index) => {
            const li = document.createElement('li');
            li.className = 'converted-item';

            const fileInfo = document.createElement('div');
            fileInfo.className = 'min-w-0';

            const fileName = document.createElement('div');
            fileName.className = 'file-name';
            fileName.textContent = file.name;

            const fileMeta = document.createElement('div');
            fileMeta.className = 'file-meta';
            fileMeta.textContent = `${formatFileSize(file.size)} / ${file.sourceName}`;

            const downloadButton = document.createElement('button');
            downloadButton.type = 'button';
            downloadButton.className = 'download-btn';
            downloadButton.textContent = t('converted.download');
            downloadButton.addEventListener('click', () => downloadConvertedFile(index));

            fileInfo.append(fileName, fileMeta);
            li.append(fileInfo, downloadButton);
            convertedList.appendChild(li);
        });

        convertedCount.textContent = convertedFiles.length;
        convertedEmpty.style.display = convertedFiles.length > 0 ? 'none' : 'grid';
        clearConvertedBtn.style.display = convertedFiles.length > 0 ? 'block' : 'none';
    }

    function downloadConvertedFile(index) {
        const convertedFile = convertedFiles[index];
        if (!convertedFile) {
            return;
        }

        const anchor = document.createElement('a');
        anchor.href = convertedFile.url;
        anchor.download = convertedFile.name;
        document.body.appendChild(anchor);
        anchor.click();
        document.body.removeChild(anchor);
    }

    function addConvertedFile(downloadName, blob, sourceName) {
        convertedFiles.unshift({
            name: downloadName,
            sourceName,
            size: blob.size,
            url: window.URL.createObjectURL(blob),
            objectUrl: true,
        });
        renderConvertedFiles();
    }

    function addConvertedServerFile(downloadName, size, sourceName, downloadUrl, deleteUrl) {
        convertedFiles.unshift({
            name: downloadName,
            sourceName,
            size,
            url: downloadUrl,
            objectUrl: false,
            deleteUrl,
        });
        renderConvertedFiles();
    }

    function releaseConvertedServerFile(file) {
        if (!file.deleteUrl) {
            return Promise.resolve();
        }

        return fetch(file.deleteUrl, {
            method: 'DELETE',
            keepalive: true,
        }).catch((error) => {
            console.warn('Failed to delete converted server file.', error);
        });
    }

    async function clearConvertedFiles() {
        const filesToClear = [...convertedFiles];
        convertedFiles = [];
        renderConvertedFiles();

        filesToClear.forEach((file) => {
            if (file.objectUrl) {
                window.URL.revokeObjectURL(file.url);
            }
        });

        await Promise.all(filesToClear.map(releaseConvertedServerFile));
    }

    queueList.addEventListener('dragstart', (event) => {
        const item = event.target.closest('.queue-item');
        if (!item) return;
        dragStartIndex = parseInt(item.dataset.index, 10);
        item.classList.add('dragging');
    });

    queueList.addEventListener('dragend', (event) => {
        const item = event.target.closest('.queue-item');
        if (item) item.classList.remove('dragging');
    });

    queueList.addEventListener('dragover', (event) => {
        event.preventDefault();
        const target = event.target.closest('.queue-item');
        if (!target) return;
        document.querySelectorAll('.queue-item').forEach(item => item.classList.remove('drag-over'));
        target.classList.add('drag-over');
    });

    queueList.addEventListener('dragleave', (event) => {
        const target = event.target.closest('.queue-item');
        if (target) target.classList.remove('drag-over');
    });

    queueList.addEventListener('drop', (event) => {
        event.preventDefault();
        const target = event.target.closest('.queue-item');
        if (!target) return;
        target.classList.remove('drag-over');
        const dragEndIndex = parseInt(target.dataset.index, 10);
        const [draggedItem] = fileQueue.splice(dragStartIndex, 1);
        fileQueue.splice(dragEndIndex, 0, draggedItem);
        renderQueue();
    });

    function addToQueue(files) {
        for (const file of files) {
            if (isMidiFile(file)) fileQueue.push(file);
        }
        renderQueue();
        fileInput.value = '';
    }

    window.removeFromQueue = (index) => {
        fileQueue.splice(index, 1);
        renderQueue();
    };

    clearQueueBtn.addEventListener('click', () => {
        fileQueue = [];
        renderQueue();
        fileInput.value = '';
    });

    clearConvertedBtn.addEventListener('click', () => {
        if (window.confirm(t('converted.clear_confirm'))) {
            clearConvertedFiles();
        }
    });

    window.addEventListener('beforeunload', clearConvertedFiles);

    dropZone.addEventListener('dragover', (event) => {
        event.preventDefault();
        dropZone.classList.add('dragover');
    });

    ['dragleave', 'dragend'].forEach((type) => {
        dropZone.addEventListener(type, () => dropZone.classList.remove('dragover'));
    });

    dropZone.addEventListener('drop', (event) => {
        event.preventDefault();
        dropZone.classList.remove('dragover');
        if (event.dataTransfer.files.length) addToQueue(event.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => addToQueue(fileInput.files));

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function formatFrequency(value) {
        return value >= 1000 ? `${(value / 1000).toFixed(2)} kHz` : `${value.toFixed(1)} Hz`;
    }

    function formatGainDb(value) {
        return `${value >= 0 ? '+' : ''}${value.toFixed(1)} dB`;
    }

    function plotWidth() {
        return CURVE_WIDTH - CURVE_MARGIN.left - CURVE_MARGIN.right;
    }

    function plotHeight() {
        return CURVE_HEIGHT - CURVE_MARGIN.top - CURVE_MARGIN.bottom;
    }

    function frequencyToX(frequencyHz) {
        const ratio = (Math.log(frequencyHz) - Math.log(MIN_CURVE_FREQUENCY_HZ)) / curveLogSpan;
        return CURVE_MARGIN.left + (ratio * plotWidth());
    }

    function xToFrequency(x) {
        const ratio = clamp((x - CURVE_MARGIN.left) / plotWidth(), 0, 1);
        return MIN_CURVE_FREQUENCY_HZ * ((MAX_CURVE_FREQUENCY_HZ / MIN_CURVE_FREQUENCY_HZ) ** ratio);
    }

    function gainToY(gainDb) {
        const ratio = (MAX_CURVE_GAIN_DB - gainDb) / (MAX_CURVE_GAIN_DB - MIN_CURVE_GAIN_DB);
        return CURVE_MARGIN.top + (ratio * plotHeight());
    }

    function yToGain(y) {
        const ratio = clamp((y - CURVE_MARGIN.top) / plotHeight(), 0, 1);
        return MAX_CURVE_GAIN_DB - (ratio * (MAX_CURVE_GAIN_DB - MIN_CURVE_GAIN_DB));
    }

    function evaluateCurveGainDb(points, frequencyHz) {
        if (!points.length) return 0.0;
        if (frequencyHz <= points[0].frequency_hz) return points[0].gain_db;
        if (frequencyHz >= points[points.length - 1].frequency_hz) return points[points.length - 1].gain_db;
        for (let index = 0; index < points.length - 1; index += 1) {
            const leftPoint = points[index];
            const rightPoint = points[index + 1];
            if (frequencyHz >= leftPoint.frequency_hz && frequencyHz <= rightPoint.frequency_hz) {
                const leftLog = Math.log(leftPoint.frequency_hz);
                const rightLog = Math.log(rightPoint.frequency_hz);
                const frequencyLog = Math.log(frequencyHz);
                const ratio = (frequencyLog - leftLog) / (rightLog - leftLog);
                return leftPoint.gain_db + (ratio * (rightPoint.gain_db - leftPoint.gain_db));
            }
        }
        return points[points.length - 1].gain_db;
    }

    function createWaveOptions(currentType) {
        const options = [
            ['pulse', t('wave.pulse')],
            ['sine', t('wave.sine')],
            ['sawtooth', t('wave.sawtooth')],
            ['triangle', t('wave.triangle')],
        ];
        return options.map(([value, label]) => `
            <option value="${value}" ${currentType === value ? 'selected' : ''}>${label}</option>
        `).join('');
    }

    function buildCurvePath(points) {
        return points.map((point, index) => {
            const command = index === 0 ? 'M' : 'L';
            return `${command} ${frequencyToX(point.frequency_hz).toFixed(2)} ${gainToY(point.gain_db).toFixed(2)}`;
        }).join(' ');
    }

    function buildCurveArea(points) {
        const startX = frequencyToX(points[0].frequency_hz).toFixed(2);
        const endX = frequencyToX(points[points.length - 1].frequency_hz).toFixed(2);
        const bottomY = (CURVE_MARGIN.top + plotHeight()).toFixed(2);
        return `M ${startX} ${bottomY} ${buildCurvePath(points).slice(2)} L ${endX} ${bottomY} Z`;
    }

    function buildCurveSvg(layer, layerIndex) {
        const selectedPoint = layer.frequencyCurve[layer.selectedPointIndex] || layer.frequencyCurve[0];
        const gainTicks = [MAX_CURVE_GAIN_DB, 0, MIN_CURVE_GAIN_DB];
        const freqTicks = [MIN_CURVE_FREQUENCY_HZ, 27.5, 110.0, 440.0, 1760.0, MAX_CURVE_FREQUENCY_HZ];

        return `
            <div class="curve-summary">
                ${t('curve.selected_point', {
                    frequency: formatFrequency(selectedPoint.frequency_hz),
                    gain: formatGainDb(selectedPoint.gain_db),
                })}
            </div>
            <svg
                class="curve-svg"
                id="curveSvg${layerIndex}"
                viewBox="0 0 ${CURVE_WIDTH} ${CURVE_HEIGHT}"
                aria-label="${t('curve.aria_label', { index: layerIndex + 1 })}"
            >
                <rect
                    x="${CURVE_MARGIN.left}"
                    y="${CURVE_MARGIN.top}"
                    width="${plotWidth()}"
                    height="${plotHeight()}"
                    fill="transparent"
                ></rect>
                ${gainTicks.map((gainDb) => `
                    <g>
                        <line
                            class="${gainDb === 0 ? 'curve-zero-line' : 'curve-grid-line'}"
                            x1="${CURVE_MARGIN.left}"
                            y1="${gainToY(gainDb)}"
                            x2="${CURVE_MARGIN.left + plotWidth()}"
                            y2="${gainToY(gainDb)}"
                        ></line>
                        <text class="curve-axis-label" x="4" y="${gainToY(gainDb) + 4}">${formatGainDb(gainDb)}</text>
                    </g>
                `).join('')}
                ${freqTicks.map((frequencyHz) => `
                    <g>
                        <line
                            class="curve-grid-line"
                            x1="${frequencyToX(frequencyHz)}"
                            y1="${CURVE_MARGIN.top}"
                            x2="${frequencyToX(frequencyHz)}"
                            y2="${CURVE_MARGIN.top + plotHeight()}"
                        ></line>
                        <text
                            class="curve-axis-label"
                            x="${frequencyToX(frequencyHz)}"
                            y="${CURVE_HEIGHT - 6}"
                            text-anchor="middle"
                        >${frequencyHz >= 1000 ? `${(frequencyHz / 1000).toFixed(1)}k` : Math.round(frequencyHz)}</text>
                    </g>
                `).join('')}
                <path class="curve-fill" d="${buildCurveArea(layer.frequencyCurve)}"></path>
                <path class="curve-path" d="${buildCurvePath(layer.frequencyCurve)}"></path>
                ${layer.frequencyCurve.map((point, pointIndex) => {
                    const isEndpoint = pointIndex === 0 || pointIndex === layer.frequencyCurve.length - 1;
                    const pointRadius = isEndpoint ? 3.4 : 3.0;

                    return `
                        <circle
                            class="curve-point-hit"
                            cx="${frequencyToX(point.frequency_hz)}"
                            cy="${gainToY(point.gain_db)}"
                            r="7"
                            onpointerdown="startCurvePointDrag(${layerIndex}, ${pointIndex}, event)"
                            onclick="selectCurvePoint(${layerIndex}, ${pointIndex})"
                        ></circle>
                        <circle
                            class="curve-point ${layer.selectedPointIndex === pointIndex ? 'selected' : ''}"
                            cx="${frequencyToX(point.frequency_hz)}"
                            cy="${gainToY(point.gain_db)}"
                            r="${pointRadius}"
                        ></circle>
                    `;
                }).join('')}
            </svg>
        `;
    }

    function faderFillPercent(value, min, max) {
        const ratio = (Number(value) - min) / (max - min);
        return `${clamp(ratio * 100, 0, 100).toFixed(2)}%`;
    }

    function createFaderScale(ticks, min, max) {
        return ticks.map((tick, index) => {
            const position = faderFillPercent(tick.value, min, max);
            const edgeClass = index === 0
                ? 'is-start'
                : index === ticks.length - 1
                    ? 'is-end'
                    : '';

            return `
                <span
                    class="fader-scale-mark ${edgeClass}"
                    style="--tick-position: ${position}"
                    aria-hidden="true"
                ></span>
                <span
                    class="fader-scale-label ${edgeClass}"
                    style="--tick-position: ${position}"
                >${tick.label}</span>
            `;
        }).join('');
    }

    function updateFaderFill(input) {
        if (!input) {
            return;
        }

        const min = Number(input.min);
        const max = Number(input.max);
        input.style.setProperty('--fill', faderFillPercent(input.value, min, max));
    }

    function renderLayers() {
        layersContainer.innerHTML = '';

        for (let layerIndex = 0; layerIndex < layerCount; layerIndex += 1) {
            const layer = layers[layerIndex];
            const selectedPoint = layer.frequencyCurve[layer.selectedPointIndex] || layer.frequencyCurve[0];
            const canRemoveSelected = layer.frequencyCurve.length > 2
                && layer.selectedPointIndex > 0
                && layer.selectedPointIndex < layer.frequencyCurve.length - 1;

            const card = document.createElement('div');
            card.className = 'layer-card';
            card.innerHTML = `
                <div class="layer-title-row">
                    <div>
                        <div class="layer-title">${t('layer.title', { index: layerIndex + 1 })}</div>
                    </div>
                    <button
                        type="button"
                        class="preview-btn"
                        onclick="playPreview(${layerIndex})"
                        title="${t('layer.play_preview')}"
                        aria-label="${t('layer.play_preview')}"
                    >${ICONS.svg('play')}</button>
                </div>
                <div class="layer-control-grid">
                    <div class="field-block waveform-field">
                        <label class="field-label" for="waveType${layerIndex}">${t('layer.waveform_type')}</label>
                        <select
                            class="form-select control-select"
                            id="waveType${layerIndex}"
                            onchange="updateLayerType(${layerIndex}, this.value)"
                        >
                            ${createWaveOptions(layer.type)}
                        </select>
                    </div>
                    <div class="field-block" style="display: ${layer.type === 'pulse' ? 'grid' : 'none'};">
                        <label class="fader-label" for="dutyFader${layerIndex}">
                            <span>${t('layer.pulse_width')}</span>
                            <input
                                type="number"
                                class="readout"
                                id="dutyValue${layerIndex}"
                                min="0.01"
                                max="0.99"
                                step="0.01"
                                value="${layer.duty.toFixed(2)}"
                                inputmode="decimal"
                                onchange="updateLayerDuty(${layerIndex}, this.value, this)"
                            >
                        </label>
                        <div class="fader-shell">
                            <input
                                type="range"
                                class="fader-input"
                                id="dutyFader${layerIndex}"
                                min="0.01"
                                max="0.99"
                                step="0.01"
                                value="${layer.duty}"
                                style="--fill: ${faderFillPercent(layer.duty, 0.01, 0.99)}"
                                oninput="updateLayerDuty(${layerIndex}, this.value, this)"
                            >
                        </div>
                        <div class="fader-scale" aria-hidden="true">
                            ${createFaderScale([
                                { value: 0.01, label: '0.01' },
                                { value: 0.25, label: '0.25' },
                                { value: 0.50, label: '0.50' },
                                { value: 0.75, label: '0.75' },
                                { value: 0.99, label: '0.99' },
                            ], 0.01, 0.99)}
                        </div>
                    </div>
                    <div class="field-block layer-volume-control ${layer.type === 'pulse' ? '' : 'layer-volume-wide'}">
                        <label class="fader-label" for="volumeFader${layerIndex}">
                            <span>${t('layer.base_volume')}</span>
                            <input
                                type="number"
                                class="readout"
                                id="volumeValue${layerIndex}"
                                min="0.00"
                                max="2.00"
                                step="0.01"
                                value="${layer.volume.toFixed(2)}"
                                inputmode="decimal"
                                onchange="updateLayerVolume(${layerIndex}, this.value, this)"
                            >
                        </label>
                        <div class="fader-shell">
                            <input
                                type="range"
                                class="fader-input"
                                id="volumeFader${layerIndex}"
                                min="0.0"
                                max="2.0"
                                step="0.01"
                                value="${layer.volume}"
                                style="--fill: ${faderFillPercent(layer.volume, 0.0, 2.0)}"
                                oninput="updateLayerVolume(${layerIndex}, this.value, this)"
                            >
                        </div>
                        <div class="fader-scale" aria-hidden="true">
                            ${createFaderScale([
                                { value: 0.00, label: '0.00' },
                                { value: 0.50, label: '0.50' },
                                { value: 1.00, label: '1.00' },
                                { value: 1.50, label: '1.50' },
                                { value: 2.00, label: '2.00' },
                            ], 0.0, 2.0)}
                        </div>
                    </div>
                    <div class="control-switch layer-curve-toggle">
                        <input
                            class="control-switch-input"
                            type="checkbox"
                            id="curveToggle${layerIndex}"
                            ${layer.curveEnabled ? 'checked' : ''}
                            onchange="toggleCurveEnabled(${layerIndex}, this.checked)"
                        >
                        <label class="control-switch-label" for="curveToggle${layerIndex}">
                            <span class="control-switch-track" aria-hidden="true">
                                <span class="control-switch-thumb"></span>
                            </span>
                            <span class="control-switch-text">${t('layer.enable_curve')}</span>
                        </label>
                    </div>
                </div>
                ${layer.curveEnabled ? `
                    <div class="curve-panel">
                        <div class="curve-toolbar">
                            <button
                                type="button"
                                class="utility-btn"
                                onclick="addCurvePoint(${layerIndex})"
                                ${layer.frequencyCurve.length >= MAX_CURVE_POINTS ? 'disabled' : ''}
                            >
                                ${t('curve.add_point')}
                            </button>
                            <button
                                type="button"
                                class="utility-btn"
                                onclick="removeSelectedPoint(${layerIndex})"
                                ${canRemoveSelected ? '' : 'disabled'}
                            >
                                ${t('curve.remove_selected')}
                            </button>
                            <button
                                type="button"
                                class="utility-btn"
                                onclick="resetCurve(${layerIndex})"
                            >
                                ${t('curve.reset')}
                            </button>
                        </div>
                        <div class="curve-summary">
                            ${t('curve.drag_help')}
                        </div>
                        ${buildCurveSvg(layer, layerIndex)}
                        <div class="curve-summary mt-2">
                            ${t('curve.points_summary', {
                                count: layer.frequencyCurve.length,
                                frequency: formatFrequency(selectedPoint.frequency_hz),
                                gain: formatGainDb(selectedPoint.gain_db),
                            })}
                        </div>
                    </div>
                ` : ''}
            `;
            layersContainer.appendChild(card);
        }

        updateLayerButtons();
    }

    function updateLayerButtons() {
        addLayerBtn.disabled = layerCount === maxLayers;
        removeLayerBtn.disabled = layerCount === 1;
        removeLayerBtn.style.display = 'inline-flex';
    }

    function activeLayersPayload() {
        return layers.slice(0, layerCount).map((layer) => ({
            type: layer.type,
            duty: Number(layer.duty.toFixed(4)),
            volume: Number(layer.volume.toFixed(4)),
            frequency_curve: layer.curveEnabled
                ? layer.frequencyCurve.map((point) => ({
                    frequency_hz: point.frequency_hz,
                    gain_db: Number(point.gain_db.toFixed(4)),
                }))
                : [],
        }));
    }

    function updateLayerType(layerIndex, value) {
        layers[layerIndex].type = value;
        renderLayers();
    }

    function normaliseDecimalInput(value, min, max) {
        const parsedValue = parseFloat(value);
        const finiteValue = Number.isFinite(parsedValue) ? parsedValue : min;
        return Number(clamp(finiteValue, min, max).toFixed(2));
    }

    function updateLayerDuty(layerIndex, value, input = null) {
        const duty = normaliseDecimalInput(value, 0.01, 0.99);
        layers[layerIndex].duty = duty;
        const dutyValue = document.getElementById(`dutyValue${layerIndex}`);
        if (dutyValue) {
            dutyValue.value = duty.toFixed(2);
        }
        const dutyFader = document.getElementById(`dutyFader${layerIndex}`);
        if (dutyFader) {
            dutyFader.value = duty.toFixed(2);
        }
        updateFaderFill(dutyFader || input);
    }

    function updateLayerVolume(layerIndex, value, input = null) {
        const volume = normaliseDecimalInput(value, 0.0, 2.0);
        layers[layerIndex].volume = volume;
        const volumeValue = document.getElementById(`volumeValue${layerIndex}`);
        if (volumeValue) {
            volumeValue.value = volume.toFixed(2);
        }
        const volumeFader = document.getElementById(`volumeFader${layerIndex}`);
        if (volumeFader) {
            volumeFader.value = volume.toFixed(2);
        }
        updateFaderFill(volumeFader || input);
    }

    function toggleCurveEnabled(layerIndex, enabled) {
        const layer = layers[layerIndex];
        layer.curveEnabled = enabled;
        if (!layer.frequencyCurve.length) {
            layer.frequencyCurve = createDefaultCurve();
            layer.selectedPointIndex = 0;
        }
        window.clearTimeout(layerRenderTimer);
        layerRenderTimer = window.setTimeout(() => {
            layerRenderTimer = null;
            renderLayers();
        }, CONTROL_SWITCH_TRANSITION_MS);
    }

    function selectCurvePoint(layerIndex, pointIndex) {
        layers[layerIndex].selectedPointIndex = pointIndex;
        renderLayers();
    }

    function addCurvePoint(layerIndex) {
        const layer = layers[layerIndex];
        if (layer.frequencyCurve.length >= MAX_CURVE_POINTS) return;

        let widestGapIndex = 0;
        let widestGap = -1;
        for (let index = 0; index < layer.frequencyCurve.length - 1; index += 1) {
            const gap = Math.log(layer.frequencyCurve[index + 1].frequency_hz) - Math.log(layer.frequencyCurve[index].frequency_hz);
            if (gap > widestGap) {
                widestGap = gap;
                widestGapIndex = index;
            }
        }

        const leftPoint = layer.frequencyCurve[widestGapIndex];
        const rightPoint = layer.frequencyCurve[widestGapIndex + 1];
        const newFrequency = Math.sqrt(leftPoint.frequency_hz * rightPoint.frequency_hz);
        const newGain = evaluateCurveGainDb(layer.frequencyCurve, newFrequency);

        layer.frequencyCurve.splice(widestGapIndex + 1, 0, {
            frequency_hz: newFrequency,
            gain_db: newGain,
        });
        layer.selectedPointIndex = widestGapIndex + 1;
        renderLayers();
    }

    function removeSelectedPoint(layerIndex) {
        const layer = layers[layerIndex];
        if (layer.selectedPointIndex <= 0 || layer.selectedPointIndex >= layer.frequencyCurve.length - 1) {
            return;
        }

        layer.frequencyCurve.splice(layer.selectedPointIndex, 1);
        layer.selectedPointIndex = Math.max(0, layer.selectedPointIndex - 1);
        renderLayers();
    }

    function resetCurve(layerIndex) {
        layers[layerIndex].frequencyCurve = createDefaultCurve();
        layers[layerIndex].selectedPointIndex = 0;
        renderLayers();
    }

    window.updateLayerType = updateLayerType;
    window.updateLayerDuty = updateLayerDuty;
    window.updateLayerVolume = updateLayerVolume;
    window.toggleCurveEnabled = toggleCurveEnabled;
    window.addCurvePoint = addCurvePoint;
    window.removeSelectedPoint = removeSelectedPoint;
    window.resetCurve = resetCurve;
    window.selectCurvePoint = selectCurvePoint;

    window.startCurvePointDrag = (layerIndex, pointIndex, event) => {
        event.preventDefault();
        layers[layerIndex].selectedPointIndex = pointIndex;
        dragState = { layerIndex, pointIndex };
        renderLayers();
    };

    window.addLayer = () => {
        if (layerCount >= maxLayers) return;
        layerCount += 1;
        layers[layerCount - 1].active = true;
        renderLayers();
    };

    window.removeLayer = () => {
        if (layerCount <= 1) return;
        layers[layerCount - 1] = createDefaultLayer(layerCount - 1);
        layerCount -= 1;
        renderLayers();
    };

    window.playPreview = (layerIndex) => {
        const layer = layers[layerIndex];
        let src = `${layer.type}.wav`;
        if (layer.type === 'pulse') {
            src = `pulse_${layer.duty < 0.18 ? '10' : layer.duty < 0.38 ? '25' : '50'}.wav`;
        }
        previewAudio.src = `/static/previews/${src}`;
        previewAudio.play().catch((error) => console.error('Preview failed:', error));
    };

    addLayerBtn.addEventListener('click', window.addLayer);
    removeLayerBtn.addEventListener('click', window.removeLayer);

    layersContainer.addEventListener('pointerdown', (event) => {
        const fader = event.target.closest('.fader-input');
        if (fader) {
            fader.classList.add('is-dragging');
        }
    });

    window.addEventListener('pointermove', (event) => {
        if (!dragState) return;

        const { layerIndex, pointIndex } = dragState;
        const svg = document.getElementById(`curveSvg${layerIndex}`);
        if (!svg) return;

        const rect = svg.getBoundingClientRect();
        const localX = ((event.clientX - rect.left) / rect.width) * CURVE_WIDTH;
        const localY = ((event.clientY - rect.top) / rect.height) * CURVE_HEIGHT;
        const layer = layers[layerIndex];
        const points = layer.frequencyCurve;
        const point = points[pointIndex];

        point.gain_db = Number(clamp(yToGain(localY), MIN_CURVE_GAIN_DB, MAX_CURVE_GAIN_DB).toFixed(4));
        if (pointIndex === 0) {
            point.frequency_hz = MIN_CURVE_FREQUENCY_HZ;
        } else if (pointIndex === points.length - 1) {
            point.frequency_hz = MAX_CURVE_FREQUENCY_HZ;
        } else {
            const minFrequency = points[pointIndex - 1].frequency_hz * 1.0001;
            const maxFrequency = points[pointIndex + 1].frequency_hz / 1.0001;
            point.frequency_hz = clamp(xToFrequency(localX), minFrequency, maxFrequency);
        }

        renderLayers();
    });

    window.addEventListener('pointerup', () => {
        dragState = null;
        document.querySelectorAll('.fader-input.is-dragging').forEach((fader) => {
            fader.classList.remove('is-dragging');
        });
    });

    function extractDownloadName(response, fallbackName) {
        const disposition = response.headers.get('Content-Disposition') || '';
        const utfMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i);
        if (utfMatch) return decodeURIComponent(utfMatch[1]);
        const plainMatch = disposition.match(/filename="?([^"]+)"?/i);
        return plainMatch ? plainMatch[1] : fallbackName;
    }

    function sleep(ms) {
        return new Promise((resolve) => window.setTimeout(resolve, ms));
    }

    async function readJsonResponse(response) {
        try {
            return await response.json();
        } catch (error) {
            return {};
        }
    }

    async function waitForSynthesiseJob(jobId, file, index, total) {
        while (true) {
            const response = await fetch(`/synthesise/jobs/${jobId}`);
            const payload = await readJsonResponse(response);
            if (!response.ok && !['ready', 'failed', 'expired'].includes(payload.status)) {
                throw new Error(payload.error || response.statusText);
            }

            if (payload.status === 'ready') {
                processingStatus.textContent = t('status.file_ready', {
                    current: index + 1,
                    total,
                    filename: file.name,
                });
                return payload;
            }

            if (payload.status === 'failed' || payload.status === 'expired') {
                throw new Error(payload.error || payload.status);
            }

            processingStatus.textContent = t('status.rendering_file', {
                current: index + 1,
                total,
                filename: file.name,
            });
            await sleep(1000);
        }
    }

    synthForm.onsubmit = async (event) => {
        event.preventDefault();
        loading.classList.add('is-visible');
        submitBtn.disabled = true;

        const filesToProcess = [...fileQueue];
        const failedFiles = [];
        const layersJson = JSON.stringify(activeLayersPayload());
        for (let index = 0; index < filesToProcess.length; index += 1) {
            const file = filesToProcess[index];
            processingStatus.textContent = t('status.processing_file', {
                current: index + 1,
                total: filesToProcess.length,
                filename: file.name,
            });

            const formData = new FormData();
            formData.append('rate', rateSelect.value);
            formData.append('layers_json', layersJson);
            formData.append('midi_file', file);

            try {
                const response = await fetch('/synthesise/jobs', {
                    method: 'POST',
                    body: formData,
                });
                if (!response.ok) {
                    const errorPayload = await readJsonResponse(response);
                    failedFiles.push(file);
                    alert(t('alerts.processing_error', {
                        filename: file.name,
                        error: errorPayload.error || response.statusText,
                    }));
                    continue;
                }

                const job = await readJsonResponse(response);
                if (!job.job_id) {
                    throw new Error(job.error || response.statusText);
                }
                const readyJob = job.status === 'ready'
                    ? job
                    : await waitForSynthesiseJob(job.job_id, file, index, filesToProcess.length);
                const downloadUrl = new URL(readyJob.download_url, window.location.origin).toString();
                addConvertedServerFile(
                    readyJob.download_name || `${file.name.replace(/\.[^.]+$/, '') || 'output'}.wav`,
                    readyJob.size_bytes || 0,
                    file.name,
                    downloadUrl,
                    readyJob.delete_url ? new URL(readyJob.delete_url, window.location.origin).toString() : null,
                );
                processingStatus.textContent = t('status.downloading_file', {
                    current: index + 1,
                    total: filesToProcess.length,
                    filename: file.name,
                });
                downloadConvertedFile(0);
            } catch (error) {
                failedFiles.push(file);
                alert(t('alerts.processing_error', {
                    filename: file.name,
                    error: error.message || t('alerts.processing_unknown', { filename: file.name }),
                }));
            }
        }

        loading.classList.remove('is-visible');
        submitBtn.disabled = false;
        processingStatus.textContent = t('status.generating_audio');
        if (!keepQueueToggle.checked) {
            fileQueue = failedFiles;
        }
        renderQueue();
        fileInput.value = '';
    };

    async function initialisePage() {
        try {
            await restoreLanguageSwitchState();
        } catch (error) {
            console.warn('Failed to restore page state after language change.', error);
        }
        renderQueue();
        renderConvertedFiles();
        renderLayers();
    }

    initialisePage();
