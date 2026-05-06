/* Dashboard Module — Stats, Census, Charts, Alerts */
const Dashboard = {
  async loadStats() {
    try {
      const data = await api.getStats();
      document.getElementById('stats-grid').innerHTML = `
        <div class="stat-card"><div class="stat-label">Total Students</div><div class="stat-value accent">${data.total_students}</div></div>
        <div class="stat-card"><div class="stat-label">On Campus</div><div class="stat-value success">${data.on_campus}</div></div>
        <div class="stat-card"><div class="stat-label">Off Campus</div><div class="stat-value warning">${data.off_campus}</div></div>
        <div class="stat-card"><div class="stat-label">Late Alerts</div><div class="stat-value danger">${data.late_alerts}</div><div class="stat-trend">ML-predicted anomalies</div></div>
        <div class="stat-card"><div class="stat-label">Scans Today</div><div class="stat-value accent">${data.scans_today}</div></div>
        <div class="stat-card"><div class="stat-label">Curfew Violations</div><div class="stat-value danger">${data.curfew_violations_today}</div><div class="stat-trend">Today</div></div>`;
      // Update alert badge
      const badge = document.getElementById('alert-badge');
      if (data.late_alerts > 0) { badge.textContent = data.late_alerts; badge.classList.remove('hidden'); }
      else { badge.classList.add('hidden'); }
    } catch (e) { console.error('Stats load failed:', e); }
  },

  async loadCensus() {
    try {
      const data = await api.getCensus();
      const container = document.getElementById('census-table-container');
      if (!data.students_out || data.students_out.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:2rem">All students are on campus ✅</p>';
        return;
      }
      let rows = data.students_out.map(s => {
        const hours = s.hours_out ? s.hours_out.toFixed(1) : '—';
        const cls = s.hours_out > 24 ? 'color:var(--danger);font-weight:700' : (s.hours_out > 8 ? 'color:var(--warning)' : '');
        return `<tr><td>${s.roll_no}</td><td>${s.name}</td><td>${s.course}</td><td>${s.hostel}</td><td style="${cls}">${hours}h</td></tr>`;
      }).join('');
      container.innerHTML = `<table><thead><tr><th>Roll No</th><th>Name</th><th>Course</th><th>Hostel</th><th>Hours Out</th></tr></thead><tbody>${rows}</tbody></table>`;
    } catch (e) { console.error('Census load failed:', e); }
  },

  async loadChart() {
    try {
      const data = await api.getHourlyAnalytics();
      const maxVal = Math.max(...data.entries, ...data.exits, 1);
      const canvas = document.getElementById('hourly-chart');
      const container = canvas.parentElement;
      // Replace canvas with custom bars (no chart library needed)
      const chartHtml = `
        <div class="chart-bars">${data.hours.map((h, i) =>
          `<div class="chart-bar entries" style="height:${Math.max((data.entries[i]/maxVal)*100, 2)}%" title="Hour ${h}: ${data.entries[i]} entries"></div>` +
          `<div class="chart-bar exits" style="height:${Math.max((data.exits[i]/maxVal)*100, 2)}%" title="Hour ${h}: ${data.exits[i]} exits"></div>`
        ).join('')}</div>
        <div class="chart-labels">${data.hours.filter((_,i)=>i%3===0).map(h => `<span>${h}:00</span>`).join('')}</div>
        <div class="chart-legend">
          <div class="chart-legend-item"><div class="chart-legend-dot" style="background:var(--success)"></div> Entries</div>
          <div class="chart-legend-item"><div class="chart-legend-dot" style="background:var(--warning)"></div> Exits</div>
        </div>`;
      canvas.style.display = 'none';
      let chartDiv = container.querySelector('.chart-custom');
      if (!chartDiv) { chartDiv = document.createElement('div'); chartDiv.className = 'chart-custom'; container.appendChild(chartDiv); }
      chartDiv.innerHTML = chartHtml;
    } catch (e) { console.error('Chart load failed:', e); }
  },

  async loadAlerts() {
    try {
      const data = await api.getLateAlerts();
      const container = document.getElementById('alerts-container');
      if (!data.alerts || data.alerts.length === 0) {
        container.innerHTML = '<div class="no-alerts"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><p>No late-stay alerts — all students within predicted windows</p></div>';
        return;
      }
      container.innerHTML = data.alerts.map(a => {
        const sev = a.severity === 'CRITICAL' ? 'critical' : 'warning';
        return `<div class="alert-card ${sev}">
          <div class="alert-severity severity-${sev}">${a.severity}</div>
          <div class="alert-info">
            <div class="alert-name">${a.name} <span style="color:var(--text-muted);font-weight:400;font-size:0.82rem">${a.roll_no}</span></div>
            <div class="alert-details">${a.course || a.department} • ${a.hostel} • Exit: ${new Date(a.exit_time).toLocaleString()}</div>
          </div>
          <div style="text-align:right">
            <div class="alert-hours">${a.hours_overdue.toFixed(1)}h</div>
            <div class="alert-hours-label">overdue</div>
          </div>
          <button class="btn btn-sm btn-ghost" onclick="alert('📞 Warden: ${a.warden_contact}')">📞</button>
        </div>`;
      }).join('');
    } catch (e) { console.error('Alerts load failed:', e); }
  },

  async loadRecentScans() {
    try {
      const data = await api.getRecentScans(10);
      const container = document.getElementById('recent-scans-list');
      if (!data.scans || data.scans.length === 0) {
        container.innerHTML = '<p style="color:var(--text-muted);padding:1rem;text-align:center">No recent scans</p>';
        return;
      }
      container.innerHTML = data.scans.map(s => {
        const time = new Date(s.timestamp).toLocaleTimeString();
        const flags = (s.is_late ? '<span class="flag flag-late">LATE</span>' : '') +
                      (s.is_curfew_violation ? '<span class="flag flag-curfew">CURFEW</span>' : '');
        return `<div class="scan-item">
          <span class="dir-badge ${s.direction === 'IN' ? 'dir-in' : 'dir-out'}">${s.direction}</span>
          <div><div class="scan-name">${s.name}</div><div class="scan-roll">${s.roll_no}</div></div>
          ${flags}<span class="scan-time">${time}</span>
        </div>`;
      }).join('');
    } catch (e) { console.error('Recent scans load failed:', e); }
  },

  async loadStudents(search = '') {
    try {
      const data = search ? await api.searchStudents(search) : await api.getStudents();
      const container = document.getElementById('students-table-container');
      if (!data.students || data.students.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--text-muted);padding:2rem">No students found</p>';
        return;
      }
      const rows = data.students.map(s => {
        const statusCls = s.is_blacklisted ? 'status-blacklisted' : (s.status === 'OUT' ? 'status-out' : 'status-in');
        const statusText = s.is_blacklisted ? 'Blacklisted' : s.status;
        return `<tr><td>${s.roll_no}</td><td style="font-weight:600">${s.name}</td><td>${s.course}</td><td>Year ${s.year}</td><td>${s.hostel}</td><td><span class="status-badge ${statusCls}"><span class="status-dot"></span>${statusText}</span></td></tr>`;
      }).join('');
      container.innerHTML = `<table><thead><tr><th>Roll No</th><th>Name</th><th>Course</th><th>Year</th><th>Hostel</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
    } catch (e) { console.error('Students load failed:', e); }
  },

  loadAll() {
    this.loadStats();
    this.loadCensus();
    this.loadChart();
    this.loadRecentScans();
  }
};
