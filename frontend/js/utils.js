/**
 * DSR Petrol Platform — Utility Functions
 */

/** Format number as Indian currency */
export function formatCurrency(amount) {
    if (amount == null || isNaN(amount)) return '₹0';
    const num = parseFloat(amount);
    return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

/** Format large numbers with K/L/Cr suffixes */
export function formatCompact(num) {
    if (num >= 10000000) return '₹' + (num / 10000000).toFixed(1) + ' Cr';
    if (num >= 100000) return '₹' + (num / 100000).toFixed(1) + ' L';
    if (num >= 1000) return '₹' + (num / 1000).toFixed(1) + 'K';
    return formatCurrency(num);
}

/** Format date to DD/MM/YYYY */
export function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

/** Format date to readable string */
export function formatDateLong(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** Get relative time (e.g., "2 hours ago") */
export function timeAgo(dateStr) {
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = now - then;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `${days}d ago`;
    return formatDate(dateStr);
}

/** Get today's date in YYYY-MM-DD */
export function today() {
    return new Date().toISOString().split('T')[0];
}

/** Get first day of current month in YYYY-MM-DD */
export function monthStart() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
}

/** Generate initials from a name */
export function getInitials(name) {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

/** Debounce function */
export function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}

/** Get status badge class */
export function getStatusBadge(status) {
    const map = {
        approved: 'badge-success',
        pending_review: 'badge-warning',
        processing: 'badge-info',
        rejected: 'badge-danger',
        draft: 'badge-neutral',
    };
    return map[status] || 'badge-neutral';
}

/** Get status display name */
export function getStatusLabel(status) {
    const map = {
        approved: 'Approved',
        pending_review: 'Pending Review',
        processing: 'Processing',
        rejected: 'Rejected',
        draft: 'Draft',
    };
    return map[status] || status;
}

/** Sanitize HTML to prevent XSS */
export function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/** Create an element with attributes */
export function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);
    for (const [key, val] of Object.entries(attrs)) {
        if (key === 'className') el.className = val;
        else if (key === 'innerHTML') el.innerHTML = val;
        else if (key === 'textContent') el.textContent = val;
        else if (key.startsWith('on')) el.addEventListener(key.slice(2).toLowerCase(), val);
        else el.setAttribute(key, val);
    }
    children.forEach(child => {
        if (typeof child === 'string') el.appendChild(document.createTextNode(child));
        else if (child) el.appendChild(child);
    });
    return el;
}
