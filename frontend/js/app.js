/**
 * DSR Petrol Platform — Main Application Shell
 */
import router from './router.js';
import store from './state.js';
import { isAuthenticated, login, getUser } from './auth.js';
import { renderSidebar, initSidebar } from './components/sidebar.js';
import { renderTopbar, initTopbar } from './components/topbar.js';
import { showToast } from './components/toast.js';

// Page imports
import { renderDashboard } from './pages/dashboard.js';
import { renderScanDSR } from './pages/scan-dsr.js';
import { renderReviewOCR } from './pages/review-ocr.js';
import { renderReports } from './pages/reports.js';
import { renderAnalytics } from './pages/analytics.js';
import { renderUsers } from './pages/users.js';
import { renderSettings } from './pages/settings.js';
import { renderOCRHistory } from './pages/ocr-history.js';

// Apply saved theme
document.documentElement.setAttribute('data-theme', store.get('theme'));

// ── Page Renderers ──

const PAGE_TITLES = {
    dashboard: 'Dashboard',
    scan: 'Scan DSR',
    review: 'Review OCR',
    reports: 'Reports',
    analytics: 'Analytics',
    'ocr-history': 'OCR History',
    users: 'Users',
    settings: 'Settings',
};

function renderAppShell(pageId, params = {}) {
    const app = document.getElementById('app');

    app.innerHTML = `
        <div class="app-shell ${store.get('sidebarCollapsed') ? 'sidebar-collapsed' : ''}">
            <aside class="sidebar">${renderSidebar(pageId)}</aside>
            <div class="sidebar-overlay"></div>
            <main class="app-main">
                ${renderTopbar(PAGE_TITLES[pageId] || pageId, ['Home', PAGE_TITLES[pageId] || pageId])}
                <div class="content" id="page-content">
                    <div class="processing-container">
                        <div class="processing-spinner"></div>
                    </div>
                </div>
            </main>
        </div>
        <nav class="mobile-nav">
            <div class="mobile-nav-items">
                <a href="#/dashboard" class="mobile-nav-item ${pageId === 'dashboard' ? 'active' : ''}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
                    Home
                </a>
                <a href="#/scan" class="mobile-nav-item ${pageId === 'scan' ? 'active' : ''}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 7V5a2 2 0 012-2h2"/><path d="M17 3h2a2 2 0 012 2v2"/><path d="M21 17v2a2 2 0 01-2 2h-2"/><path d="M7 21H5a2 2 0 01-2-2v-2"/><line x1="7" y1="12" x2="17" y2="12"/></svg>
                    Scan
                </a>
                <a href="#/reports" class="mobile-nav-item ${pageId === 'reports' ? 'active' : ''}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    Reports
                </a>
                <a href="#/analytics" class="mobile-nav-item ${pageId === 'analytics' ? 'active' : ''}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    Analytics
                </a>
            </div>
        </nav>
    `;

    // Initialize shell components
    initSidebar();
    initTopbar();

    // Mobile sidebar overlay close
    document.querySelector('.sidebar-overlay')?.addEventListener('click', () => {
        document.querySelector('.app-shell')?.classList.remove('sidebar-open');
    });

    // Show mobile menu button on mobile
    if (window.innerWidth <= 1024) {
        const mobileBtn = document.getElementById('mobile-menu-btn');
        if (mobileBtn) mobileBtn.style.display = 'flex';
    }

    return document.getElementById('page-content');
}

function renderLoginPage() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="auth-page">
            <div class="auth-left">
                <div class="auth-form-container">
                    <div class="auth-form-header">
                        <h2>Welcome back</h2>
                        <p>Sign in to your DSR management account</p>
                    </div>
                    <form class="auth-form" id="login-form">
                        <div class="form-group">
                            <label class="form-label">Email Address</label>
                            <input type="email" class="form-input" id="login-email" placeholder="you@company.com" required autofocus />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Password</label>
                            <input type="password" class="form-input" id="login-password" placeholder="Enter your password" required />
                        </div>
                        <button type="submit" class="btn btn-primary btn-lg w-full" id="login-btn">
                            Sign In
                        </button>
                    </form>
                    <div class="auth-footer">
                        <p>Powered by DSR Petrol Platform v1.0</p>
                    </div>
                </div>
            </div>
            <div class="auth-right">
                <div class="auth-branding">
                    <div class="auth-branding-logo">
                        <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
                    </div>
                    <h1>DSR Petrol Platform</h1>
                    <p>Digitize your Daily Sales Reports with AI-powered OCR. Fast, accurate, and effortless.</p>
                    <div class="auth-features">
                        <div class="auth-feature">
                            <div class="auth-feature-icon">📷</div>
                            <span>Snap a photo of your DSR sheet</span>
                        </div>
                        <div class="auth-feature">
                            <div class="auth-feature-icon">🤖</div>
                            <span>AI extracts all values automatically</span>
                        </div>
                        <div class="auth-feature">
                            <div class="auth-feature-icon">📊</div>
                            <span>Real-time analytics & reports</span>
                        </div>
                        <div class="auth-feature">
                            <div class="auth-feature-icon">✅</div>
                            <span>Manager verification & approval</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Login handler
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;
        const btn = document.getElementById('login-btn');
        btn.disabled = true;
        btn.textContent = 'Signing in...';

        try {
            await login(email, password);
            showToast('success', 'Welcome!', 'You have signed in successfully.');
            router.navigate('/dashboard');
        } catch (err) {
            showToast('error', 'Login Failed', err.message || 'Invalid credentials');
            btn.disabled = false;
            btn.textContent = 'Sign In';
        }
    });
}

// Simple placeholder pages
function renderPlaceholderPage(container, title, subtitle) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">${title}</h1>
                <p class="page-subtitle">${subtitle}</p>
            </div>
        </div>
        <div class="card">
            <div class="card-body">
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <h3>${title}</h3>
                    <p>This section is coming soon. Check back later!</p>
                </div>
            </div>
        </div>`;
}

// ── Route Definitions ──

function authGuard(pageId, pageRenderer) {
    return (params) => {
        if (!isAuthenticated()) {
            router.navigate('/login');
            return;
        }
        const content = renderAppShell(pageId, params);
        pageRenderer(content, params);
    };
}

router.add('/login', () => {
    if (isAuthenticated()) { router.navigate('/dashboard'); return; }
    renderLoginPage();
});

router.add('/dashboard', authGuard('dashboard', renderDashboard));
router.add('/scan', authGuard('scan', renderScanDSR));
router.add('/review/:id', authGuard('review', renderReviewOCR));

router.add('/reports', authGuard('reports', renderReports));
router.add('/analytics', authGuard('analytics', renderAnalytics));
router.add('/ocr-history', authGuard('ocr-history', renderOCRHistory));
router.add('/users', authGuard('users', renderUsers));
router.add('/settings', authGuard('settings', renderSettings));

// Start router
router.start();
