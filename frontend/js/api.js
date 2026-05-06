/* API Client — Handles all backend communication */
const API_BASE = window.location.origin + '/api';
let authToken = localStorage.getItem('campusgate_token') || null;

const api = {
  _headers() {
    const h = { 'Content-Type': 'application/json' };
    if (authToken) h['Authorization'] = `Bearer ${authToken}`;
    return h;
  },
  async post(url, body) {
    const r = await fetch(API_BASE + url, { method: 'POST', headers: this._headers(), body: JSON.stringify(body) });
    if (!r.ok && r.status === 401) { App.logout(); throw new Error('Session expired'); }
    return r.json();
  },
  async get(url) {
    const r = await fetch(API_BASE + url, { headers: this._headers() });
    if (!r.ok && r.status === 401) { App.logout(); throw new Error('Session expired'); }
    return r.json();
  },
  async login(guardId, password) {
    const data = await this.post('/auth/login', { guard_id: guardId, password });
    authToken = data.access_token;
    localStorage.setItem('campusgate_token', authToken);
    localStorage.setItem('campusgate_guard', JSON.stringify({ name: data.guard_name, gate: data.gate }));
    return data;
  },
  logout() {
    authToken = null;
    localStorage.removeItem('campusgate_token');
    localStorage.removeItem('campusgate_guard');
  },
  scan(rollNo, guardId, manualDir) {
    return this.post('/scan', { roll_no: rollNo, guard_id: guardId, manual_direction: manualDir || null });
  },
  getStats() { return this.get('/admin/stats'); },
  getCensus() { return this.get('/admin/census'); },
  getLateAlerts() { return this.get('/admin/late-alerts'); },
  getRecentScans(limit = 15) { return this.get(`/admin/recent-scans?limit=${limit}`); },
  getHourlyAnalytics() { return this.get('/admin/analytics/hourly'); },
  getStudents(params = '') { return this.get(`/students/${params}`); },
  searchStudents(q) { return this.get(`/students/?search=${encodeURIComponent(q)}`); },
};
