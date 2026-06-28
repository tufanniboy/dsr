/**
 * DSR Petrol — Dashboard Page
 */
import api from '../api.js';
import { renderKPICard, animateCounters } from '../components/kpi-card.js';
import { formatCurrency, formatDate, getStatusBadge, getStatusLabel } from '../utils.js';

const KPI_ICONS = {
    sales: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
    revenue: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
    cash: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><circle cx="12" cy="12" r="3"/></svg>',
    upi: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>',
    credit: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 4H3a2 2 0 00-2 2v12a2 2 0 002 2h18a2 2 0 002-2V6a2 2 0 00-2-2z"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    expense: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    report: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>',
    pending: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
};

export async function renderDashboard(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Dashboard</h1>
                <p class="page-subtitle">Welcome back! Here's your daily overview.</p>
            </div>
            <div class="page-actions">
                <a href="#/scan" class="btn btn-primary">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7V5a2 2 0 012-2h2"/><path d="M17 3h2a2 2 0 012 2v2"/><path d="M21 17v2a2 2 0 01-2 2h-2"/><path d="M7 21H5a2 2 0 01-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>
                    Scan DSR
                </a>
            </div>
        </div>

        <div class="kpi-grid" id="kpi-grid">
            ${Array(8).fill('<div class="kpi-card"><div class="skeleton" style="width:100%;height:80px"></div></div>').join('')}
        </div>

        <div class="chart-grid">
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Sales Trend (7 Days)</h3>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="sales-trend-chart"></canvas>
                </div>
            </div>
            <div class="chart-container">
                <div class="chart-header">
                    <h3 class="chart-title">Payment Methods</h3>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="payment-chart"></canvas>
                </div>
            </div>
        </div>

        <div class="activity-section">
            <div class="activity-header">
                <h3 class="activity-title">Recent Reports</h3>
                <a href="#/reports" class="btn btn-ghost btn-sm">View All →</a>
            </div>
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Manager</th>
                            <th>Status</th>
                            <th>Total Sales</th>
                            <th>Cash</th>
                            <th>UPI</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="recent-reports-body">
                        <tr><td colspan="7" class="text-center p-6"><div class="skeleton" style="height:20px;width:200px;margin:0 auto"></div></td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Load data
    loadKPIs();
    loadSalesTrend();
    loadRecentReports();
}

async function loadKPIs() {
    try {
        const kpis = await api.getKPIs();
        const grid = document.getElementById('kpi-grid');
        if (!grid) return;

        grid.innerHTML = [
            renderKPICard("Today's Sales", kpis.today_sales, KPI_ICONS.sales, 'orange', null, true, 0),
            renderKPICard('Monthly Sales', kpis.monthly_sales, KPI_ICONS.revenue, 'blue', null, true, 1),
            renderKPICard('Cash Collection', kpis.cash_collection, KPI_ICONS.cash, 'green', null, true, 2),
            renderKPICard('UPI Collection', kpis.upi_collection, KPI_ICONS.upi, 'purple', null, true, 3),
            renderKPICard('Card Collection', kpis.card_collection, KPI_ICONS.credit, 'blue', null, true, 4),
            renderKPICard('Expenses', kpis.expenses, KPI_ICONS.expense, 'red', null, true, 5),
            renderKPICard('Net Revenue', kpis.net_revenue, KPI_ICONS.revenue, 'green', null, true, 6),
            renderKPICard('Pending Approvals', kpis.pending_approvals, KPI_ICONS.pending, 'yellow', null, false, 7),
        ].join('');

        // Animate counters after render
        setTimeout(animateCounters, 100);
    } catch (e) {
        console.error('Failed to load KPIs:', e);
    }
}

async function loadSalesTrend() {
    try {
        const trend = await api.getSalesTrend(7);
        const canvas = document.getElementById('sales-trend-chart');
        if (!canvas || !window.Chart) return;

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: trend.map(d => {
                    const dt = new Date(d.date);
                    return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
                }),
                datasets: [{
                    label: 'Daily Sales',
                    data: trend.map(d => d.sales),
                    borderColor: '#FF6B00',
                    backgroundColor: 'rgba(255, 107, 0, 0.08)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#FF6B00',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.04)' },
                        ticks: {
                            callback: v => '₹' + (v >= 100000 ? (v/100000).toFixed(1) + 'L' : (v/1000).toFixed(0) + 'K'),
                            font: { size: 11 },
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { size: 11 } }
                    }
                },
                interaction: { intersect: false, mode: 'index' },
            }
        });

        // Payment chart
        const kpis = await api.getKPIs();
        const payCanvas = document.getElementById('payment-chart');
        if (payCanvas && window.Chart) {
            new Chart(payCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Cash', 'UPI', 'Card', 'Credit'],
                    datasets: [{
                        data: [kpis.cash_collection, kpis.upi_collection, kpis.card_collection, kpis.credit_collection],
                        backgroundColor: ['#10B981', '#7C3AED', '#2563EB', '#F59E0B'],
                        borderWidth: 0,
                        hoverOffset: 8,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { padding: 16, usePointStyle: true, pointStyle: 'circle', font: { size: 12 } }
                        }
                    },
                    cutout: '65%',
                }
            });
        }
    } catch (e) {
        console.error('Failed to load charts:', e);
    }
}

async function loadRecentReports() {
    try {
        const result = await api.getDSRList({ per_page: 8 });
        const tbody = document.getElementById('recent-reports-body');
        if (!tbody) return;

        if (!result.data || result.data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center p-6 text-secondary">No reports yet. <a href="#/scan">Upload your first DSR</a></td></tr>`;
            return;
        }

        tbody.innerHTML = result.data.map(r => `
            <tr>
                <td>${formatDate(r.report_date)}</td>
                <td>${r.manager_name || '—'}</td>
                <td><span class="badge badge-dot ${getStatusBadge(r.status)}">${getStatusLabel(r.status)}</span></td>
                <td class="amount">${formatCurrency(r.total_sales)}</td>
                <td class="amount">${formatCurrency(r.total_cash)}</td>
                <td class="amount">${formatCurrency(r.total_upi)}</td>
                <td>
                    <a href="#/review/${r.id}" class="btn btn-ghost btn-sm">View</a>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Failed to load reports:', e);
    }
}
