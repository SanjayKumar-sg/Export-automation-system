/**
 * send.js — Campaign send monitor: start/pause/resume/stop + progress polling.
 */

let sendPoller = null;

// ── Start Campaign ────────────────────────────────────────────────────────
document.getElementById('btnStartCampaign')?.addEventListener('click', async function () {
  const campaignId = document.getElementById('campaignSelect')?.value;
  if (!campaignId) { showToast('Please select a campaign', 'warning'); return; }

  this.disabled = true;
  const logEl = document.getElementById('sendLog');
  if (logEl) logEl.innerHTML = '';
  appendLog('sendLog', 'Starting campaign…');

  try {
    await apiPost(`/send/start/${campaignId}`);
    setControls('running');
    startSendPolling();
  } catch (e) {
    showToast('Failed to start campaign', 'danger');
    this.disabled = false;
  }
});

// ── Pause ─────────────────────────────────────────────────────────────────
document.getElementById('btnPauseSend')?.addEventListener('click', async () => {
  await apiPost('/send/pause');
  showToast('Campaign paused', 'warning');
  appendLog('sendLog', '⏸ Campaign paused');
});

// ── Resume ────────────────────────────────────────────────────────────────
document.getElementById('btnResumeSend')?.addEventListener('click', async () => {
  await apiPost('/send/resume');
  showToast('Campaign resumed', 'info');
  appendLog('sendLog', '▶ Campaign resumed');
});

// ── Stop ──────────────────────────────────────────────────────────────────
document.getElementById('btnStopSend')?.addEventListener('click', async () => {
  if (!confirm('Stop the campaign?')) return;
  await apiPost('/send/stop');
  stopSendPolling();
  setControls('idle');
  showToast('Campaign stopped', 'danger');
  appendLog('sendLog', '■ Campaign stopped by user');
});

// ── Polling ───────────────────────────────────────────────────────────────
function startSendPolling() {
  if (sendPoller) clearInterval(sendPoller);
  sendPoller = setInterval(pollSend, 2000);
}

function stopSendPolling() {
  if (sendPoller) { clearInterval(sendPoller); sendPoller = null; }
}

async function pollSend() {
  try {
    const state = await apiGet('/send/status');

    const total = state.total || 0;
    const sent  = state.sent  || 0;
    const pct   = total > 0 ? Math.round((state.progress / total) * 100) : 0;

    // Progress bar
    document.getElementById('sendProgressBar')?.setAttribute('style', `width:${pct}%`);
    document.getElementById('sendProgressPct') && (document.getElementById('sendProgressPct').textContent = pct + '%');
    document.getElementById('sendProgressLabel') &&
      (document.getElementById('sendProgressLabel').textContent = `Sending ${state.progress} of ${total}…`);
    document.getElementById('sendETA') && state.estimated_remaining &&
      (document.getElementById('sendETA').textContent = `Estimated: ${state.estimated_remaining} remaining`);

    // Stats
    setText('sTotal', total);
    setText('sSent', state.sent);
    setText('sFailed', state.failed);
    setText('sCurrentRecipient', state.current_recipient || '—');

    // SMTP indicator
    const dot = document.getElementById('smtpDot');
    const stText = document.getElementById('smtpStatus');
    if (dot && stText) {
      if (state.smtp_connected) {
        dot.style.background = '#10b981';
        stText.textContent = 'Connected';
      } else {
        dot.style.background = '#ef4444';
        stText.textContent = 'Disconnected';
      }
    }

    // Log
    if (state.log?.length) {
      const logEl = document.getElementById('sendLog');
      if (logEl && logEl.dataset.lastLen !== String(state.log.length)) {
        logEl.dataset.lastLen = String(state.log.length);
        logEl.innerHTML = '';
        state.log.forEach(msg => {
          const type = msg.startsWith('✗') ? 'error' : msg.startsWith('✓') ? 'info' : 'info';
          appendLog('sendLog', msg, type);
        });
      }
    }

    if (!state.running) {
      stopSendPolling();
      setControls('idle');
      const pctComplete = total > 0 ? Math.round((sent / total) * 100) : 0;
      showToast(
        `Campaign finished! Sent: ${state.sent} | Failed: ${state.failed}`,
        'success', 8000
      );
    }
  } catch (e) {
    console.error('Send poll error:', e);
  }
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '—';
}

function setControls(state) {
  const start  = document.getElementById('btnStartCampaign');
  const pause  = document.getElementById('btnPauseSend');
  const resume = document.getElementById('btnResumeSend');
  const stop   = document.getElementById('btnStopSend');

  if (state === 'running') {
    start?.classList.add('d-none');
    pause?.classList.remove('d-none');
    stop?.classList.remove('d-none');
    resume?.classList.add('d-none');
  } else {
    if (start) { start.classList.remove('d-none'); start.disabled = false; }
    pause?.classList.add('d-none');
    resume?.classList.add('d-none');
    stop?.classList.add('d-none');
  }
}

// Resume monitoring on page load
(async () => {
  try {
    const state = await apiGet('/send/status');
    if (state.running) { setControls('running'); startSendPolling(); }
  } catch {}
})();
