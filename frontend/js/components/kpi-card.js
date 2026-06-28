/**
 * DSR Petrol — KPI Card with Animated Counter
 */
import { formatCurrency } from '../utils.js';

export function renderKPICard(label, value, icon, color, trend = null, isCurrency = true, delay = 0) {
    const formattedValue = isCurrency ? formatCurrency(value) : value.toLocaleString();
    const trendHtml = trend ? `
        <div class="kpi-trend ${trend.direction}">
            ${trend.direction === 'up' ? '↑' : '↓'} ${trend.value}%
        </div>` : '';

    return `
        <div class="kpi-card stagger-${delay + 1}" data-value="${value}" data-currency="${isCurrency}">
            <div class="kpi-icon ${color}">
                ${icon}
            </div>
            <div class="kpi-content">
                <div class="kpi-label">${label}</div>
                <div class="kpi-value" data-target="${value}">${formattedValue}</div>
                ${trendHtml}
            </div>
        </div>`;
}

/** Animate all KPI counters on the page */
export function animateCounters() {
    const cards = document.querySelectorAll('.kpi-value[data-target]');
    cards.forEach(el => {
        const target = parseFloat(el.dataset.target) || 0;
        if (target === 0) return;

        const isCurrency = el.closest('.kpi-card')?.dataset.currency === 'true';
        const duration = 1200;
        const start = performance.now();

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease-out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;
            el.textContent = isCurrency ? formatCurrency(current) : Math.round(current).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });
}
