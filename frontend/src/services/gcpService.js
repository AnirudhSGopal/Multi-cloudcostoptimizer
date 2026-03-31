import api from './api'

const gcpService = {
  getCosts: (params) => api.get('/gcp/costs', { params }),
  getStorageUsage: () => api.get('/gcp/storage'),
  getSecurityFindings: () => api.get('/gcp/security'),
  getRecommendations: () => api.get('/gcp/recommendations'),
  getBuckets: () => api.get('/gcp/buckets'),
}

export default gcpService