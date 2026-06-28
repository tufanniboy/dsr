/**
 * DSR Petrol — Topbar Component
 */
import store from '../state.js';
import { getInitials } from '../utils.js';
import { logout, getUser } from '../auth.js';

export function renderTopbar(pageTitle = 'Dashboard', breadcrumbs = []) {
    const user = getUser();
    const initials = getInitials(user?.full_name);
    const theme = store.get('theme');

    const crumbs = breadcrumbs.map((c, i) =>
        i < breadcrumbs.length - 1
            ? `<span>${c}</span><span class="topbar-breadcrumb-sep">/</span>`
            : `<span>${c}</span>`
    ).join('');

    return `
        <header class="topbar">
            <div class="topbar-left">
                <button class="btn btn-icon btn-ghost" id="mobile-menu-btn" style="display:none">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
                </button>
                <div class="topbar-breadcrumb">${crumbs || `<span>${pageTitle}</span>`}</div>
            </div>
            <div class="topbar-right">
                <div class="topbar-search">
                    <svg class="topbar-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <input type="text" placeholder="Search reports..." id="global-search-input" />
                </div>

                <button class="btn btn-icon btn-ghost" id="theme-toggle-btn" data-tooltip="Toggle Theme">
                    ${theme === 'dark'
                        ? '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
                        : '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/></svg>'
                    }
                </button>

                <div class="topbar-notification" id="notification-bell">
                    <button class="btn btn-icon btn-ghost">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
                    </button>
                    <span class="topbar-notification-count hidden" id="notif-count">0</span>
                </div>

                <div class="topbar-user dropdown" id="user-menu">
                    <div class="avatar">${initials}</div>
                    <div class="topbar-user-info">
                        <span class="topbar-user-name">${user?.full_name || 'User'}</span>
                        <span class="topbar-user-role">${user?.role?.replace('_', ' ') || 'Staff'}</span>
                    </div>
                    <div class="dropdown-menu" id="user-dropdown">
                        <a class="dropdown-item" href="#/profile">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                            Profile
                        </a>
                        <a class="dropdown-item" href="#/settings">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-3.46-1.41V18"/></svg>
                            Settings
                        </a>
                        <div class="dropdown-divider"></div>
                        <div class="dropdown-item" id="logout-btn" style="color:var(--color-danger)">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                            Logout
                        </div>
                    </div>
                </div>
            </div>
        </header>`;
}

export function initTopbar() {
    // Theme toggle
    document.getElementById('theme-toggle-btn')?.addEventListener('click', () => {
        const current = store.get('theme');
        store.setTheme(current === 'dark' ? 'light' : 'dark');
        // Re-render the page to update icon
        window.dispatchEvent(new HashChangeEvent('hashchange'));
    });

    // User dropdown
    const userMenu = document.getElementById('user-menu');
    userMenu?.addEventListener('click', (e) => {
        userMenu.classList.toggle('open');
        e.stopPropagation();
    });

    document.addEventListener('click', () => {
        document.querySelectorAll('.dropdown.open').forEach(d => d.classList.remove('open'));
    });

    // Logout
    document.getElementById('logout-btn')?.addEventListener('click', () => logout());

    // Mobile menu
    document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
        document.querySelector('.app-shell')?.classList.toggle('sidebar-open');
    });

    // Global search
    const searchInput = document.getElementById('global-search-input');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) window.location.hash = `#/reports?search=${encodeURIComponent(query)}`;
            }
        });
    }
}
