/**
 * Admin API service — wraps all /api/v1/admin/* endpoints.
 */
import { apiClient } from './api'

const adminService = {
  // ── Users ───────────────────────────────────────────────
  getUsers: (params = {}) =>
    apiClient.get('/api/v1/admin/users', { params }),

  getUser: (id) =>
    apiClient.get(`/api/v1/admin/users/${id}`),

  updateUser: (id, data) =>
    apiClient.patch(`/api/v1/admin/users/${id}`, data),

  deleteUser: (id) =>
    apiClient.delete(`/api/v1/admin/users/${id}?confirm=true`),

  promoteUser: (id, role) =>
    apiClient.post(`/api/v1/admin/users/${id}/promote`, { role }),

  // ── Cloud Accounts ─────────────────────────────────────
  getCloudAccounts: (params = {}) =>
    apiClient.get('/api/v1/admin/cloud-accounts', { params }),

  // ── Scans ──────────────────────────────────────────────
  getScans: (params = {}) =>
    apiClient.get('/api/v1/admin/scans', { params }),

  // ── Stats ──────────────────────────────────────────────
  getStats: () =>
    apiClient.get('/api/v1/admin/stats'),

  // ── System Health ──────────────────────────────────────
  getSystemHealth: () =>
    apiClient.get('/api/v1/admin/system-health'),
}

export default adminService
