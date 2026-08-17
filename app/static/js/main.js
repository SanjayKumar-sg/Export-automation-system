/**
 * main.js — Shared utilities used by all pages.
 * Handles: sidebar toggle, dark/light theme, CSRF, toast messages.
 */

// ── CSRF Token ────────────────────────────────────────────────────────────
function getCsrfToken() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// ── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const id = 'toast_' + Date.now();
  const icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill',
                  warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };
  const icon = icons[type] || icons.info;

  const html = `
    <div id="${id}" class="toast align-items-center text-bg-${type} border-0 show" role="alert">
      <div class="d-flex">
        <div class="toast-body">
          <i class="bi ${icon} me-2"></i>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>`;

  container.insertAdjacentHTML('beforeend', html);
  const toastEl = document.getElementById(id);
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 300);
  }, duration);
}

// ── Sidebar Toggle ────────────────────────────────────────────────────────
const sidebarEl   = document.getElementById('sidebar');
const mainWrapper = document.getElementById('mainWrapper');
const toggleBtn   = document.getElementById('sidebarToggle');

if (toggleBtn && sidebarEl) {
  toggleBtn.addEventListener('click', () => {
    const isMobile = window.innerWidth < 769;
    if (isMobile) {
      sidebarEl.classList.toggle('mobile-open');
    } else {
      sidebarEl.classList.toggle('collapsed');
      mainWrapper.classList.toggle('expanded');
      localStorage.setItem('sidebarCollapsed', sidebarEl.classList.contains('collapsed'));
    }
  });

  // Restore sidebar state
  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebarEl.classList.add('collapsed');
    mainWrapper.classList.add('expanded');
  }

  // Close sidebar on mobile overlay click
  document.addEventListener('click', (e) => {
    if (window.innerWidth < 769 &&
        sidebarEl.classList.contains('mobile-open') &&
        !sidebarEl.contains(e.target) &&
        !toggleBtn.contains(e.target)) {
      sidebarEl.classList.remove('mobile-open');
    }
  });
}

// ── Dark / Light Theme Toggle ─────────────────────────────────────────────
const themeToggle = document.getElementById('themeToggle');
const htmlEl = document.documentElement;

function setTheme(theme) {
  htmlEl.setAttribute('data-bs-theme', theme);
  localStorage.setItem('theme', theme);
  const icon = document.getElementById('themeToggle')?.querySelector('i');
  if (icon) {
    icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
  }
}

// Init theme from localStorage or default dark
setTheme(localStorage.getItem('theme') || 'dark');

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const current = htmlEl.getAttribute('data-bs-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
  });
}

// ── AJAX Helper ───────────────────────────────────────────────────────────
async function apiPost(url, data = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(data),
  });
  return res.json();
}

async function apiGet(url) {
  const res = await fetch(url);
  return res.json();
}

// ── Format Numbers ────────────────────────────────────────────────────────
function formatNumber(n) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

// ── Append Log Entry ──────────────────────────────────────────────────────
function appendLog(containerId, message, type = 'info') {
  const container = document.getElementById(containerId);
  if (!container) return;
  const ts = new Date().toLocaleTimeString();
  const cls = type === 'error' ? 'log-error' : type === 'warn' ? 'log-warn' : 'log-info';
  const entry = document.createElement('div');
  entry.className = `log-entry ${cls}`;
  entry.textContent = `[${ts}] ${message}`;
  container.appendChild(entry);
  container.scrollTop = container.scrollHeight;
}

// ── Insert Token into Textarea ────────────────────────────────────────────
function insertToken(token) {
  const ta = document.getElementById('emailBody') || document.getElementById('tplBody');
  if (!ta) return;
  const start = ta.selectionStart;
  const end = ta.selectionEnd;
  ta.value = ta.value.slice(0, start) + token + ta.value.slice(end);
  ta.selectionStart = ta.selectionEnd = start + token.length;
  ta.focus();
}
