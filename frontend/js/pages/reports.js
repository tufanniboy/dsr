/**
 * DSR Petrol — Reports Page
 */
import api from '../api.js';
import { formatCurrency, formatDate, getStatusBadge, getStatusLabel } from '../utils.js';
import { showLoader } from '../components/loader.js';

export async function renderReports(container, params = {}) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Reports</h1>
                <p class="page-subtitle">View and export generated DSR reports.</p>
            </div>
            <div class="export-group">
                <button class="btn btn-secondary" id="export-excel">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="8" y1="13" x2="16" y2="13"></line><line x1="8" y1="17" x2="16" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Export Excel
                </button>
            </div>
        </div>

        <div class="data-table-container">
            <div class="data-table-toolbar">
                <div class="data-table-filters">
                    <div class="filter-group">
                        <label class="filter-label">Date Range</label>
                        <div class="date-range-picker">
                            <input type="date" id="filter-start" />
                            <span class="date-range-sep">to</span>
                            <input type="date" id="filter-end" />
                        </div>
                    </div>
                    <div class="filter-group">
                        <label class="filter-label">Status</label>
                        <select class="form-select" id="filter-status">
                            <option value="">All Statuses</option>
                            <option value="approved">Approved</option>
                            <option value="pending_review">Pending Review</option>
                            <option value="rejected">Rejected</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" id="apply-filters" style="margin-top:20px">Filter</button>
                </div>
            </div>
            
            <div class="data-table-wrapper" id="reports-table-wrapper">
                <!-- Table goes here -->
            </div>
            
            <div class="pagination" id="reports-pagination">
                <!-- Pagination goes here -->
            </div>
        </div>
    `;

    // Defaults
    const searchParams = new URLSearchParams(window.location.hash.split('?')[1] || '');
    if (searchParams.has('search')) {
        // Will handle global search query
    }

    // Default dates (this month)
    const d = new Date();
    document.getElementById('filter-end').value = d.toISOString().split('T')[0];
    d.setDate(1);
    document.getElementById('filter-start').value = d.toISOString().split('T')[0];

    document.getElementById('apply-filters').addEventListener('click', () => loadReports(1));

    loadReports(1);
}

async function loadReports(page) {
    const wrapper = document.getElementById('reports-table-wrapper');
    const pag = document.getElementById('reports-pagination');
    
    showLoader(wrapper, 'Loading reports...');

    const start = document.getElementById('filter-start').value;
    const end = document.getElementById('filter-end').value;
    const status = document.getElementById('filter-status').value;

    try {
        const queryParams = { page, per_page: 20 };
        if (start) queryParams.start_date = start;
        if (end) queryParams.end_date = end;
        if (status) queryParams.status = status;

        let result;
        // Check if coming from global search
        const globalSearch = new URLSearchParams(window.location.hash.split('?')[1]).get('search');
        if (globalSearch) {
            result = await api.search(globalSearch, null, page);
        } else {
            result = await api.getDSRList(queryParams);
        }
        
        if (!result.data || result.data.length === 0) {
            wrapper.innerHTML = `
                <div class="empty-state">
                    <h3>No reports found</h3>
                    <p>Try adjusting your filters.</p>
                </div>
            `;
            pag.innerHTML = '';
            return;
        }

        wrapper.innerHTML = `
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Report Date</th>
                        <th>Manager Name</th>
                        <th>Status</th>
                        <th class="text-right">Total Sales</th>
                        <th class="text-right">Cash</th>
                        <th class="text-right">UPI</th>
                        <th class="text-right">Card</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${result.data.map(r => `
                        <tr>
                            <td><strong>${formatDate(r.report_date)}</strong></td>
                            <td>${r.manager_name || '—'}</td>
                            <td><span class="badge badge-dot ${getStatusBadge(r.status)}">${getStatusLabel(r.status)}</span></td>
                            <td class="amount" style="font-weight:600">${formatCurrency(r.total_sales)}</td>
                            <td class="amount">${formatCurrency(r.total_cash)}</td>
                            <td class="amount">${formatCurrency(r.total_upi)}</td>
                            <td class="amount">${formatCurrency(r.total_card)}</td>
                            <td>
                                <a href="#/review/${r.id}" class="btn btn-ghost btn-sm">View</a>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        // Render Pagination
        const totalPages = Math.ceil(result.total / result.per_page);
        pag.innerHTML = `
            <div class="pagination-info">Showing ${((page - 1) * result.per_page) + 1} to ${Math.min(page * result.per_page, result.total)} of ${result.total} reports</div>
            <div class="pagination-controls">
                <button class="pagination-btn" ${page === 1 ? 'disabled' : ''} onclick="window.loadReportsPage(${page - 1})">Prev</button>
                <button class="pagination-btn active">${page}</button>
                <button class="pagination-btn" ${page >= totalPages ? 'disabled' : ''} onclick="window.loadReportsPage(${page + 1})">Next</button>
            </div>
        `;

        // Export setup
        document.getElementById('export-excel').onclick = async () => {
            const blob = await api.exportReport('excel', { start_date: start, end_date: end });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `dsr_export_${start}_to_${end}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
        };

    } catch (e) {
        wrapper.innerHTML = `<div class="empty-state"><p style="color:var(--color-danger)">Error: ${e.message}</p></div>`;
    }
}

// Attach to window for onclick handlers
window.loadReportsPage = loadReports;
