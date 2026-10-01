/**
 * Zustand store for admin panel state.
 */
import { create } from 'zustand'
import adminService from '../services/adminService'

const useAdminStore = create((set, get) => ({
  // ── Users ────────────────────────────────────────────────
  users: [],
  usersTotal: 0,
  usersPage: 1,
  usersPages: 1,
  usersLoading: false,
  usersError: '',
  usersSearch: '',

  fetchUsers: async (params = {}) => {
    set({ usersLoading: true, usersError: '' })
    try {
      const { search, page } = { search: get().usersSearch, page: get().usersPage, ...params }
      const { data } = await adminService.getUsers({ search, page, per_page: 20 })
      set({
        users: data.users,
        usersTotal: data.total,
        usersPage: data.page,
        usersPages: data.pages,
        usersLoading: false,
        usersError: '',
      })
    } catch (e) {
      console.warn('Failed to fetch users')
      set({ usersLoading: false, usersError: e.response?.data?.error || 'Unable to load users.' })
    }
  },

  setUsersSearch: (search) => set({ usersSearch: search }),
  setUsersPage: (page) => set({ usersPage: page }),

  updateUser: async (id, data) => {
    try {
      await adminService.updateUser(id, data)
      await get().fetchUsers()
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.error || e.message }
    }
  },

  deleteUser: async (id) => {
    try {
      await adminService.deleteUser(id)
      await get().fetchUsers()
      return { success: true }
    } catch (e) {
      return { success: false, error: e.response?.data?.error || e.message }
    }
  },

  // ── Cloud Accounts ───────────────────────────────────────
  cloudAccounts: [],
  cloudAccountsTotal: 0,
  cloudAccountsPage: 1,
  cloudAccountsPages: 1,
  cloudAccountsLoading: false,
  cloudAccountsError: '',
  cloudAccountsProvider: '',
  cloudAccountsStatus: '',

  fetchCloudAccounts: async (params = {}) => {
    set({ cloudAccountsLoading: true, cloudAccountsError: '' })
    try {
      const { provider, status, page } = {
        provider: get().cloudAccountsProvider,
        status: get().cloudAccountsStatus,
        page: get().cloudAccountsPage,
        ...params,
      }
      const queryParams = { page, per_page: 20 }
      if (provider) queryParams.provider = provider
      if (status) queryParams.status = status
      const { data } = await adminService.getCloudAccounts(queryParams)
      set({
        cloudAccounts: data.cloud_accounts,
        cloudAccountsTotal: data.total,
        cloudAccountsPage: data.page,
        cloudAccountsPages: data.pages,
        cloudAccountsLoading: false,
        cloudAccountsError: '',
      })
    } catch (e) {
      console.warn('Failed to fetch cloud accounts')
      set({
        cloudAccountsLoading: false,
        cloudAccountsError: e.response?.data?.error || 'Unable to load cloud accounts.',
      })
    }
  },

  setCloudAccountsProvider: (p) => set({ cloudAccountsProvider: p, cloudAccountsPage: 1 }),
  setCloudAccountsStatus: (s) => set({ cloudAccountsStatus: s, cloudAccountsPage: 1 }),

  // ── Scans ────────────────────────────────────────────────
  scans: [],
  scansTotal: 0,
  scansPage: 1,
  scansPages: 1,
  scansLoading: false,
  scansError: '',
  scansStatus: '',

  fetchScans: async (params = {}) => {
    set({ scansLoading: true, scansError: '' })
    try {
      const { status, page } = {
        status: get().scansStatus,
        page: get().scansPage,
        ...params,
      }
      const queryParams = { page, per_page: 20 }
      if (status) queryParams.status = status
      const { data } = await adminService.getScans(queryParams)
      set({
        scans: data.scans,
        scansTotal: data.total,
        scansPage: data.page,
        scansPages: data.pages,
        scansLoading: false,
        scansError: '',
      })
    } catch (e) {
      console.warn('Failed to fetch scans')
      set({ scansLoading: false, scansError: e.response?.data?.error || 'Unable to load scans.' })
    }
  },

  setScansStatus: (s) => set({ scansStatus: s, scansPage: 1 }),

  // ── Stats ────────────────────────────────────────────────
  stats: null,
  statsLoading: false,
  statsError: '',

  fetchStats: async () => {
    set({ statsLoading: true, statsError: '' })
    try {
      const { data } = await adminService.getStats()
      set({ stats: data, statsLoading: false, statsError: '' })
    } catch (e) {
      console.warn('Failed to fetch platform statistics')
      set({ statsLoading: false, statsError: e.response?.data?.error || 'Unable to load platform statistics.' })
    }
  },

  // ── System Health ────────────────────────────────────────
  health: null,
  healthLoading: false,
  healthError: '',

  fetchHealth: async () => {
    set({ healthLoading: true, healthError: '' })
    try {
      const { data } = await adminService.getSystemHealth()
      set({ health: data, healthLoading: false, healthError: '' })
    } catch (e) {
      console.warn('Failed to fetch system health')
      set({ healthLoading: false, healthError: e.response?.data?.error || 'Unable to load system health.' })
    }
  },
}))

export default useAdminStore
