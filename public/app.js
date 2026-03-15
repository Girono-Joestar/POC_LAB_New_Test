/* ==========================================================================
   POC AI Lab — Frontend Logic
   With comprehensive console logging for debugging and monitoring.
   ========================================================================== */

// ---------------------------------------------------------------------------
// Logger Utility — Prefixes all logs with [POC-AI-LAB] and timestamps
// ---------------------------------------------------------------------------
const LOG_PREFIX = '[POC-AI-LAB]';
const log = {
    info: (...args) => console.log(`${LOG_PREFIX} ℹ️`, new Date().toISOString(), ...args),
    warn: (...args) => console.warn(`${LOG_PREFIX} ⚠️`, new Date().toISOString(), ...args),
    error: (...args) => console.error(`${LOG_PREFIX} ❌`, new Date().toISOString(), ...args),
    debug: (...args) => console.debug(`${LOG_PREFIX} 🐛`, new Date().toISOString(), ...args),
    net: (...args) => console.log(`${LOG_PREFIX} 🌐`, new Date().toISOString(), ...args),
    ui: (...args) => console.log(`${LOG_PREFIX} 🎨`, new Date().toISOString(), ...args),
};

log.info('App script loaded — initializing…');

let currentExperimentId = null;
let carouselIndex = 0;
let carouselImages = [];

// ---------------------------------------------------------------------------
// DOM References
// ---------------------------------------------------------------------------
const $list = document.getElementById('experiment-list');
const $details = document.getElementById('experiment-details');
const $loader = document.getElementById('loader');
const $hero = document.getElementById('hero');
const $backBtn = document.getElementById('back-btn');
const $title = document.getElementById('exp-title');
const $narration = document.getElementById('narration-text');
const $audio = document.getElementById('exp-audio');
const $track = document.getElementById('carousel-track');
const $dots = document.getElementById('carousel-dots');
const $prevBtn = document.getElementById('carousel-prev');
const $nextBtn = document.getElementById('carousel-next');
const $chatMsgs = document.getElementById('chat-messages');
const $chatInput = document.getElementById('chat-input');
const $sendBtn = document.getElementById('send-btn');

log.debug('DOM references acquired:', {
    list: !!$list, details: !!$details, loader: !!$loader, hero: !!$hero,
    backBtn: !!$backBtn, title: !!$title, audio: !!$audio, track: !!$track,
    chatMsgs: !!$chatMsgs, chatInput: !!$chatInput, sendBtn: !!$sendBtn,
});

// ---------------------------------------------------------------------------
// Network Helper — Wrapper around fetch with logging
// ---------------------------------------------------------------------------
// Custom error class for API failures — gives proper stack traces + .detail/.status
class ApiError extends Error {
    constructor(status, detail, body = {}) {
        super(detail || `HTTP ${status}`);
        this.name = 'ApiError';
        this.status = status;
        this.detail = detail;
        this.body = body;
    }
}

async function apiFetch(url, options = {}) {
    const method = options.method || 'GET';
    const startTime = performance.now();
    log.net(`→ ${method} ${url}`);

    try {
        const res = await fetch(url, options);
        const elapsed = (performance.now() - startTime).toFixed(0);
        const logFn = res.ok ? log.net : log.warn;
        logFn(`← ${method} ${url} → ${res.status} (${elapsed}ms)`);

        if (!res.ok) {
            const errorBody = await res.json().catch(() => ({ detail: res.statusText }));
            log.error(`API error response:`, errorBody);
            throw new ApiError(res.status, errorBody.detail || res.statusText, errorBody);
        }

        const data = await res.json();
        log.debug(`Response data for ${url}:`, typeof data === 'object' ? `${JSON.stringify(data).substring(0, 200)}…` : data);
        return data;

    } catch (err) {
        if (err instanceof ApiError) throw err; // re-throw API errors
        const elapsed = (performance.now() - startTime).toFixed(0);
        log.error(`Network failure: ${method} ${url} after ${elapsed}ms —`, err.message || err);
        throw err;
    }
}

// ---------------------------------------------------------------------------
// Fetch & Render Experiment List
// ---------------------------------------------------------------------------
async function fetchExperiments() {
    log.info('Fetching experiment list…');
    try {
        const data = await apiFetch('/api/experiments');
        log.info(`Received ${data.length} experiments`);
        renderList(data);
    } catch (err) {
        log.error('Failed to load experiments:', err);
        $loader.innerHTML = `<p class="body-medium" style="color:var(--md-sys-color-error)">Failed to load experiments. Please refresh.</p>`;
    }
}

function renderList(experiments) {
    log.ui(`Rendering ${experiments.length} experiment cards`);
    $loader.classList.add('hidden');

    experiments.forEach((exp, i) => {
        const card = document.createElement('div');
        card.className = 'exp-card';
        card.style.animationDelay = `${i * 0.08}s`;
        card.setAttribute('data-exp-id', exp.id);

        card.innerHTML = `
            <img class="exp-card__img" src="${exp.thumbnail || ''}"
                 alt="${exp.apparatus}"
                 onerror="this.style.display='none'">
            <div class="exp-card__body">
                <p class="exp-card__title">${exp.apparatus}</p>
                <p class="exp-card__sub">${exp.narration_script ? exp.narration_script.substring(0, 80) + '…' : 'Tap to explore'}</p>
            </div>
        `;
        card.onclick = () => {
            log.ui(`Card clicked: ${exp.id} — "${exp.apparatus}"`);
            showDetails(exp.id);
        };
        $list.appendChild(card);
    });
    log.ui('Card rendering complete');
}

// ---------------------------------------------------------------------------
// Experiment Detail View
// ---------------------------------------------------------------------------
async function showDetails(id) {
    log.info(`Opening experiment detail: ${id}`);
    currentExperimentId = id;
    $list.classList.add('hidden');
    $hero.classList.add('hidden');
    $details.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Reset chat
    $chatMsgs.innerHTML = `<div class="message ai"><p>👋 Hi! Ask me anything about this experiment.</p></div>`;
    log.ui('Chat window reset');

    try {
        const exp = await apiFetch(`/api/experiments/${id}`);
        log.info(`Detail loaded for ${id}: "${exp.apparatus}", images=${(exp.images || []).length}, audio=${exp.audio_loc || 'NONE'}`);

        $title.textContent = exp.apparatus;
        $narration.textContent = exp.narration_script || '';

        // Audio
        if (exp.audio_loc) {
            $audio.src = exp.audio_loc;
            log.debug(`Audio source set: ${exp.audio_loc}`);
        } else {
            log.warn(`No audio file for experiment ${id}`);
            $audio.src = '';
        }

        // Carousel
        carouselImages = exp.images || [];
        carouselIndex = 0;
        log.debug(`Carousel images: ${carouselImages.length}`, carouselImages);
        buildCarousel();

    } catch (err) {
        log.error(`Failed to load detail for ${id}:`, err);
    }
}

function goBackToList() {
    log.ui('Navigating back to experiment list');
    $details.classList.add('hidden');
    $list.classList.remove('hidden');
    $hero.classList.remove('hidden');
    $audio.pause();
    log.debug('Audio paused');
    currentExperimentId = null;
}

// ---------------------------------------------------------------------------
// Carousel
// ---------------------------------------------------------------------------
function buildCarousel() {
    log.ui(`Building carousel with ${carouselImages.length} images`);
    $track.innerHTML = '';
    $dots.innerHTML = '';

    if (carouselImages.length === 0) {
        log.warn('No images available for carousel');
        $track.innerHTML = '<p style="margin:auto;color:var(--md-sys-color-outline)">No images available</p>';
        $prevBtn.classList.add('hidden');
        $nextBtn.classList.add('hidden');
        return;
    }

    carouselImages.forEach((src, i) => {
        const img = document.createElement('img');
        img.src = src;
        img.alt = `Experiment image ${i + 1}`;
        img.onerror = function () {
            log.warn(`Carousel image failed to load: ${src}`);
            this.style.display = 'none';
        };
        img.onload = function () {
            log.debug(`Carousel image loaded: ${src} (${this.naturalWidth}×${this.naturalHeight})`);
        };
        $track.appendChild(img);

        const dot = document.createElement('button');
        dot.className = 'carousel__dot' + (i === 0 ? ' active' : '');
        dot.ariaLabel = `Go to image ${i + 1}`;
        dot.onclick = () => {
            log.debug(`Carousel dot clicked: index ${i}`);
            goToSlide(i);
        };
        $dots.appendChild(dot);
    });

    $prevBtn.classList.toggle('hidden', carouselImages.length <= 1);
    $nextBtn.classList.toggle('hidden', carouselImages.length <= 1);
    updateCarousel();
    log.ui('Carousel built and ready');
}

function goToSlide(i) {
    carouselIndex = i;
    updateCarousel();
}

function updateCarousel() {
    $track.style.transform = `translateX(-${carouselIndex * 100}%)`;
    $dots.querySelectorAll('.carousel__dot').forEach((d, i) => {
        d.classList.toggle('active', i === carouselIndex);
    });
    log.debug(`Carousel slide: ${carouselIndex + 1}/${carouselImages.length}`);
}

$prevBtn.onclick = () => {
    carouselIndex = (carouselIndex - 1 + carouselImages.length) % carouselImages.length;
    log.debug(`Carousel prev → slide ${carouselIndex + 1}`);
    updateCarousel();
};
$nextBtn.onclick = () => {
    carouselIndex = (carouselIndex + 1) % carouselImages.length;
    log.debug(`Carousel next → slide ${carouselIndex + 1}`);
    updateCarousel();
};

// ---------------------------------------------------------------------------
// Chat
// ---------------------------------------------------------------------------
async function sendMessage() {
    const text = $chatInput.value.trim();
    if (!text) { log.warn('Empty chat message — ignoring'); return; }
    if (!currentExperimentId) { log.warn('No experiment selected — cannot chat'); return; }

    log.info(`💬 Sending chat — exp=${currentExperimentId}, prompt="${text.substring(0, 100)}…" (${text.length} chars)`);
    appendMessage('user', text);
    $chatInput.value = '';
    $chatInput.focus();

    // Show typing indicator
    const typingEl = appendMessage('ai typing', '●●● Thinking…');
    log.debug('Typing indicator shown');

    const startTime = performance.now();
    try {
        const data = await apiFetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: text, experiment_id: currentExperimentId }),
        });

        typingEl.remove();
        const elapsed = (performance.now() - startTime).toFixed(0);
        log.info(`✅ AI replied in ${elapsed}ms — ${(data.reply || '').length} chars`);
        log.debug(`AI reply preview: "${(data.reply || '').substring(0, 150)}…"`);
        appendMessage('ai', data.reply || 'No response received.');

    } catch (err) {
        typingEl.remove();
        const elapsed = (performance.now() - startTime).toFixed(0);
        log.error(`Chat failed after ${elapsed}ms:`, err);
        if (err.detail) {
            appendMessage('ai', `⚠️ ${err.detail}`);
        } else {
            appendMessage('ai', '⚠️ Could not connect to the assistant. Check your network.');
        }
    }
}

function appendMessage(className, text) {
    const div = document.createElement('div');
    div.className = `message ${className}`;
    const p = document.createElement('p');
    p.textContent = text;
    div.appendChild(p);
    $chatMsgs.appendChild(div);
    $chatMsgs.scrollTop = $chatMsgs.scrollHeight;
    log.debug(`Chat message appended: [${className}] "${text.substring(0, 80)}…"`);
    return div;
}

// Chat event listeners
$backBtn.onclick = goBackToList;
$sendBtn.onclick = sendMessage;
$chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ---------------------------------------------------------------------------
// URL query param support  (?exp=BKR-01)
// ---------------------------------------------------------------------------
function checkQueryParams() {
    const params = new URLSearchParams(window.location.search);
    const expId = params.get('exp');
    if (expId) {
        log.info(`🔗 QR deep-link detected: exp=${expId}`);
        showDetails(expId);
    } else {
        log.debug('No query params — showing list view');
    }
}

// ---------------------------------------------------------------------------
// Global Error Handler
// ---------------------------------------------------------------------------
window.onerror = function (msg, src, line, col, error) {
    log.error(`Uncaught error: ${msg} at ${src}:${line}:${col}`, error);
};
window.onunhandledrejection = function (event) {
    log.error('Unhandled promise rejection:', event.reason);
};

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------
log.info('🚀 Initializing app…');
fetchExperiments().then(() => {
    log.info('✅ Experiment list loaded — checking query params…');
    checkQueryParams();
}).catch(err => {
    log.error('Fatal: App initialization failed:', err);
});
