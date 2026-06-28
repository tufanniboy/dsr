/**
 * DSR Petrol — Settings Page
 */
import { getUser } from '../auth.js';
import store from '../state.js';

export function renderSettings(container) {
    const user = getUser();
    const currentTheme = store.get('theme');

    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">Settings</h1>
                <p class="page-subtitle">Manage your account and platform preferences.</p>
            </div>
        </div>

        <div style="display:grid; grid-template-columns: 250px 1fr; gap: var(--space-6);">
            <div class="card" style="align-self: start;">
                <div class="sidebar-nav">
                    <div class="sidebar-item active">👤 Profile Settings</div>
                    <div class="sidebar-item">🎨 Appearance</div>
                    <div class="sidebar-item">🔔 Notifications</div>
                    ${user?.role === 'super_admin' ? '<div class="sidebar-item">⚙️ System Config</div>' : ''}
                </div>
            </div>
            
            <div class="card">
                <div class="card-header"><h3 class="card-title">Profile Settings</h3></div>
                <div class="card-body">
                    <div style="display:flex;gap:var(--space-4);margin-bottom:var(--space-6)">
                        <div class="avatar avatar-xl">${user?.full_name?.charAt(0) || 'U'}</div>
                        <div>
                            <h3 style="font-size:var(--text-lg);font-weight:600">${user?.full_name}</h3>
                            <p style="color:var(--text-tertiary)">${user?.email}</p>
                            <span class="badge badge-primary mt-2">${user?.role?.replace('_', ' ')}</span>
                        </div>
                    </div>
                    
                    <form style="display:flex;flex-direction:column;gap:var(--space-4);max-width:400px">
                        <div class="form-group">
                            <label class="form-label">Full Name</label>
                            <input type="text" class="form-input" value="${user?.full_name || ''}" disabled />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-input" value="${user?.email || ''}" disabled />
                        </div>
                        <div class="form-group">
                            <label class="form-label">Phone</label>
                            <input type="text" class="form-input" value="${user?.phone || ''}" disabled />
                        </div>
                    </form>
                </div>
                
                <div class="card-header" style="border-top:1px solid var(--border-light)"><h3 class="card-title">Appearance</h3></div>
                <div class="card-body">
                    <p style="margin-bottom:var(--space-3)">Select your preferred theme:</p>
                    <div style="display:flex;gap:var(--space-3)">
                        <button class="btn ${currentTheme === 'light' ? 'btn-primary' : 'btn-secondary'}" onclick="document.getElementById('theme-toggle-btn').click()">
                            ☀️ Light Mode
                        </button>
                        <button class="btn ${currentTheme === 'dark' ? 'btn-primary' : 'btn-secondary'}" onclick="document.getElementById('theme-toggle-btn').click()">
                            🌙 Dark Mode
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}
