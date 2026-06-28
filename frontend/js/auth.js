/**
 * DSR Petrol Platform — Auth Module
 */
import api from './api.js';
import store from './state.js';
import { showToast } from './components/toast.js';

export async function login(email, password) {
    try {
        const result = await api.login(email, password);
        store.set('token', result.access_token);
        store.set('user', result.user);
        store.saveSession();
        return result;
    } catch (error) {
        throw error;
    }
}

export function logout() {
    store.clearSession();
    window.location.hash = '#/login';
}

export function isAuthenticated() {
    return !!store.get('token') && !!store.get('user');
}

export function getUser() {
    return store.get('user');
}

export function getUserRole() {
    return store.get('user')?.role || 'staff';
}

export function hasRole(...roles) {
    const userRole = getUserRole();
    return roles.includes(userRole);
}

export function canAccess(requiredRoles) {
    if (!requiredRoles || requiredRoles.length === 0) return true;
    return hasRole(...requiredRoles);
}
