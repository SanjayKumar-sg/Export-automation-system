/**
 * validation.js — Email validation page: run validation, filter table.
 */

// ── Run Validation ────────────────────────────────────────────────────────
document.getElementById('btnValidateAll')?.addEventListener('click', async function () {
  const btn = this;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Validating…';

  const progress = document.getElementById('validationProgress');
  if (progress) progress.classList.remove('d-none');

  try {
    const result = await apiPost('/validation/run');

    if (result.status === 'complete') {
      const stats = result.stats;

      // Update stat cards
      Object.entries(stats).forEach(([key, val]) => {
        const el = document.getElementById('stat_' + key);
        if (el) el.textContent = val;
      });

      showToast(
        `Validation complete! Valid: ${stats.valid || 0}, Invalid: ${stats.invalid || 0}, Duplicates: ${stats.duplicate || 0}`,
        'success', 6000
      );
    }
  } catch (e) {
    showToast('Validation failed: ' + e.message, 'danger');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="bi bi-shield-check me-2"></i>Validate All';
    if (progress) progress.classList.add('d-none');
  }
});

// ── Status Filter Tabs ────────────────────────────────────────────────────
document.querySelectorAll('.status-filter-btn').forEach(btn => {
  btn.addEventListener('click', async function () {
    document.querySelectorAll('.status-filter-btn').forEach(b => b.classList.remove('active'));
    this.classList.add('active');

    const status = this.dataset.status;
    await loadBuyersByStatus(status);
  });
});

async function loadBuyersByStatus(status) {
  const tbody = document.getElementById('validationTableBody');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" class="text-center py-3"><span class="spinner-border spinner-border-sm"></span> Loading…</td></tr>';

  try {
    const url = status ? `/validation/buyers?status=${status}` : '/validation/buyers';
    const data = await apiGet(url);
    renderValidationTable(data.buyers || []);
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-danger text-center">Failed to load.</td></tr>';
  }
}

function renderValidationTable(buyers) {
  const tbody = document.getElementById('validationTableBody');
  if (!tbody) return;

  if (!buyers.length) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No buyers found for this status.</td></tr>';
    return;
  }

  tbody.innerHTML = buyers.map(b => `
    <tr>
      <td>${b.email}</td>
      <td>${b.company_name || '—'}</td>
      <td><span class="badge status-badge status-${b.email_status}">${b.email_status}</span></td>
      <td class="small text-muted">${b.validation_error || '—'}</td>
      <td>
        <button class="btn btn-ghost btn-sm revalidate-btn" data-id="${b.id}">
          <i class="bi bi-arrow-repeat text-info"></i>
        </button>
      </td>
    </tr>
  `).join('');

  // Attach revalidate handlers
  document.querySelectorAll('.revalidate-btn').forEach(btn => {
    btn.addEventListener('click', async function () {
      const id = this.dataset.id;
      const result = await apiPost(`/validation/revalidate/${id}`);
      showToast(`Re-validated: ${result.status}`, 'info');
      // Refresh current tab
      const activeBtn = document.querySelector('.status-filter-btn.active');
      if (activeBtn) loadBuyersByStatus(activeBtn.dataset.status);
    });
  });
}

// Load all on page init
loadBuyersByStatus('');
