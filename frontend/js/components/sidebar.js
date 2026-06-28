/**
 * DSR Petrol — Sidebar Component
 */
import store from '../state.js';
import { getUserRole } from '../auth.js';

const MENU_ITEMS = [
    {
        section: 'Main',
        items: [
            { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', path: '#/dashboard', roles: ['staff', 'manager', 'super_admin'] },
            { id: 'scan', label: 'Scan DSR', icon: 'scan', path: '#/scan', roles: ['staff', 'manager', 'super_admin'] },
            { id: 'reports', label: 'Reports', icon: 'reports', path: '#/reports', roles: ['staff', 'manager', 'super_admin'] },
        ]
    },
    {
        section: 'Analytics',
        items: [
            { id: 'ocr-history', label: 'OCR History', icon: 'history', path: '#/ocr-history', roles: ['manager', 'super_admin'] },
            { id: 'analytics', label: 'Analytics', icon: 'analytics', path: '#/analytics', roles: ['manager', 'super_admin'] },
        ]
    },
    {
        section: 'Admin',
        items: [
            { id: 'users', label: 'Users', icon: 'users', path: '#/users', roles: ['super_admin'] },
            { id: 'settings', label: 'Settings', icon: 'settings', path: '#/settings', roles: ['super_admin'] },
        ]
    },
];

const ICONS = {
    dashboard: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    scan: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7V5a2 2 0 012-2h2"/><path d="M17 3h2a2 2 0 012 2v2"/><path d="M21 17v2a2 2 0 01-2 2h-2"/><path d="M7 21H5a2 2 0 01-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>',
    reports: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    history: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    analytics: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    users: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
    settings: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
    collapse: '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>',
};

export function renderSidebar(activeId = 'dashboard') {
    const role = getUserRole();

    let html = `
        <div class="sidebar-header">
            <div class="sidebar-logo">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            </div>
            <div class="sidebar-brand">
                <span class="sidebar-brand-name">DSR Petrol</span>
                <span class="sidebar-brand-sub">Management Platform</span>
            </div>
        </div>
        <nav class="sidebar-nav">
    `;

    for (const section of MENU_ITEMS) {
        const visibleItems = section.items.filter(item => item.roles.includes(role));
        if (visibleItems.length === 0) continue;

        html += `<div class="sidebar-section">
            <div class="sidebar-section-title">${section.section}</div>`;

        for (const item of visibleItems) {
            const isActive = item.id === activeId;
            html += `
                <a href="${item.path}" class="sidebar-item ${isActive ? 'active' : ''}" data-page="${item.id}">
                    <span class="sidebar-item-icon">${ICONS[item.icon] || ''}</span>
                    <span class="sidebar-item-text">${item.label}</span>
                </a>`;
        }
        html += `</div>`;
    }

    html += `</nav>
        <div class="sidebar-footer">
            <button class="sidebar-toggle" id="sidebar-toggle-btn">
                ${ICONS.collapse}
            </button>
        </div>`;

    return html;
}

export function initSidebar() {
    const btn = document.getElementById('sidebar-toggle-btn');
    if (btn) {
        btn.addEventListener('click', () => {
            store.toggleSidebar();
            document.querySelector('.app-shell')?.classList.toggle('sidebar-collapsed');
        });
    }

    // Apply initial state
    if (store.get('sidebarCollapsed')) {
        document.querySelector('.app-shell')?.classList.add('sidebar-collapsed');
    }
}
