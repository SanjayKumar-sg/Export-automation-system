/**
 * buyers.js — Buyer database: row selection, bulk delete, inline delete.
 */

// ── Select All ────────────────────────────────────────────────────────────
const selectAll = document.getElementById('selectAll');
if (selectAll) {
  selectAll.addEventListener('change', function () {
    document.querySelectorAll('.row-check').forEach(cb => cb.checked = this.checked);
    updateBulkBtn();
  });
}

document.querySelectorAll('.row-check').forEach(cb => {
  cb.addEventListener('change', updateBulkBtn);
});

function updateBulkBtn() {
  const selected = document.querySelectorAll('.row-check:checked').length;
  const btn = document.getElementById('btnBulkDelete');
  const cnt = document.getElementById('selectedCount');
  if (btn) btn.disabled = selected === 0;
  if (cnt) cnt.textContent = selected;
}

// ── Bulk Delete ───────────────────────────────────────────────────────────
document.getElementById('btnBulkDelete')?.addEventListener('click', async function () {
  const ids = [...document.querySelectorAll('.row-check:checked')].map(c => parseInt(c.value));
  if (!ids.length) return;
  if (!confirm(`Delete ${ids.length} buyer(s)?`)) return;

  try {
    await apiPost('/buyers/bulk-delete', { ids });
    ids.forEach(id => {
      const row = document.querySelector(`tr[data-id="${id}"]`);
      if (row) row.remove();
    });
    showToast(`Deleted ${ids.length} buyers`, 'success');
    updateBulkBtn();
  } catch (e) {
    showToast('Bulk delete failed', 'danger');
  }
});

// ── Inline Delete ─────────────────────────────────────────────────────────
document.querySelectorAll('.btn-delete').forEach(btn => {
  btn.addEventListener('click', async function () {
    const id = this.dataset.id;
    if (!confirm('Delete this buyer?')) return;

    try {
      await apiPost(`/buyers/${id}/delete`);
      this.closest('tr').remove();
      showToast('Buyer deleted', 'success');
    } catch (e) {
      showToast('Delete failed', 'danger');
    }
  });
});
