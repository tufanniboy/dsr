/**
 * DSR Petrol — OCR Review Page (Split Screen)
 */
import api from '../api.js';
import { showToast } from '../components/toast.js';
import { formatCurrency, escapeHtml } from '../utils.js';

export async function renderReviewOCR(container, params = {}) {
    const reportId = params.id;
    if (!reportId) {
        container.innerHTML = '<div class="empty-state"><h3>No report selected</h3></div>';
        return;
    }

    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Review OCR Results</h1>
                <p class="page-subtitle">Verify extracted data and approve or reject the report.</p>
            </div>
        </div>
        <div id="review-content">
            <div class="processing-container">
                <div class="processing-spinner"></div>
                <p>Loading report data...</p>
            </div>
        </div>`;

    try {
        const data = await api.getDSR(reportId);
        renderReviewUI(container, data, reportId);
    } catch (e) {
        container.querySelector('#review-content').innerHTML = `
            <div class="empty-state">
                <h3>Failed to load report</h3>
                <p>${e.message}</p>
                <a href="#/dashboard" class="btn btn-primary mt-4">Back to Dashboard</a>
            </div>`;
    }
}

function renderReviewUI(container, data, reportId) {
    const report = data.report;
    const entries = data.entries || [];
    const ocrFields = data.ocr_fields || [];
    const validations = data.validation || [];

    const isProcessing = report.status === 'processing';
    if (isProcessing) {
        container.querySelector('#review-content').innerHTML = `
            <div class="processing-container">
                <div class="processing-spinner"></div>
                <h3>OCR Processing in Progress</h3>
                <p style="color:var(--text-tertiary)">This page will refresh automatically when processing completes.</p>
            </div>`;
        setTimeout(() => renderReviewOCR(container, { id: reportId }), 3000);
        return;
    }

    // Build field confidence map
    const fieldConfMap = {};
    ocrFields.forEach(f => { fieldConfMap[f.field_name] = f; });

    const getConfClass = (fieldName) => {
        const f = fieldConfMap[fieldName];
        if (!f) return '';
        return `confidence-${f.confidence_level || 'low'}`;
    };

    const getConfBadge = (fieldName) => {
        const f = fieldConfMap[fieldName];
        if (!f) return '';
        const pct = Math.round((f.ocr_confidence || 0) * 100);
        return `<span class="confidence-badge ${f.confidence_level || 'low'}">${pct}%</span>`;
    };

    // Validation warnings HTML
    const validationHtml = validations.length > 0 ? `
        <div class="mb-4">
            <h4 style="font-size:var(--text-sm);font-weight:var(--font-semibold);margin-bottom:var(--space-2)">⚠ Validation Issues (${validations.length})</h4>
            ${validations.map(v => `
                <div class="validation-${v.severity === 'error' ? 'error' : 'warning'}">
                    <strong>${v.rule_name}:</strong> ${escapeHtml(v.message)}
                </div>
            `).join('')}
        </div>` : '';

    // Fields for each duty
    const DUTY_FIELDS = [
        'start_reading', 'end_reading', 'testing', 'rate', 'total_amount',
        'card', 'upi', 'expenses', 'credit', 'total_cash_in_hand', 'short_amount'
    ];

    const dutySections = entries.map((entry, i) => `
        <div class="duty-section">
            <div class="duty-header">
                <span class="duty-title">Duty ${entry.duty_number} — ${escapeHtml(entry.duty_name) || 'Unnamed'}</span>
            </div>
            ${DUTY_FIELDS.map(field => {
                const fieldKey = `duty_${entry.duty_number}_${field}`;
                const value = entry[field] ?? '';
                return `
                <div class="ocr-field">
                    <label class="ocr-field-label">${field.replace(/_/g, ' ')}</label>
                    <input type="text" class="ocr-field-input ${getConfClass(fieldKey)}"
                           data-duty="${entry.duty_number}" data-field="${field}"
                           value="${value}" />
                    <div class="ocr-field-meta">${getConfBadge(fieldKey)}</div>
                </div>`;
            }).join('')}
        </div>
    `).join('');

    container.querySelector('#review-content').innerHTML = `
        <div class="review-container">
            <!-- LEFT: Image Panel -->
            <div class="review-image-panel">
                <div class="review-image-toolbar">
                    <span style="font-size:var(--text-sm);font-weight:var(--font-medium)">Original Scan</span>
                    <div style="display:flex;gap:var(--space-2)">
                        <button class="btn btn-ghost btn-sm" id="img-zoom-in">🔍+</button>
                        <button class="btn btn-ghost btn-sm" id="img-zoom-out">🔍−</button>
                        <button class="btn btn-ghost btn-sm" id="img-rotate">↻</button>
                    </div>
                </div>
                <div class="review-image-wrapper" id="image-wrapper">
                    <img id="review-image" src="${report.original_image_url || report.processed_image_url || ''}"
                         alt="DSR Scan" style="transition: transform 0.3s ease" />
                </div>
            </div>

            <!-- RIGHT: Fields Panel -->
            <div class="review-fields-panel">
                <div class="review-fields-header">
                    <span style="font-size:var(--text-sm);font-weight:var(--font-medium)">Extracted Data</span>
                    <span class="badge badge-${report.status === 'approved' ? 'success' : report.status === 'rejected' ? 'danger' : 'warning'}">${report.status?.replace('_', ' ')}</span>
                </div>
                <div class="review-fields-body">
                    ${validationHtml}

                    <!-- Header Fields -->
                    <div class="duty-section">
                        <div class="duty-header">
                            <span class="duty-title">Report Header</span>
                        </div>
                        <div class="ocr-field">
                            <label class="ocr-field-label">Manager Name</label>
                            <input type="text" class="ocr-field-input ${getConfClass('manager_name')}"
                                   id="field-manager-name" value="${escapeHtml(report.manager_name) || ''}" />
                            <div class="ocr-field-meta">${getConfBadge('manager_name')}</div>
                        </div>
                        <div class="ocr-field">
                            <label class="ocr-field-label">Date</label>
                            <input type="date" class="ocr-field-input" id="field-date"
                                   value="${report.report_date || ''}" />
                        </div>
                    </div>

                    ${dutySections}
                </div>

                <div class="review-fields-footer">
                    ${report.status === 'pending_review' ? `
                        <button class="btn btn-secondary" id="save-draft-btn">Save Draft</button>
                        <button class="btn btn-danger" id="reject-btn">Reject</button>
                        <button class="btn btn-success" id="approve-btn">✓ Approve</button>
                    ` : `
                        <a href="#/dashboard" class="btn btn-secondary">Back to Dashboard</a>
                    `}
                </div>
            </div>
        </div>`;

    // Image controls
    let zoom = 1, imgRotation = 0;
    const img = document.getElementById('review-image');
    document.getElementById('img-zoom-in')?.addEventListener('click', () => {
        zoom = Math.min(zoom + 0.25, 3);
        img.style.transform = `scale(${zoom}) rotate(${imgRotation}deg)`;
    });
    document.getElementById('img-zoom-out')?.addEventListener('click', () => {
        zoom = Math.max(zoom - 0.25, 0.5);
        img.style.transform = `scale(${zoom}) rotate(${imgRotation}deg)`;
    });
    document.getElementById('img-rotate')?.addEventListener('click', () => {
        imgRotation = (imgRotation + 90) % 360;
        img.style.transform = `scale(${zoom}) rotate(${imgRotation}deg)`;
    });

    // Action buttons
    document.getElementById('approve-btn')?.addEventListener('click', async () => {
        try {
            await saveFields(reportId);
            await api.approveDSR(reportId);
            showToast('success', 'Report Approved', 'The DSR has been approved successfully.');
            setTimeout(() => window.location.hash = '#/dashboard', 1000);
        } catch (e) { showToast('error', 'Approval Failed', e.message); }
    });

    document.getElementById('reject-btn')?.addEventListener('click', async () => {
        const reason = prompt('Enter rejection reason:');
        if (!reason) return;
        try {
            await api.rejectDSR(reportId, reason);
            showToast('warning', 'Report Rejected', reason);
            setTimeout(() => window.location.hash = '#/dashboard', 1000);
        } catch (e) { showToast('error', 'Rejection Failed', e.message); }
    });

    document.getElementById('save-draft-btn')?.addEventListener('click', async () => {
        try {
            await saveFields(reportId);
            showToast('success', 'Draft Saved', 'Changes have been saved.');
        } catch (e) { showToast('error', 'Save Failed', e.message); }
    });
}

async function saveFields(reportId) {
    const managerName = document.getElementById('field-manager-name')?.value;
    const reportDate = document.getElementById('field-date')?.value;

    const entries = [];
    document.querySelectorAll('.ocr-field-input[data-duty]').forEach(input => {
        const duty = parseInt(input.dataset.duty);
        const field = input.dataset.field;
        let entry = entries.find(e => e.duty_number === duty);
        if (!entry) { entry = { duty_number: duty }; entries.push(entry); }
        const val = input.value.trim();
        entry[field] = val === '' ? null : (isNaN(val) ? val : parseFloat(val));
    });

    await api.updateDSR(reportId, { manager_name: managerName, report_date: reportDate, entries });
}
