/**
 * DSR Petrol Platform — API Client
 */
import CONFIG from './config.js';
import store from './state.js';

class ApiClient {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
    }

    _headers() {
        const headers = { 'Content-Type': 'application/json' };
        const token = store.get('token');
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }

    async _fetch(path, options = {}) {
        const url = `${this.baseUrl}${path}`;
        const config = {
            headers: this._headers(),
            ...options,
        };

        // Don't set Content-Type for FormData
        if (options.body instanceof FormData) {
            delete config.headers['Content-Type'];
        }

        try {
            const response = await fetch(url, config);

            if (response.status === 401 && !path.includes('/auth/login')) {
                store.clearSession();
                window.location.hash = '#/login';
                throw new Error('Session expired');
            }

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            // Handle blob responses (exports)
            if (options.responseType === 'blob') {
                return response.blob();
            }

            return response.json();
        } catch (error) {
            console.error(`API Error [${options.method || 'GET'} ${path}]:`, error.message);
            throw error;
        }
    }

    // Auth
    login(email, password) {
        return this._fetch('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
    }

    getProfile() {
        return this._fetch('/auth/me');
    }

    // DSR
    uploadDSR(file, pumpId) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('pump_id', pumpId);
        return this._fetch('/dsr/upload', { method: 'POST', body: formData });
    }

    getDSRList(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/dsr?${qs}`);
    }

    getDSR(id) { return this._fetch(`/dsr/${id}`); }

    updateDSR(id, data) {
        return this._fetch(`/dsr/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    }

    approveDSR(id, notes = '') {
        return this._fetch(`/dsr/${id}/approve`, {
            method: 'POST', body: JSON.stringify({ notes }),
        });
    }

    rejectDSR(id, reason) {
        return this._fetch(`/dsr/${id}/reject`, {
            method: 'POST', body: JSON.stringify({ reason }),
        });
    }

    // Analytics
    getKPIs(pumpId) {
        const qs = pumpId ? `?pump_id=${pumpId}` : '';
        return this._fetch(`/analytics/kpi${qs}`);
    }

    getSalesTrend(days = 7, pumpId) {
        const params = new URLSearchParams({ days });
        if (pumpId) params.set('pump_id', pumpId);
        return this._fetch(`/analytics/sales-trend?${params}`);
    }

    getRevenue(startDate, endDate, pumpId) {
        const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
        if (pumpId) params.set('pump_id', pumpId);
        return this._fetch(`/analytics/revenue?${params}`);
    }

    getMonthlyRevenue(year, pumpId) {
        const params = new URLSearchParams({ year });
        if (pumpId) params.set('pump_id', pumpId);
        return this._fetch(`/analytics/monthly-revenue?${params}`);
    }

    getManagerPerformance(startDate, endDate, pumpId) {
        const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
        if (pumpId) params.set('pump_id', pumpId);
        return this._fetch(`/analytics/manager-performance?${params}`);
    }

    // Reports
    getReports(type, params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/reports/${type}?${qs}`);
    }

    exportReport(format, params) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/reports/export/${format}?${qs}`, { responseType: 'blob' });
    }

    // Search
    search(query, type, page = 1) {
        const params = new URLSearchParams({ q: query, page });
        if (type) params.set('type', type);
        return this._fetch(`/search?${params}`);
    }

    // Users
    getUsers(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this._fetch(`/users?${qs}`);
    }

    createUser(data) {
        return this._fetch('/users', { method: 'POST', body: JSON.stringify(data) });
    }

    updateUser(id, data) {
        return this._fetch(`/users/${id}`, { method: 'PUT', body: JSON.stringify(data) });
    }

    deleteUser(id) {
        return this._fetch(`/users/${id}`, { method: 'DELETE' });
    }

    // Notifications
    getNotifications(page = 1) {
        return this._fetch(`/notifications?page=${page}`);
    }

    getUnread() {
        return this._fetch('/notifications/unread');
    }

    markRead(id) {
        return this._fetch(`/notifications/${id}/read`, { method: 'POST' });
    }

    markAllRead() {
        return this._fetch('/notifications/read-all', { method: 'POST' });
    }
}

const api = new ApiClient();
export default api;
