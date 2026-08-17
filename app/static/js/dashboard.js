/**
 * dashboard.js — Dashboard charts and live stats refresh.
 */

function initDashboardCharts(stats) {
  const chartDefaults = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { size: 12, family: 'Inter' } } },
      tooltip: { backgroundColor: '#1e293b', titleColor: '#f1f5f9', bodyColor: '#94a3b8' },
    },
    scales: {
      x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { size: 11 } } },
    },
  };

  // ── Daily Sends (Line Chart) ─────────────────────────────────────────
  const dailyCtx = document.getElementById('dailySendsChart')?.getContext('2d');
  if (dailyCtx && stats.daily_sends) {
    const labels = stats.daily_sends.map(d => d.date);
    const counts = stats.daily_sends.map(d => d.count);
    new Chart(dailyCtx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Emails Sent',
          data: counts,
          fill: true,
          backgroundColor: 'rgba(99,102,241,0.15)',
          borderColor: '#6366f1',
          borderWidth: 2,
          tension: 0.4,
          pointBackgroundColor: '#6366f1',
          pointRadius: 4,
        }],
      },
      options: { ...chartDefaults },
    });
  }

  // ── Source Distribution (Doughnut) ───────────────────────────────────
  const srcCtx = document.getElementById('sourceChart')?.getContext('2d');
  if (srcCtx && stats.source_distribution) {
    const srcLabels = Object.keys(stats.source_distribution);
    const srcData   = Object.values(stats.source_distribution);
    const srcColors = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];
    new Chart(srcCtx, {
      type: 'doughnut',
      data: {
        labels: srcLabels,
        datasets: [{ data: srcData, backgroundColor: srcColors, borderWidth: 0 }],
      },
      options: {
        responsive: true, maintainAspectRatio: true,
        plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } } },
        cutout: '65%',
      },
    });
  }

  // ── Classification Distribution (Bar) ───────────────────────────────
  const classCtx = document.getElementById('classChart')?.getContext('2d');
  if (classCtx && stats.classification_distribution) {
    const classLabels = Object.keys(stats.classification_distribution);
    const classData   = Object.values(stats.classification_distribution);
    new Chart(classCtx, {
      type: 'bar',
      data: {
        labels: classLabels,
        datasets: [{
          label: 'Buyers',
          data: classData,
          backgroundColor: [
            'rgba(99,102,241,0.7)', 'rgba(6,182,212,0.7)', 'rgba(16,185,129,0.7)',
            'rgba(245,158,11,0.7)', 'rgba(139,92,246,0.7)', 'rgba(239,68,68,0.7)',
          ],
          borderRadius: 6,
          borderWidth: 0,
        }],
      },
      options: { ...chartDefaults, plugins: { legend: { display: false } } },
    });
  }

  // ── Country Distribution (Horizontal Bar) ───────────────────────────
  const countryCtx = document.getElementById('countryChart')?.getContext('2d');
  if (countryCtx && stats.country_distribution) {
    const countryLabels = Object.keys(stats.country_distribution);
    const countryData   = Object.values(stats.country_distribution);
    new Chart(countryCtx, {
      type: 'bar',
      data: {
        labels: countryLabels,
        datasets: [{
          label: 'Buyers',
          data: countryData,
          backgroundColor: 'rgba(6,182,212,0.7)',
          borderRadius: 6,
          borderWidth: 0,
        }],
      },
      options: {
        ...chartDefaults,
        indexAxis: 'y',
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: { grid: { display: false }, ticks: { color: '#94a3b8' } },
        },
      },
    });
  }
}

// ── Live Stats Refresh ────────────────────────────────────────────────────
document.getElementById('refreshStats')?.addEventListener('click', async function () {
  const btn = this;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Refreshing…';
  btn.disabled = true;

  try {
    const stats = await apiGet('/api/dashboard/stats');

    const update = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = formatNumber(val);
    };

    update('totalBuyers', stats.total_buyers);
    update('businessEmails', stats.business_emails);
    update('individualEmails', stats.individual_emails);
    update('sentToday', stats.sent_today);
    update('failedToday', stats.failed_today);
    update('pending', stats.pending);

    showToast('Dashboard stats refreshed!', 'success');
  } catch (e) {
    showToast('Failed to refresh stats', 'danger');
  } finally {
    btn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i>Refresh';
    btn.disabled = false;
  }
});
