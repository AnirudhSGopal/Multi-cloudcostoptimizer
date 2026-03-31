import { create } from 'zustand'

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

const useCloudStore = create((set) => ({
  selectedProvider: 'all',
  dateRange: '30d',
  isLoading: false,
  alerts: ALERTS,
  dismissedAlerts: [],

  setProvider:  (provider) => set({ selectedProvider: provider }),
  setDateRange: (range)    => set({ dateRange: range }),
  setLoading:   (val)      => set({ isLoading: val }),
  dismissAlert: (id)       => set((s) => ({ dismissedAlerts: [...s.dismissedAlerts, id] })),
}))

export default useCloudStore