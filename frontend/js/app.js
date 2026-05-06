/* App — Main controller: routing, auth, initialization */
const App = {
  currentView: 'scanner',

  init() {
    // Check existing session
    const token = localStorage.getItem('campusgate_token');
    if (token) {
      authToken = token;
      this.showApp();
    } else {
      this.showLogin();
    }
    this.bindEvents();
  },

  bindEvents() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const guardId = document.getElementById('guard-id').value.trim();
      const password = document.getElementById('guard-password').value;
      const errEl = document.getElementById('login-error');
      const btn = document.getElementById('login-btn');
      btn.disabled = true; btn.querySelector('span').textContent = 'Signing in...';
      try {
        await api.login(guardId, password);
        errEl.classList.add('hidden');
        this.showApp();
      } catch (err) {
        errEl.textContent = 'Invalid credentials. Try GUARD001 / guard123';
        errEl.classList.remove('hidden');
      } finally {
        btn.disabled = false; btn.querySelector('span').textContent = 'Sign In';
      }
    });

    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchView(link.dataset.view);
      });
    });

    // Logout
    document.getElementById('logout-btn').addEventListener('click', () => this.logout());

    // Manual override toggle
    document.getElementById('manual-toggle').addEventListener('change', (e) => {
      document.getElementById('manual-direction').classList.toggle('hidden', !e.target.checked);
    });

    // Dashboard refresh
    document.getElementById('refresh-dashboard-btn').addEventListener('click', () => Dashboard.loadAll());

    // Student search
    let searchTimeout;
    document.getElementById('student-search').addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(() => Dashboard.loadStudents(e.target.value), 400);
    });
  },

  showLogin() {
    document.getElementById('login-screen').classList.add('active');
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app-screen').classList.add('hidden');
    document.getElementById('app-screen').classList.remove('active');
  },

  showApp() {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('login-screen').classList.remove('active');
    document.getElementById('app-screen').classList.remove('hidden');
    document.getElementById('app-screen').classList.add('active');

    // Set guard info
    const guard = JSON.parse(localStorage.getItem('campusgate_guard') || '{}');
    document.getElementById('guard-name-display').textContent = guard.name || 'Guard';
    document.getElementById('guard-gate-display').textContent = guard.gate || 'Main Gate';
    document.getElementById('guard-avatar').textContent = (guard.name || 'G')[0];

    // Init scanner + load data
    Scanner.init();
    Dashboard.loadAll();
    this.switchView('scanner');

    // Auto-refresh every 30s
    this._refreshInterval = setInterval(() => {
      if (this.currentView === 'dashboard') Dashboard.loadAll();
      if (this.currentView === 'alerts') Dashboard.loadAlerts();
    }, 30000);
  },

  switchView(viewName) {
    this.currentView = viewName;
    // Hide all views
    document.querySelectorAll('.view').forEach(v => { v.classList.remove('active'); v.classList.add('hidden'); });
    // Show target
    const target = document.getElementById('view-' + viewName);
    if (target) { target.classList.add('active'); target.classList.remove('hidden'); }
    // Update nav
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector(`.nav-link[data-view="${viewName}"]`)?.classList.add('active');
    // Load view data
    if (viewName === 'dashboard') Dashboard.loadAll();
    if (viewName === 'alerts') Dashboard.loadAlerts();
    if (viewName === 'students') Dashboard.loadStudents();
  },

  logout() {
    api.logout();
    Scanner.stop();
    clearInterval(this._refreshInterval);
    this.showLogin();
    this.showToast('Logged out', 'success');
  },

  showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }
};

document.addEventListener('DOMContentLoaded', () => App.init());
