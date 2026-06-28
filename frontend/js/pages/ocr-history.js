/**
 * DSR Petrol — OCR History Page
 */
export function renderOCRHistory(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">OCR Processing History</h1>
                <p class="page-subtitle">Logs and confidence metrics for all processed scans.</p>
            </div>
        </div>
        
        <div class="empty-state card" style="padding: 60px">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            <h3 class="mt-4">OCR Logs Tracking</h3>
            <p style="max-width:500px;margin-top:10px">This page will display a detailed breakdown of PaddleOCR inference times, field confidence scores, and Gemini AI fallback usage metrics.</p>
        </div>
    `;
}
