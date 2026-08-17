/**
 * classification.js — AI classification page AJAX and progress polling.
 */

let classPoller = null;
let distChart   = null;

// ── Start Classification ──────────────────────────────────────────────────
document.getElementById('btnStartClassify')?.addEventListener('click', async function () {
  const batchSize = parseInt(document.getElementById('batchSize').value) || 20;

  document.getElementById('classifyIdle')?.classList.add('d-none');
  document.getElementById('classifyProgress')?.classList.remove('d-none');
  document.getElementById('classifyLog')?.classList.remove('d-none');

  try {
    await apiPost('/classification/start', { batch_size: batchSize });
    startClassifyPolling();
    this.disabled = true;
    this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Running…';
  } catch (e) {
    showToast('Failed to start classification', 'danger');
  }
});

function startClassifyPolling() {
  if (classPoller) clearInterval(classPoller);
  classPoller = setInterval(pollClassify, 2000);
}

function stopClassifyPolling() {
  if (classPoller) { clearInterval(classPoller); classPoller = null; }
}

async function pollClassify() {
  try {
    const state = await apiGet('/classification/status');
    const pct = state.total > 0 ? Math.round((state.progress / state.total) * 100) : 0;

    document.getElementById('classifyBar')?.setAttribute('style', `width:${pct}%`);
    document.getElementById('classifyPct') && (document.getElementById('classifyPct').textContent = pct + '%');
    document.getElementById('classifyLabel') && (document.getElementById('classifyLabel').textContent =
      `Classified ${state.progress} of ${state.total}…`);

    document.getElementById('cStatClassified') && (document.getElementById('cStatClassified').textContent = state.classified);
    document.getElementById('cStatFailed')    && (document.getElementById('cStatFailed').textContent    = state.failed);
    document.getElementById('cStatTokens')    && (document.getElementById('cStatTokens').textContent    = formatNumber(state.total_tokens));
    document.getElementById('totalTokens')    && (document.getElementById('totalTokens').textContent    = formatNumber(state.total_tokens));

    // Append log
    if (state.log?.length) {
      const logEl = document.getElementById('classifyLog');
      if (logEl && logEl.dataset.lastLen !== String(state.log.length)) {
        logEl.dataset.lastLen = String(state.log.length);
        logEl.innerHTML = '';
        state.log.forEach(msg => appendLog('classifyLog', msg));
      }
    }

    if (!state.running) {
      stopClassifyPolling();
      const btn = document.getElementById('btnStartClassify');
      if (btn) { btn.disabled = false; btn.innerHTML = '<i class="bi bi-stars me-2"></i>Run Classification'; }
      showToast(
        `Classification complete! Classified: ${state.classified}, Failed: ${state.failed}`,
        'success', 6000
      );
      loadDistChart();
    }
  } catch (e) {
    console.error('classify poll error', e);
  }
}

// ── Distribution Chart ────────────────────────────────────────────────────
async function loadDistChart() {
  try {
    const data = await apiGet('/classification/stats');
    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = ['#6366f1','#06b6d4','#10b981','#f59e0b','#8b5cf6','#ef4444','#ec4899','#94a3b8'];

    const ctx = document.getElementById('classDistChart')?.getContext('2d');
    if (!ctx) return;

    if (distChart) distChart.destroy();
    distChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Buyers',
          data: values,
          backgroundColor: colors.slice(0, labels.length),
          borderRadius: 8,
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
          y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        },
      },
    });
  } catch (e) {
    console.error('chart error', e);
  }
}

// Load chart on page init
loadDistChart();

// Resume polling if already running
(async () => {
  try {
    const state = await apiGet('/classification/status');
    if (state.running) {
      document.getElementById('classifyIdle')?.classList.add('d-none');
      document.getElementById('classifyProgress')?.classList.remove('d-none');
      document.getElementById('classifyLog')?.classList.remove('d-none');
      startClassifyPolling();
    }
  } catch {}
})();
