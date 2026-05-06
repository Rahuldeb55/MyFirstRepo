/* Barcode Scanner Module — Uses html5-qrcode for camera-based barcode reading */
const Scanner = {
  html5QrCode: null,
  isScanning: false,
  lastScanTime: 0,

  init() {
    this.html5QrCode = new Html5Qrcode("barcode-reader");
    this.startCamera();
    document.getElementById('manual-scan-btn').addEventListener('click', () => this.manualScan());
    document.getElementById('manual-roll-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.manualScan();
    });
  },

  async startCamera() {
    try {
      await this.html5QrCode.start(
        { facingMode: "environment" },
        { fps: 15, qrbox: { width: 280, height: 120 }, aspectRatio: 1.333, formatsToSupport: [
          Html5QrcodeSupportedFormats.CODE_128, Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.EAN_13, Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.UPC_A, Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.QR_CODE, Html5QrcodeSupportedFormats.CODE_93,
          Html5QrcodeSupportedFormats.CODABAR, Html5QrcodeSupportedFormats.ITF,
        ]},
        (decodedText) => this.onScanSuccess(decodedText),
        () => {} // Ignore failures
      );
      this.isScanning = true;
    } catch (err) {
      console.warn('Camera not available:', err);
      document.getElementById('barcode-reader').innerHTML =
        '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);flex-direction:column;padding:2rem;text-align:center">' +
        '<p style="font-size:0.9rem">📷 Camera not available</p>' +
        '<p style="font-size:0.8rem;margin-top:0.5rem">Mobile browsers require <strong>HTTPS</strong> for camera access.</p>' +
        '<p style="font-size:0.8rem;margin-top:0.3rem">Use the manual input below to enter Roll Numbers.</p></div>';
    }
  },

  async onScanSuccess(decodedText) {
    // Debounce: prevent rapid re-scans
    const now = Date.now();
    if (now - this.lastScanTime < 3000) return;
    this.lastScanTime = now;
    await this.processScan(decodedText.trim());
  },

  async manualScan() {
    const input = document.getElementById('manual-roll-input');
    const rollNo = input.value.trim();
    if (!rollNo) return;
    input.value = '';
    await this.processScan(rollNo);
  },

  async processScan(rollNo) {
    const resultPanel = document.getElementById('scan-result');
    const emptyState = document.getElementById('empty-state');

    try {
      const guard = JSON.parse(localStorage.getItem('campusgate_guard') || '{}');
      const manualToggle = document.getElementById('manual-toggle');
      const manualDir = manualToggle.checked ? document.getElementById('manual-direction').value : null;

      const data = await api.scan(rollNo, guard.id || 'GUARD001', manualDir);
      emptyState.classList.add('hidden');
      resultPanel.classList.remove('hidden');
      resultPanel.innerHTML = this.renderResult(data);
      resultPanel.querySelector('.scan-result')?.classList.add('fade-in');

      // Bind scan-again button
      const btn = document.getElementById('scan-again-btn');
      if (btn) btn.addEventListener('click', () => {
        resultPanel.classList.add('hidden');
        emptyState.classList.remove('hidden');
      });

      // Refresh recent scans
      Dashboard.loadRecentScans();

      if (data.status === 'SUCCESS') {
        App.showToast(`${data.direction === 'OUT' ? '🚶 EXIT' : '🏠 ENTRY'}: ${data.student?.name}`, 'success');
      } else if (data.status === 'DENIED') {
        App.showToast(`⛔ Denied: ${data.reason}`, 'error');
      }
    } catch (err) {
      App.showToast('Scan failed: ' + err.message, 'error');
    }
  },

  renderResult(data) {
    const s = data.student;
    if (!s) return `<div class="result-status denied">ERROR<div class="result-direction">${data.reason || 'Unknown error'}</div></div>`;

    const statusClass = data.status === 'DENIED' ? 'denied' : (data.is_late_alert ? 'late' : 'allowed');
    const statusText = data.status === 'DENIED' ? '⛔ ACCESS DENIED' :
                       (data.direction === 'OUT' ? '🚶 EXITING CAMPUS' : '🏠 ENTERING CAMPUS');
    const lateHtml = data.is_late_alert ? '<div style="margin-top:0.5rem;font-size:0.85rem">⚠️ LATE RETURN DETECTED</div>' : '';
    const deniedHtml = data.status === 'DENIED' ? `<div style="margin-top:0.8rem;padding:0.7rem;background:var(--danger-bg);border-radius:var(--radius-sm);font-size:0.85rem;color:var(--danger)">${data.reason}</div>` : '';

    return `
      <div class="result-status ${statusClass}">${statusText}${lateHtml}</div>
      ${deniedHtml}
      <div class="student-profile">
        <div class="student-name">${s.name}</div>
        <div class="student-roll">Roll No: ${s.roll_no} &nbsp;|&nbsp; ${s.course}</div>
        <div class="student-details">
          <div class="detail-item"><div class="detail-label">Father's Name</div><div class="detail-value">${s.father_name}</div></div>
          <div class="detail-item"><div class="detail-label">Course</div><div class="detail-value">${s.course}</div></div>
          <div class="detail-item"><div class="detail-label">Date of Birth</div><div class="detail-value">${s.date_of_birth || '—'}</div></div>
          <div class="detail-item"><div class="detail-label">Blood Group</div><div class="detail-value">${s.blood_group || '—'}</div></div>
          <div class="detail-item"><div class="detail-label">Phone</div><div class="detail-value">${s.phone || '—'}</div></div>
          <div class="detail-item"><div class="detail-label">Year</div><div class="detail-value">${s.year}</div></div>
          <div class="detail-item"><div class="detail-label">Hostel</div><div class="detail-value">${s.hostel}</div></div>
          <div class="detail-item"><div class="detail-label">Room</div><div class="detail-value">${s.room}</div></div>
        </div>
        ${data.predicted_return_hours ? \`<div class="detail-item" style="margin-top:0.6rem"><div class="detail-label">Predicted Return</div><div class="detail-value">\${data.predicted_return_hours} hours</div></div>\` : ''}
        <div class="emergency-actions">
          <a href="tel:${s.emergency.warden_contact}" class="btn-call btn-call-warden">📞 ${s.emergency.warden_name || 'Call Warden'}</a>
          <a href="tel:${s.emergency.parent_contact}" class="btn-call btn-call-parent">📞 ${s.emergency.father_name || 'Call Father'}</a>
        </div>
        <button class="btn btn-ghost btn-full scan-again-btn" id="scan-again-btn" style="margin-top:1rem">Scan Next Student</button>
      </div>`;
  },

  stop() {
    if (this.html5QrCode && this.isScanning) {
      this.html5QrCode.stop().catch(() => {});
      this.isScanning = false;
    }
  }
};
