/* ==========================================================================
   MQC AI Lab — Frontend Logic v2.0
   Tabbed experiment view, rich procedure display, LangChain-backed chat.
   ========================================================================== */

// ─────────────────────────────────────────────────────────────────────────────
// Logger
// ─────────────────────────────────────────────────────────────────────────────
const LOG_PREFIX = '[MQC-LAB]';
const log = {
    info: (...a) => console.log(LOG_PREFIX, '✅', ...a),
    warn: (...a) => console.warn(LOG_PREFIX, '⚠️', ...a),
    error: (...a) => console.error(LOG_PREFIX, '❌', ...a),
    net: (...a) => console.log(LOG_PREFIX, '🌐', ...a),
};
log.info('App v2.0 loading…');

// ─────────────────────────────────────────────────────────────────────────────
// State
// ─────────────────────────────────────────────────────────────────────────────
let currentExpId = null;
let chatHistory = [];         // [{role, content}]
let carouselIndex = 0;
let carouselImages = [];
const sessionId = 'sess_' + Math.random().toString(36).slice(2, 10);

// ─────────────────────────────────────────────────────────────────────────────
// DOM refs
// ─────────────────────────────────────────────────────────────────────────────
const $list     = document.getElementById('experiment-list');
const $details  = document.getElementById('experiment-details');
const $loader   = document.getElementById('loader');
const $hero     = document.getElementById('hero');
const $backBtn  = document.getElementById('back-btn');
const $title    = document.getElementById('exp-title');
const $shortDesc= document.getElementById('exp-short-desc');
const $narration= document.getElementById('narration-text');
const $audio    = document.getElementById('exp-audio');
const $track    = document.getElementById('carousel-track');
const $dots     = document.getElementById('carousel-dots');
const $prevBtn  = document.getElementById('carousel-prev');
const $nextBtn  = document.getElementById('carousel-next');
const $chatMsgs = document.getElementById('chat-messages');
const $chatInput= document.getElementById('chat-input');
const $sendBtn  = document.getElementById('send-btn');
const $greeting = document.getElementById('chat-greeting');

// ─────────────────────────────────────────────────────────────────────────────
// Network helper
// ─────────────────────────────────────────────────────────────────────────────
class ApiError extends Error {
    constructor(status, detail) { super(detail || 'HTTP ' + status); this.status = status; this.detail = detail; }
}

async function apiFetch(url, options = {}) {
    log.net('→', options.method || 'GET', url);
    const t = performance.now();
    const res = await fetch(url, options);
    const ms = (performance.now() - t).toFixed(0);
    log.net('←', res.status, `(${ms}ms)`, url);
    if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new ApiError(res.status, body.detail || res.statusText);
    }
    return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Experiment list
// ─────────────────────────────────────────────────────────────────────────────
async function fetchExperiments() {
    try {
        const data = await apiFetch('/api/experiments');
        renderList(data);
    } catch (e) {
        log.error('Failed to load experiments:', e);
        $loader.innerHTML = `<p style="color:var(--md-sys-color-error)">Failed to load experiments. Please refresh.</p>`;
    }
}

function renderList(experiments) {
    $loader.classList.add('hidden');
    experiments.forEach((exp, i) => {
        const card = document.createElement('div');
        card.className = 'exp-card';
        card.style.animationDelay = `${i * 0.07}s`;
        card.setAttribute('data-exp-id', exp.id);

        const thumb = exp.thumbnail || `https://placehold.co/600x400/1a237e/ffffff?text=${encodeURIComponent(exp.id)}`;
        const desc  = exp.short_desc || (exp.narration_script ? exp.narration_script.substring(0, 90) + '…' : 'Tap to explore');

        card.innerHTML = `
            <img class="exp-card__img" src="${thumb}" alt="${escHtml(exp.apparatus)}" onerror="this.src='https://placehold.co/600x400/455a64/ffffff?text=MQC+Lab'">
            <div class="exp-card__body">
                <p class="exp-card__title">${escHtml(exp.apparatus)}</p>
                <p class="exp-card__sub">${escHtml(desc)}</p>
            </div>`;
        card.onclick = () => showDetails(exp.id);
        $list.appendChild(card);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Experiment detail
// ─────────────────────────────────────────────────────────────────────────────
async function showDetails(id) {
    currentExpId = id;
    chatHistory = [];

    $list.classList.add('hidden');
    $hero.classList.add('hidden');
    $details.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Reset tabs
    switchTab('overview');

    // Reset chat
    $chatMsgs.innerHTML = '';

    try {
        const exp = await apiFetch(`/api/experiments/${id}`);
        log.info('Loaded experiment:', id, exp.apparatus);

        // Header
        $title.textContent = exp.apparatus || id;
        $shortDesc.textContent = exp.short_desc || '';

        // Narration
        $narration.textContent = exp.narration_script || '';
        document.getElementById('narration-card').style.display = exp.narration_script ? '' : 'none';

        // Audio
        if (exp.audio_loc) {
            $audio.src = exp.audio_loc;
        } else {
            $audio.src = '';
        }

        // Carousel
        carouselImages = exp.images?.length > 0 ? exp.images : [`https://placehold.co/600x400/37474f/ffffff?text=${encodeURIComponent(exp.id)}`];
        carouselIndex = 0;
        buildCarousel();

        // Populate tabs
        populateOverview(exp);
        populateProcedure(exp);
        populateTheory(exp);
        populateKeyPoints(exp);

        // Chat greeting
        const apparatus = exp.apparatus || id;
        const shortName = apparatus.split('—')[0].trim().split('&')[0].trim();
        $greeting.textContent = `Here to help with ${shortName}!`;
        appendMessage('ai', `Hey there! 👋 I'm your MQC Lab guide for **${apparatus}**. Ask me about the theory, procedure, formulas — anything! I'm here to help you understand, not just recite text.`);

    } catch (e) {
        log.error('Failed to load detail for', id, e);
        $title.textContent = 'Failed to load experiment';
    }
}

function goBackToList() {
    $details.classList.add('hidden');
    $list.classList.remove('hidden');
    $hero.classList.remove('hidden');
    $audio.pause();
    currentExpId = null;
    chatHistory = [];
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab switching
// ─────────────────────────────────────────────────────────────────────────────
function switchTab(name) {
    ['overview','procedure','theory','keypoints'].forEach(t => {
        document.getElementById('tab-' + t)?.classList.toggle('active', t === name);
        document.getElementById('panel-' + t)?.classList.toggle('active', t === name);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab content population
// ─────────────────────────────────────────────────────────────────────────────
function populateOverview(exp) {
    // Objectives
    const $obj = document.getElementById('objectives-list');
    $obj.innerHTML = '';
    (exp.objectives || []).forEach(o => {
        const li = document.createElement('li');
        li.textContent = o;
        $obj.appendChild(li);
    });

    // Formulas
    const $fmls = document.getElementById('formula-grid');
    $fmls.innerHTML = '';
    (exp.formulas || []).forEach(f => {
        const chip = document.createElement('div');
        chip.className = 'formula-chip';
        chip.textContent = f;
        $fmls.appendChild(chip);
    });
}

function populateProcedure(exp) {
    const container = document.getElementById('procedure-content');
    container.innerHTML = '';
    const proc = exp.procedure || {};

    if (Array.isArray(proc)) {
        container.appendChild(buildStepList('Steps', proc));
    } else if (typeof proc === 'object' && Object.keys(proc).length > 0) {
        for (const [method, steps] of Object.entries(proc)) {
            container.appendChild(buildStepList(method, Array.isArray(steps) ? steps : [steps]));
        }
    } else {
        container.innerHTML = '<p style="color:var(--md-sys-color-on-surface-variant);font-size:.87rem">No procedure steps available.</p>';
    }
}

function buildStepList(title, steps) {
    const section = document.createElement('div');
    section.className = 'procedure-section';
    section.innerHTML = `<h4>${escHtml(title)}</h4>`;
    const ul = document.createElement('ol');
    ul.className = 'step-list';
    steps.forEach((step, i) => {
        const li = document.createElement('li');
        li.className = 'step-item';
        li.innerHTML = `<span class="step-num">${i + 1}</span><span>${escHtml(step)}</span>`;
        ul.appendChild(li);
    });
    section.appendChild(ul);
    return section;
}

function populateTheory(exp) {
    const container = document.getElementById('theory-content');
    container.innerHTML = '';
    const theory = exp.theory || {};

    if (typeof theory === 'object' && Object.keys(theory).length > 0) {
        for (const [key, val] of Object.entries(theory)) {
            const block = document.createElement('div');
            block.className = 'theory-block';
            block.innerHTML = `<h4>${escHtml(key)}</h4><p>${escHtml(String(val))}</p>`;
            container.appendChild(block);
        }
    } else if (typeof theory === 'string' && theory.trim()) {
        const block = document.createElement('div');
        block.className = 'theory-block';
        block.innerHTML = `<p>${escHtml(theory)}</p>`;
        container.appendChild(block);
    } else {
        container.innerHTML = '<p style="color:var(--md-sys-color-on-surface-variant);font-size:.87rem">No theory information available.</p>';
    }
}

function populateKeyPoints(exp) {
    const $kp = document.getElementById('keypoints-list');
    $kp.innerHTML = '';
    (exp.key_points || []).forEach(kp => {
        const li = document.createElement('li');
        li.className = 'key-point-item';
        li.innerHTML = `<span class="material-symbols-outlined">check_circle</span><span>${escHtml(kp)}</span>`;
        $kp.appendChild(li);
    });
    if (!(exp.key_points?.length)) {
        $kp.innerHTML = '<li style="color:var(--md-sys-color-on-surface-variant);font-size:.87rem">No key points listed.</li>';
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Carousel
// ─────────────────────────────────────────────────────────────────────────────
function buildCarousel() {
    $track.innerHTML = '';
    $dots.innerHTML = '';
    carouselImages.forEach((src, i) => {
        const img = document.createElement('img');
        img.src = src;
        img.alt = `Experiment image ${i + 1}`;
        img.onerror = () => { img.src = `https://placehold.co/600x400/455a64/ffffff?text=Image+${i+1}`; };
        $track.appendChild(img);

        const dot = document.createElement('button');
        dot.className = 'carousel__dot' + (i === 0 ? ' active' : '');
        dot.ariaLabel = `Image ${i + 1}`;
        dot.onclick = () => goToSlide(i);
        $dots.appendChild(dot);
    });
    $prevBtn.classList.toggle('hidden', carouselImages.length <= 1);
    $nextBtn.classList.toggle('hidden', carouselImages.length <= 1);
    updateCarousel();
}

function goToSlide(i) { carouselIndex = i; updateCarousel(); }
function updateCarousel() {
    $track.style.transform = `translateX(-${carouselIndex * 100}%)`;
    $dots.querySelectorAll('.carousel__dot').forEach((d, i) => d.classList.toggle('active', i === carouselIndex));
}
$prevBtn.onclick = () => { carouselIndex = (carouselIndex - 1 + carouselImages.length) % carouselImages.length; updateCarousel(); };
$nextBtn.onclick = () => { carouselIndex = (carouselIndex + 1) % carouselImages.length; updateCarousel(); };

// ─────────────────────────────────────────────────────────────────────────────
// Chat — with history
// ─────────────────────────────────────────────────────────────────────────────
async function sendMessage() {
    const text = $chatInput.value.trim();
    if (!text || !currentExpId) return;

    appendMessage('user', text);
    chatHistory.push({ role: 'user', content: text });
    $chatInput.value = '';

    const typing = appendMessage('ai typing', '●●● Thinking…');

    try {
        const data = await apiFetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: text,
                experiment_id: currentExpId,
                session_id: sessionId,
                history: chatHistory.slice(-10),  // last 5 turns
            }),
        });

        typing.remove();
        const reply = data.reply || 'No response received.';
        appendMessage('ai', reply);
        chatHistory.push({ role: 'assistant', content: reply });

    } catch (e) {
        typing.remove();
        log.error('Chat failed:', e);
        const msg = e.detail || 'Could not reach the assistant. Check your connection.';
        appendMessage('ai', '⚠️ ' + msg);
    }
}

function appendMessage(className, text) {
    const div = document.createElement('div');
    div.className = `message ${className}`;
    const p = document.createElement('p');
    // Render bold markdown (**text**) simply
    p.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    div.appendChild(p);
    $chatMsgs.appendChild(div);
    $chatMsgs.scrollTop = $chatMsgs.scrollHeight;
    return div;
}

$backBtn.onclick = goBackToList;
$sendBtn.onclick = sendMessage;
$chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });

// ─────────────────────────────────────────────────────────────────────────────
// URL query param (QR deep-link)
// ─────────────────────────────────────────────────────────────────────────────
function checkQueryParams() {
    const exp = new URLSearchParams(window.location.search).get('exp');
    if (exp) { log.info('QR deep-link:', exp); showDetails(exp); }
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility
// ─────────────────────────────────────────────────────────────────────────────
function escHtml(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─────────────────────────────────────────────────────────────────────────────
// Global error handlers
// ─────────────────────────────────────────────────────────────────────────────
window.onerror = (m, s, l, c, e) => log.error('Uncaught:', m, e);
window.onunhandledrejection = e => log.error('Unhandled rejection:', e.reason);

// ─────────────────────────────────────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────────────────────────────────────
fetchExperiments().then(checkQueryParams).catch(e => log.error('Init failed:', e));
