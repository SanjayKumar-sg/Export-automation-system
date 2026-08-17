/**
 * search.js — Buyer search page AJAX with progress polling.
 */

let searchPoller = null;

// ── Start Search ─────────────────────────────────────────────────────────
document.getElementById('btnStart')?.addEventListener('click', async function () {
  const keyword    = document.getElementById('searchKeyword').value.trim();
  const maxResults = parseInt(document.getElementById('maxResults').value) || 100;
  const sources    = [...document.querySelectorAll('.source-check:checked')].map(c => c.value);

  if (!keyword) { showToast('Please enter a keyword', 'warning'); return; }
  if (!sources.length) { showToast('Select at least one source', 'warning'); return; }

  clearLog('searchLog');
  appendLog('searchLog', `Starting search for "${keyword}" across: ${sources.join(', ')}`);

  setSearchButtons('running');

  try {
    await apiPost('/search/start', { keyword, max_results: maxResults, sources });
    startPolling();
  } catch (e) {
    showToast('Failed to start search', 'danger');
    setSearchButtons('idle');
  }
});

// ── Pause ─────────────────────────────────────────────────────────────────
document.getElementById('btnPause')?.addEventListener('click', async () => {
  await apiPost('/search/pause');
  showToast('Search paused', 'warning');
});

// ── Resume ────────────────────────────────────────────────────────────────
document.getElementById('btnResume')?.addEventListener('click', async () => {
  await apiPost('/search/resume');
  showToast('Search resumed', 'info');
});

// ── Cancel ────────────────────────────────────────────────────────────────
document.getElementById('btnCancel')?.addEventListener('click', async () => {
  await apiPost('/search/cancel');
  stopPolling();
  setSearchButtons('idle');
  showToast('Search cancelled', 'danger');
});

// ── Polling ───────────────────────────────────────────────────────────────
function startPolling() {
  if (searchPoller) clearInterval(searchPoller);
  searchPoller = setInterval(pollStatus, 1500);
}

function stopPolling() {
  if (searchPoller) { clearInterval(searchPoller); searchPoller = null; }
}

async function pollStatus() {
  try {
    const state = await apiGet('/search/status');

    // Update progress bar
    const pct = state.total > 0 ? Math.round((state.progress / state.total) * 100) : 0;
    const bar  = document.getElementById('progressBar');
    const pctEl = document.getElementById('progressPct');
    const label = document.getElementById('progressLabel');
    if (bar) bar.style.width = pct + '%';
    if (pctEl) pctEl.textContent = pct + '%';
    if (label) label.textContent = state.current_source
      ? `Searching ${state.current_source}…` : 'Processing…';

    // Update stats
    setText('statFound', state.found);
    setText('statSaved', state.saved);
    setText('statSource', state.current_source || '—');

    // Append new log messages
    if (state.log?.length) {
      const logEl = document.getElementById('searchLog');
      if (logEl && logEl.dataset.lastLen !== String(state.log.length)) {
        logEl.dataset.lastLen = String(state.log.length);
        logEl.innerHTML = '';
        state.log.forEach(msg => appendLog('searchLog', msg));
      }
    }

    if (!state.running) {
      stopPolling();
      setSearchButtons('idle');
      const bar2 = document.getElementById('progressBar');
      if (bar2) { bar2.style.width = '100%'; bar2.classList.remove('progress-bar-animated'); }
      showToast(`Search complete! Saved ${state.saved} new buyers.`, 'success', 6000);
    }
  } catch (e) {
    console.error('Poll error:', e);
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function clearLog(id) {
  const el = document.getElementById(id);
  if (el) { el.innerHTML = ''; delete el.dataset.lastLen; }
}

function setSearchButtons(state) {
  const btnStart  = document.getElementById('btnStart');
  const btnPause  = document.getElementById('btnPause');
  const btnResume = document.getElementById('btnResume');
  const btnCancel = document.getElementById('btnCancel');

  if (state === 'running') {
    btnStart?.classList.add('d-none');
    btnPause?.classList.remove('d-none');
    btnCancel?.classList.remove('d-none');
    btnResume?.classList.add('d-none');
  } else {
    btnStart?.classList.remove('d-none');
    btnPause?.classList.add('d-none');
    btnResume?.classList.add('d-none');
    btnCancel?.classList.add('d-none');
  }
}

// Check if a search is already running on page load
(async () => {
  try {
    const state = await apiGet('/search/status');
    if (state.running) { setSearchButtons('running'); startPolling(); }
  } catch {}
})();
