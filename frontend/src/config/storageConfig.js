/**
 * Central Single Source of Truth for Cloud Provider Storage Capacity.
 * Fixed storage distribution (40% / 30% / 30%):
 *   AWS:   4 GB (40%)
 *   GCP:   3 GB (30%)
 *   Azure: 3 GB (30%)
 *   Total: 10 GB
 *
 * Rules:
 * - Fixed & identical before and after optimization.
 * - No component hardcodes storage numbers.
 * - No thousands separators, no decimals (10 GB, not 10.0 GB).
 */

export const STORAGE_CONFIG = {
  AWS: {
    key: 'AWS',
    provider: 'aws',
    name: 'AWS',
    serviceName: 'AWS S3',
    sizeGb: 4,
    sharePct: 40,
    tabLabel: 'AWS (4 GB · 40%)',
    sizeLabel: '4 GB',
    shareLabel: '40%',
    badgeLabel: '4 GB · 40%',
  },
  GCP: {
    key: 'GCP',
    provider: 'gcp',
    name: 'GCP',
    serviceName: 'GCP Storage',
    sizeGb: 3,
    sharePct: 30,
    tabLabel: 'GCP (3 GB · 30%)',
    sizeLabel: '3 GB',
    shareLabel: '30%',
    badgeLabel: '3 GB · 30%',
  },
  Azure: {
    key: 'Azure',
    provider: 'azure',
    name: 'Azure',
    serviceName: 'Azure Blob',
    sizeGb: 3,
    sharePct: 30,
    tabLabel: 'Azure (3 GB · 30%)',
    sizeLabel: '3 GB',
    shareLabel: '30%',
    badgeLabel: '3 GB · 30%',
  },
  Total: {
    sizeGb: 10,
    sizeLabel: '10 GB',
    statusBadge: 'Storage: 10 GB (unchanged)',
    tabLabel: 'Multi-Cloud Stack (10 GB)',
  }
}

export const TOTAL_STORAGE_GB = STORAGE_CONFIG.Total.sizeGb
export const TOTAL_STORAGE_LABEL = STORAGE_CONFIG.Total.sizeLabel
export const TOTAL_STORAGE_STATUS = STORAGE_CONFIG.Total.statusBadge

export function getProviderStorage(provider) {
  const p = (provider || '').toUpperCase()
  if (p === 'AWS') return STORAGE_CONFIG.AWS
  if (p === 'GCP') return STORAGE_CONFIG.GCP
  if (p === 'AZURE') return STORAGE_CONFIG.Azure
  return STORAGE_CONFIG.Total
}

export function validateStorageInvariance(beforeGb, afterGb) {
  if (beforeGb !== afterGb) {
    throw new Error(`Storage size invariance violation: before=${beforeGb} GB, after=${afterGb} GB`)
  }
  return true
}
