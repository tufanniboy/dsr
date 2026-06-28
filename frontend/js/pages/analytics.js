/**
 * DSR Petrol — Analytics Page
 */
import api from '../api.js';

export async function renderAnalytics(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Analytics</h1>
                <p class="page-subtitle">Deep dive into sales performance and trends.</p>
            </div>
            <div class="date-range-picker">
                <select id="analytics-year" class="form-select">
                    <option value="2024">2024</option>
                    <option value="2023">2023</option>
                </select>
            </div>
        </div>

        <div class="analytics-grid">
            <div class="analytics-chart-card full-width">
                <div class="analytics-chart-header">
                    <h3 class="analytics-chart-title">Monthly Revenue</h3>
                </div>
                <div class="chart-canvas-wrapper" style="height:350px">
                    <canvas id="monthly-revenue-chart"></canvas>
                </div>
            </div>

            <div class="analytics-chart-card">
                <div class="analytics-chart-header">
                    <h3 class="analytics-chart-title">Manager Performance</h3>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="manager-chart"></canvas>
                </div>
            </div>

            <div class="analytics-chart-card">
                <div class="analytics-chart-header">
                    <h3 class="analytics-chart-title">Collection Distribution</h3>
                </div>
                <div class="chart-canvas-wrapper">
                    <canvas id="collection-chart"></canvas>
                </div>
            </div>
        </div>
    `;

    setTimeout(loadAnalytics, 100);
}

async function loadAnalytics() {
    if (!window.Chart) return;

    try {
        const year = document.getElementById('analytics-year').value;
        const monthly = await api.getMonthlyRevenue(year);
        
        // 1. Monthly Revenue Bar Chart
        new Chart(document.getElementById('monthly-revenue-chart'), {
            type: 'bar',
            data: {
                labels: monthly.map(m => m.month),
                datasets: [{
                    label: 'Revenue',
                    data: monthly.map(m => m.revenue),
                    backgroundColor: '#FF6B00',
                    borderRadius: 4
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
                        ticks: { callback: v => '₹' + (v/100000).toFixed(1) + 'L' }
                    },
                    x: { grid: { display: false } }
                }
            }
        });

        // 2. Manager Performance (Dummy Data for visual for now, ideally API call)
        new Chart(document.getElementById('manager-chart'), {
            type: 'bar',
            data: {
                labels: ['Amit', 'Raj', 'Vikram', 'Priya'],
                datasets: [{
                    label: 'Reports Processed',
                    data: [142, 125, 98, 110],
                    backgroundColor: '#3B82F6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: { legend: { display: false } }
            }
        });

        // 3. Collection Distribution
        const kpis = await api.getKPIs();
        new Chart(document.getElementById('collection-chart'), {
            type: 'polarArea',
            data: {
                labels: ['Cash', 'UPI', 'Card', 'Credit'],
                datasets: [{
                    data: [kpis.cash_collection, kpis.upi_collection, kpis.card_collection, kpis.credit_collection],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.7)',
                        'rgba(124, 58, 237, 0.7)',
                        'rgba(37, 99, 235, 0.7)',
                        'rgba(245, 158, 11, 0.7)'
                    ]
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'right' } }
            }
        });

    } catch (e) {
        console.error('Analytics load error', e);
    }
}
