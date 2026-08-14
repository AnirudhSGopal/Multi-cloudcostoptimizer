import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '../services/api'
import cloudService from '../services/cloudService'

export const ALERTS = [
  {
    id: 'azure-public-blob',
    type: 'critical',
    provider: 'Azure',
    title: 'Public blob access detected',
    impact: 'Unauthenticated public read access to prod-assets container',
    resource: 'storageaccount/prod-assets',
    owner: 'Platform Team',
    time: '2m ago',
    fixSteps: [
      'Go to Azure Portal → Storage Accounts',
      'Select prod-assets → Configuration',
      'Set "Allow Blob Public Access" to Disabled',
      'Save and verify with az cli: az storage container set-permission',
    ],
  },
  {
    id: 'gcp-uniform-access',
    type: 'warning',
    provider: 'GCP',
    title: 'Uniform bucket access disabled',
    impact: 'Inconsistent IAM enforcement — legacy ACLs active on 3 buckets',
    resource: 'gs://us-central1 (3 buckets)',
    owner: 'Data Engineering',
    time: '18m ago',
    fixSteps: [
      'Run: gsutil uniformbucketlevelaccess set on gs://BUCKET_NAME',
      'Repeat for all 3 affected buckets in us-central1',
      'Verify: gsutil uniformbucketlevelaccess get gs://BUCKET_NAME',
    ],
  },
  {
    id: 'aws-cloudtrail',
    type: 'info',
    provider: 'AWS',
    title: 'CloudTrail multi-region logging incomplete',
    impact: 'API activity in non-primary regions not captured',
    resource: 'CloudTrail / us-east-1',
    owner: 'Security Team',
    time: '1h ago',
    fixSteps: [
      'Open AWS Console → CloudTrail',
      'Edit trail → Enable "Apply to all regions"',
      'Confirm S3 bucket has capacity for increased log volume',
    ],
  },
]

function toAlertShape(a) {
  const type = a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info'
  
  let fixSteps = []
  if (type === 'critical') {
    fixSteps = [
      `Locate the affected resource or file: ${a.location ?? 'Unknown'}.`,
      'Identify and extract any hardcoded credentials, API keys, or JWT secrets.',
      'Configure the service to inject these values via environment variables.',
      'Rotate any exposed credentials immediately on the provider control panel.'
    ]
  } else if (type === 'warning') {
    fixSteps = [
      `Review access rules and permissions for: ${a.location ?? 'Unknown'}.`,
      'Enforce least-privilege configurations and restrict open access controls.',
      'Enable server-side validation and secure configurations.',
      'Run verification scripts to ensure that resources are not publicly queryable.'
    ]
  } else {
    fixSteps = [
      'Assess development guidelines and enforce secure header best practices.',
      'Implement missing security libraries or middleware.',
      'Set up continuous security testing in the CI/CD pipeline.'
    ]
  }

  return {
    id:       a.id,
    type,
    title:    a.message,
    impact:   a.message,
    resource: a.location ?? 'Unknown',
    owner:    'Security Team',
    time:     'just now',
    fixSteps,
  }
}

function toComplianceRow(r) {
  const status = r.status === 'pass' ? 'Pass' : 'Fail'
  const score  = r.status === 'pass' ? '>85%' : r.severity === 'high' ? '<70%' : '70–85%'
  return { framework: r.check, status, score, findings: r.detail }
}

const useCloudStore = create(
  persist(
    (set, get) => ({
      selectedProvider: 'all',
      dateRange: '30d',
      isLoading: false,
      securityScore: 74,
      alerts: ALERTS,
      dismissedAlerts: [],
      scanOverall: null,
      scanCompliance: null,
      scanTime: null,
      repoUrl: '',
      hasScanned: false,

      // In-memory background scan states
      scanning: false,
      progress: 0,
      scanError: '',

      // Multi-Cloud Account & Cost Optimization state
      accounts: [],
      costData: [],
      resources: [],
      recommendations: [],
      costLoading: false,
      accountsLoading: false,
      costError: '',

      setProvider:  (provider) => set({ selectedProvider: provider }),
      setDateRange: (range)    => set({ dateRange: range }),
      setLoading:   (val)      => set({ isLoading: val }),
      setRepoUrl:   (url)      => set({ repoUrl: url }),
      dismissAlert: (id)       => set((s) => ({ dismissedAlerts: [...s.dismissedAlerts, id] })),
      setError:     (err)      => set({ scanError: err }),

      // ── Cloud Accounts & Sync Actions ──────────────────────────────────
      fetchAccounts: async () => {
        set({ accountsLoading: true })
        try {
          const { data } = await cloudService.getAccounts()
          const accountsList = data.accounts || []
          set({ accounts: accountsList, accountsLoading: false })
          return accountsList
        } catch (e) {
          console.error("Failed to fetch cloud accounts:", e)
          set({ accountsLoading: false })
          return []
        }
      },

      testConnection: async (provider, credentials) => {
        try {
          const { data } = await cloudService.testConnection({ provider, credentials })
          return { success: true, message: data.message || "Credentials verified." }
        } catch (e) {
          const message = e.response?.data?.error || e.message || "Validation failed"
          return { success: false, error: message }
        }
      },

      addCloudAccount: async (provider, label, credentials) => {
        try {
          const { data } = await cloudService.createAccount({
            provider,
            account_label: label,
            credentials,
          })
          await get().fetchAccounts()
          await get().syncAllAccounts()
          return { success: true, message: data.message }
        } catch (e) {
          const message = e.response?.data?.error || e.message || "Failed to save account"
          return { success: false, error: message }
        }
      },

      deleteCloudAccount: async (accountId) => {
        try {
          await cloudService.deleteAccount(accountId)
          await get().fetchAccounts()
          await get().syncAllAccounts()
          return { success: true }
        } catch (e) {
          const message = e.response?.data?.error || e.message || "Failed to delete account"
          return { success: false, error: message }
        }
      },

      syncAllAccounts: async () => {
        const { accounts } = get()
        if (!accounts || accounts.length === 0) {
          set({ costData: [], resources: [], recommendations: [], costError: '' })
          return
        }

        set({ costLoading: true, costError: '' })

        let aggregatedCost = []
        let aggregatedResources = []
        let aggregatedRecs = []
        let errors = []

        for (const acc of accounts) {
          try {
            const { data } = await cloudService.syncAccount(acc.id)
            if (data.cost_data) aggregatedCost = [...aggregatedCost, ...data.cost_data]
            if (data.resources) aggregatedResources = [...aggregatedResources, ...data.resources]
            if (data.recommendations) aggregatedRecs = [...aggregatedRecs, ...data.recommendations]
            if (data.cost_error) errors.push(`${acc.provider.toUpperCase()}: ${data.cost_error}`)
          } catch (e) {
            const errStr = e.response?.data?.error || e.message
            errors.push(`${acc.provider.toUpperCase()}: ${errStr}`)
          }
        }

        set({
          costData: aggregatedCost,
          resources: aggregatedResources,
          recommendations: aggregatedRecs,
          costError: errors.join(" | "),
          costLoading: false,
        })
      },

      updateScanResults: (newAlerts, score, overall, compliance, scanTime, repoUrl) => set({
        alerts: newAlerts,
        securityScore: score,
        scanOverall: overall,
        scanCompliance: compliance,
        scanTime: scanTime,
        repoUrl: repoUrl,
        hasScanned: true,
        dismissedAlerts: []
      }),

      resetScan: () => set({
        alerts: ALERTS,
        securityScore: 74,
        scanOverall: null,
        scanCompliance: null,
        scanTime: null,
        repoUrl: '',
        hasScanned: false,
        dismissedAlerts: [],
        scanning: false,
        progress: 0,
        scanError: ''
      }),

      startBackgroundScan: async (url, filesWithContent) => {
        set({ scanning: true, progress: 20, scanError: '' })
        try {
          set({ progress: 50 })
          
          const { data } = await apiClient.post('/api/audit', {
            repoUrl: url || null,
            files: filesWithContent,
          }, { timeout: 300000 })

          set({ progress: 90 })

          const nextOverall = data.overall ?? null
          const nextScanAlerts = data.alerts ? data.alerts : []
          const nextCompliance = data.compliance ? data.compliance.map(toComplianceRow) : null
          const nextScanTime = new Date()

          set({
            alerts: nextScanAlerts.map(toAlertShape),
            securityScore: nextOverall?.score ?? 74,
            scanOverall: nextOverall,
            scanCompliance: nextCompliance,
            scanTime: nextScanTime.toISOString(),
            repoUrl: url,
            hasScanned: true,
            dismissedAlerts: [],
            scanning: false,
            progress: 0
          })
        } catch (e) {
          const detail = e?.response?.data?.detail || e.message || 'Audit failed'
          set({ scanError: detail, scanning: false, progress: 0 })
          console.error(e)
        }
      }
    }),
    {
      name: 'cloudopt-state-store',
      partialize: (state) => ({
        selectedProvider: state.selectedProvider,
        dateRange: state.dateRange,
        securityScore: state.securityScore,
        alerts: state.alerts,
        dismissedAlerts: state.dismissedAlerts,
        scanOverall: state.scanOverall,
        scanCompliance: state.scanCompliance,
        scanTime: state.scanTime,
        repoUrl: state.repoUrl,
        hasScanned: state.hasScanned,
        accounts: state.accounts,
        costData: state.costData,
        resources: state.resources,
        recommendations: state.recommendations,
      })
    }
  )
)

export default useCloudStore