/**
 * DSR Petrol — Users Page (Admin Only)
 */
import api from '../api.js';
import { showToast } from '../components/toast.js';

export async function renderUsers(container) {
    container.innerHTML = `
        <div class="page-header">
            <div>
                <h1 class="page-title">User Management</h1>
                <p class="page-subtitle">Manage staff, managers, and roles.</p>
            </div>
            <button class="btn btn-primary" onclick="alert('Add User modal coming soon')">+ Add User</button>
        </div>
        
        <div class="card">
            <div class="data-table-wrapper">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Created</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="users-tbody">
                        <tr><td colspan="6" class="text-center p-6"><div class="processing-spinner" style="margin:0 auto"></div></td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;

    try {
        const result = await api.getUsers();
        const tbody = document.getElementById('users-tbody');
        
        if (!result.data || result.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center p-6">No users found.</td></tr>';
            return;
        }

        tbody.innerHTML = result.data.map(u => `
            <tr>
                <td>
                    <div style="display:flex;align-items:center;gap:8px">
                        <div class="avatar avatar-sm">${u.full_name?.charAt(0) || '?'}</div>
                        <strong>${u.full_name}</strong>
                    </div>
                </td>
                <td>${u.email}</td>
                <td><span class="badge badge-neutral">${u.role.replace('_', ' ')}</span></td>
                <td><span class="badge badge-${u.is_active ? 'success' : 'danger'}">${u.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-ghost btn-sm" onclick="alert('Edit user ${u.id}')">Edit</button>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        document.getElementById('users-tbody').innerHTML = `<tr><td colspan="6" class="text-center p-6 text-danger">Error loading users: ${e.message}</td></tr>`;
    }
}
