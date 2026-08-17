/**
 * reports.js — Reports page: chart rendering and report generation.
 */

function initReportCharts(stats) {
  // ── Success vs Failure Rate ──────────────────────────────────────────
  const srCtx = document.getElementById('successRateChart')?.getContext('2d');
  if (srCtx) {
    const sent   = stats.sent_today    || 0;
    const failed = stats.failed_today  || 0;
    new Chart(srCtx, {
      type: 'doughnut',
      data: {
        labels: ['Sent', 'Failed'],
        datasets: [{
          data: [sent, failed],
          backgroundColor: ['#10b981', '#ef4444'],
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true,
        cutout: '60%',
        plugins: {
          legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 12 } } },
        },
      },
    });
  }

  // ── Top Countries (Horizontal Bar) ───────────────────────────────────
  const ctyCtx = document.getElementById('topCountriesChart')?.getContext('2d');
  if (ctyCtx && stats.country_distribution) {
    const labels = Object.keys(stats.country_distribution).slice(0, 10);
    const values = Object.values(stats.country_distribution).slice(0, 10);
    new Chart(ctyCtx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Buyers',
          data: values,
          backgroundColor: 'rgba(99,102,241,0.7)',
          borderRadius: 6,
          borderWidth: 0,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: { grid: { display: false }, ticks: { color: '#94a3b8' } },
        },
      },
    });
  }
}

// ── Generate Buyers Report ────────────────────────────────────────────────
document.getElementById('btnGenBuyers')?.addEventListener('click', async function () {
  const fmt = document.getElementById('buyersFormat').value;
  this.disabled = true;
  this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating…';

  try {
    const result = await apiPost('/reports/generate/buyers', { format: fmt });
    if (result.status === 'ready') {
      window.location.href = `/reports/download/${result.report_id}`;
      showToast('Report generated!', 'success');
    }
  } catch (e) {
    showToast('Report generation failed', 'danger');
  } finally {
    this.disabled = false;
    this.innerHTML = '<i class="bi bi-download me-2"></i>Generate &amp; Download';
  }
});

// ── Generate Campaign Report ──────────────────────────────────────────────
document.getElementById('btnGenCampaign')?.addEventListener('click', async function () {
  const campaignId = document.getElementById('campaignSelect').value;
  if (!campaignId) { showToast('Select a campaign', 'warning'); return; }

  const fmt = document.getElementById('campaignFormat').value;
  this.disabled = true;
  this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Generating…';

  try {
    const result = await apiPost(`/reports/generate/campaign/${campaignId}`, { format: fmt });
    if (result.status === 'ready') {
      window.location.href = `/reports/download/${result.report_id}`;
      showToast('Report generated!', 'success');
    }
  } catch (e) {
    showToast('Report generation failed', 'danger');
  } finally {
    this.disabled = false;
    this.innerHTML = '<i class="bi bi-download me-2"></i>Generate &amp; Download';
  }
});

// ── Load campaigns into selector ──────────────────────────────────────────
(async () => {
  try {
    const data = await apiGet('/campaigns/api');
    const sel = document.getElementById('campaignSelect');
    if (sel && data.campaigns) {
      data.campaigns.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = `${c.name} (${c.status})`;
        sel.appendChild(opt);
      });
    }
  } catch {}
})();
