/**
 * campaign.js — Campaign builder: save, preview, template load, test send.
 */

// ── Save Campaign ─────────────────────────────────────────────────────────
document.getElementById('btnSaveCampaign')?.addEventListener('click', async function () {
  const data = buildCampaignPayload();
  if (!data.name) { showToast('Campaign name is required', 'warning'); return; }
  if (!data.subject) { showToast('Email subject is required', 'warning'); return; }
  if (!data.body_html) { showToast('Email body is required', 'warning'); return; }

  this.disabled = true;
  this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Saving…';

  try {
    const result = await apiPost('/campaigns/save', data);
    if (result.status === 'saved') {
      showToast('Campaign saved!', 'success');
      document.getElementById('campaignId').value = result.campaign_id;
      window.history.replaceState(null, '', '/campaigns/builder/' + result.campaign_id);
    }
  } catch (e) {
    showToast('Save failed', 'danger');
  } finally {
    this.disabled = false;
    this.innerHTML = '<i class="bi bi-floppy me-1"></i>Save Campaign';
  }
});

function buildCampaignPayload() {
  return {
    campaign_id: document.getElementById('campaignId')?.value || '',
    name: document.getElementById('campaignName')?.value?.trim() || '',
    subject: document.getElementById('emailSubject')?.value?.trim() || '',
    body_html: document.getElementById('emailBody')?.value || '',
    audience: document.getElementById('campaignAudience')?.value || 'all',
    cc: document.getElementById('emailCc')?.value || '',
    bcc: document.getElementById('emailBcc')?.value || '',
    daily_limit: parseInt(document.getElementById('dailyLimit')?.value) || 200,
    delay_seconds: parseInt(document.getElementById('delaySeconds')?.value) || 3,
    attachment_id: document.getElementById('attachmentSelect')?.value || '',
    template_id: document.getElementById('templateSelect')?.value || '',
  };
}

// ── Preview Email ─────────────────────────────────────────────────────────
document.getElementById('btnPreview')?.addEventListener('click', function () {
  const subject = document.getElementById('emailSubject')?.value || '';
  const body = document.getElementById('emailBody')?.value || '';

  document.getElementById('previewSubject').textContent = subject;
  const frame = document.getElementById('previewFrame');
  frame.srcdoc = body;

  const modal = new bootstrap.Modal(document.getElementById('previewModal'));
  modal.show();
});

// ── HTML / Preview toggle ─────────────────────────────────────────────────
document.getElementById('btnHtmlMode')?.addEventListener('click', function () {
  this.classList.add('active');
  document.getElementById('btnPreviewMode').classList.remove('active');
  document.getElementById('emailBody').classList.remove('d-none');
  document.getElementById('emailBodyPreview').classList.add('d-none');
});

document.getElementById('btnPreviewMode')?.addEventListener('click', function () {
  this.classList.add('active');
  document.getElementById('btnHtmlMode').classList.remove('active');
  const body = document.getElementById('emailBody').value;
  const preview = document.getElementById('emailBodyPreview');
  preview.innerHTML = body;
  document.getElementById('emailBody').classList.add('d-none');
  preview.classList.remove('d-none');
});

// ── Load Template ─────────────────────────────────────────────────────────
document.getElementById('btnLoadTemplate')?.addEventListener('click', function () {
  const sel = document.getElementById('templateSelect');
  const opt = sel?.selectedOptions[0];
  if (!opt || !opt.value) { showToast('Select a template first', 'warning'); return; }

  document.getElementById('emailSubject').value = opt.dataset.subject || '';
  document.getElementById('emailBody').value    = opt.dataset.body || '';
  showToast('Template loaded', 'success');
});

// ── Send Test Email ───────────────────────────────────────────────────────
document.getElementById('btnSendTest')?.addEventListener('click', async function () {
  const to = document.getElementById('testEmailTo')?.value?.trim();
  if (!to) { showToast('Enter a test email address', 'warning'); return; }

  this.disabled = true;
  this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Sending…';
  const resultEl = document.getElementById('testEmailResult');

  try {
    const result = await apiPost('/send/test', {
      to_email: to,
      subject: document.getElementById('emailSubject')?.value || 'Test Email',
      body: document.getElementById('emailBody')?.value || '<p>Test</p>',
      attachment_id: document.getElementById('attachmentSelect')?.value || '',
    });

    const ok = result.status === 'sent';
    resultEl.innerHTML = `<div class="alert alert-${ok ? 'success' : 'danger'} py-1 small mt-2">${result.message}</div>`;
  } catch (e) {
    resultEl.innerHTML = '<div class="alert alert-danger py-1 small mt-2">Failed to send test email</div>';
  } finally {
    this.disabled = false;
    this.innerHTML = '<i class="bi bi-send me-2"></i>Send Test';
  }
});
