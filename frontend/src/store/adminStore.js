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
  usersSearch: '',

  fetchUsers: async (params = {}) => {
    set({ usersLoading: true })
    try {
      const { search, page } = { search: get().usersSearch, page: get().usersPage, ...params }
      const { data } = await adminService.getUsers({ search, page, per_page: 20 })
      set({
        users: data.users,
        usersTotal: data.total,
        usersPage: data.page,
        usersPages: data.pages,
        usersLoading: false,
      })
    } catch (e) {
      console.error('Failed to fetch users:', e)
      set({ usersLoading: false })
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
  cloudAccountsProvider: '',
  cloudAccountsStatus: '',

  fetchCloudAccounts: async (params = {}) => {
    set({ cloudAccountsLoading: true })
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
      })
    } catch (e) {
      console.error('Failed to fetch cloud accounts:', e)
      set({ cloudAccountsLoading: false })
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
  scansStatus: '',

  fetchScans: async (params = {}) => {
    set({ scansLoading: true })
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
      })
    } catch (e) {
      console.error('Failed to fetch scans:', e)
      set({ scansLoading: false })
    }
  },

  setScansStatus: (s) => set({ scansStatus: s, scansPage: 1 }),

  // ── Stats ────────────────────────────────────────────────
  stats: null,
  statsLoading: false,

  fetchStats: async () => {
    set({ statsLoading: true })
    try {
      const { data } = await adminService.getStats()
      set({ stats: data, statsLoading: false })
    } catch (e) {
      console.error('Failed to fetch stats:', e)
      set({ statsLoading: false })
    }
  },

  // ── System Health ────────────────────────────────────────
  health: null,
  healthLoading: false,

  fetchHealth: async () => {
    set({ healthLoading: true })
    try {
      const { data } = await adminService.getSystemHealth()
      set({ health: data, healthLoading: false })
    } catch (e) {
      console.error('Failed to fetch health:', e)
      set({ healthLoading: false })
    }
  },
}))

export default useAdminStore
