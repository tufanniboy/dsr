/**
 * DSR Petrol Platform — Simple State Management
 */

class Store {
    constructor() {
        this._state = {
            user: null,
            token: null,
            theme: localStorage.getItem('dsr-theme') || 'light',
            sidebarCollapsed: localStorage.getItem('dsr-sidebar') === 'true',
            notifications: [],
            unreadCount: 0,
        };
        this._listeners = new Map();
    }

    get(key) { return this._state[key]; }

    set(key, value) {
        const old = this._state[key];
        this._state[key] = value;
        if (old !== value) this._notify(key, value, old);
    }

    subscribe(key, callback) {
        if (!this._listeners.has(key)) this._listeners.set(key, new Set());
        this._listeners.get(key).add(callback);
        return () => this._listeners.get(key)?.delete(callback);
    }

    _notify(key, newVal, oldVal) {
        this._listeners.get(key)?.forEach(cb => cb(newVal, oldVal));
    }

    // Persistence
    saveSession() {
        if (this._state.token) {
            sessionStorage.setItem('dsr-token', this._state.token);
        }
        if (this._state.user) {
            sessionStorage.setItem('dsr-user', JSON.stringify(this._state.user));
        }
    }

    loadSession() {
        const token = sessionStorage.getItem('dsr-token');
        const user = sessionStorage.getItem('dsr-user');
        if (token) this._state.token = token;
        if (user) {
            try { this._state.user = JSON.parse(user); } catch (e) {}
        }
    }

    clearSession() {
        sessionStorage.removeItem('dsr-token');
        sessionStorage.removeItem('dsr-user');
        this._state.user = null;
        this._state.token = null;
    }

    setTheme(theme) {
        this.set('theme', theme);
        localStorage.setItem('dsr-theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
    }

    toggleSidebar() {
        const collapsed = !this._state.sidebarCollapsed;
        this.set('sidebarCollapsed', collapsed);
        localStorage.setItem('dsr-sidebar', collapsed);
    }
}

const store = new Store();
store.loadSession();

export default store;
